from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Depends, Form
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.responses import RedirectResponse

from app.he_server import add_ciphertexts
from app.he import decrypt_number_demo
from app.db.database import engine, SessionLocal
from app.db.models import Patient, Measurement
from app.db.database import Base

app = FastAPI(title="Medical HE App")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


NAV = [
    {"href": "/", "label": "Dashboard"},
    {"href": "/patients", "label": "Pacjenci"},
    {"href": "/measurements", "label": "Pomiary"},
    {"href": "/he", "label": "Agregacje (HE)"},
    {"href": "/benchmark", "label": "Benchmark"},
]

def common_context(request: Request, active: str):
    return {
        "request": request,
        "nav": NAV,
        "active": active,
        "app_name": "Medical Data • Homomorphic Encryption",
    }

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    ctx = common_context(request, active="/")
    ctx.update({
        "stats": [
            {"label": "Pacjenci", "value": 12},
            {"label": "Pomiary (30 dni)", "value": 284},
            {"label": "Operacje HE", "value": 38},
        ],
        "events": [
            "Zapisano 5 pomiarów pacjenta #102 (ciphertext).",
            "Obliczono średnią glukozy (HE) dla pacjenta #102.",
            "Benchmark: HE vs plaintext (do uzupełnienia wynikami).",
        ]
    })
    return templates.TemplateResponse("dashboard.html", ctx)

@app.get("/patients", response_class=HTMLResponse)
def patients(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, active="/patients")
    ctx["patients"] = db.query(Patient).order_by(Patient.id.desc()).all()
    return templates.TemplateResponse("patients.html", ctx)

@app.post("/patients", response_class=HTMLResponse)
def patients_create(
    request: Request,
    name: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    p = Patient(name=name.strip(), note=(note.strip() or None))
    db.add(p)
    db.commit()
    return RedirectResponse(url="/patients", status_code=303)

@app.get("/measurements", response_class=HTMLResponse)
def measurements(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, active="/measurements")
    ctx["patients"] = db.query(Patient).order_by(Patient.name.asc()).all()
    ctx["measurements"] = (
        db.query(Measurement)
        .order_by(Measurement.taken_at.desc())
        .limit(200)
        .all()
    )
    return templates.TemplateResponse("measurements.html", ctx)

import base64
@app.post("/measurements", response_class=HTMLResponse)
def measurements_create(
    request: Request,
    patient_id: int = Form(...),
    kind: str = Form(...),
    value: str = Form(...),   # <-- było float, zmień na str
    taken_at: str = Form(""),
    db: Session = Depends(get_db),
):
    dt = None
    if taken_at.strip():
        dt = datetime.fromisoformat(taken_at)
        
    try:
     base64.b64decode(value.strip().encode("utf-8"), validate=True)
    except Exception:
    # możesz tu zwrócić stronę z komunikatem, na razie prosto:
        raise ValueError("Wartość nie jest poprawnym base64 ciphertext.")
    m = Measurement(
        patient_id=patient_id,
        kind=kind.strip(),
        value=value.strip(),  # <-- zapis ciphertext
        taken_at=dt or datetime.utcnow(),
    )
    db.add(m)
    db.commit()
    return RedirectResponse(url="/measurements", status_code=303)

@app.get("/he", response_class=HTMLResponse)
def he(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, active="/he")
    ctx["patients"] = db.query(Patient).order_by(Patient.name.asc()).all()
    ctx["result_title"] = None
    return templates.TemplateResponse("he.html", ctx)


@app.post("/he/sum", response_class=HTMLResponse)
def he_sum(
    request: Request,
    patient_id: int = Form(...),
    kind: str = Form(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Measurement)
        .filter(Measurement.patient_id == patient_id, Measurement.kind == kind)
        .order_by(Measurement.taken_at.desc())
        .all()
    )
    cts = [r.value for r in rows]
    print("CTS count:", len(cts))
    try:
        result_ct = add_ciphertexts(cts)
    except Exception as e:
        print("add_ciphertexts failed:", e)
        raise

    print("RESULT_CT len:", len(result_ct) if result_ct else "EMPTY")

    # optional demo decrypt (only for local demo)
    result_plain = None
    try:
        result_plain = decrypt_number_demo(result_ct)
    except Exception:
        # ignore decrypt errors in server; client should decrypt
        result_plain = None

    ctx = common_context(request, active="/he")
    ctx["patients"] = db.query(Patient).order_by(Patient.name.asc()).all()
    ctx["result_title"] = "Suma (HE)"
    ctx["result_plain"] = result_plain
    ctx["result_ct"] = result_ct
    ctx["count"] = len(cts)
    ctx["kind"] = kind
    ctx["patient_id"] = patient_id
    return templates.TemplateResponse("he.html", ctx)


@app.post("/he/avg", response_class=HTMLResponse)
def he_avg(
    request: Request,
    patient_id: int = Form(...),
    kind: str = Form(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Measurement)
        .filter(Measurement.patient_id == patient_id, Measurement.kind == kind)
        .order_by(Measurement.taken_at.desc())
        .all()
    )
    cts = [r.value for r in rows]
    print("CTS count (avg):", len(cts))
    result_ct = add_ciphertexts(cts) if cts else ""

    total = None
    try:
        total = decrypt_number_demo(result_ct) if result_ct else None
    except Exception:
        total = None
    avg = (total / len(cts)) if (cts and total is not None) else 0.0

    ctx = common_context(request, active="/he")
    ctx["patients"] = db.query(Patient).order_by(Patient.name.asc()).all()
    ctx["result_title"] = "Średnia (HE)"
    ctx["result_plain"] = avg
    ctx["result_ct"] = result_ct
    ctx["count"] = len(cts)
    ctx["kind"] = kind
    ctx["patient_id"] = patient_id
    return templates.TemplateResponse("he.html", ctx)