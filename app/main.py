import csv
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.he_server import add_ciphertexts
from app.he import decrypt_number_demo, encrypt_number_demo
from app.db.database import engine, SessionLocal
from app.db.models import Patient, Measurement
from app.db.database import Base
from project_paths import PUBLIC_CTX_PATH, resolve_secret_context_path, using_legacy_secret_path

app = FastAPI(title="Medical HE App")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)

MEASUREMENT_KINDS = {
    "glucose": "Glukoza",
    "pressure_sys": "Ciśnienie skurczowe",
    "heart_rate": "Tętno",
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def cipher_preview(value: str, head: int = 24, tail: int = 16) -> str:
    if len(value) <= head + tail + 3:
        return value
    return f"{value[:head]}...{value[-tail:]}"


def kind_label(kind: str) -> str:
    return MEASUREMENT_KINDS.get(kind, kind)


templates.env.filters["cipher_preview"] = cipher_preview
templates.env.filters["kind_label"] = kind_label


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
        "error": None,
        "success": None,
    }


def key_status() -> dict[str, str | bool]:
    public_exists = PUBLIC_CTX_PATH.exists()
    secret_path = resolve_secret_context_path()
    secret_exists = secret_path.exists()

    return {
        "public_exists": public_exists,
        "secret_exists": secret_exists,
        "secret_path": str(secret_path),
        "legacy_secret": using_legacy_secret_path(),
    }


def load_patients(db: Session) -> list[Patient]:
    return db.query(Patient).order_by(Patient.name.asc()).all()


def load_measurements(db: Session) -> list[Measurement]:
    return (
        db.query(Measurement)
        .options(joinedload(Measurement.patient))
        .order_by(Measurement.taken_at.desc())
        .limit(200)
        .all()
    )


def build_dashboard_stats(db: Session) -> list[dict[str, int]]:
    patient_count = db.query(Patient).count()
    measurement_count = db.query(Measurement).count()
    he_ops_count = 0

    summary_path = Path("benchmark_summary.csv")
    if summary_path.exists():
        with summary_path.open(encoding="utf-8", newline="") as f:
            he_ops_count = sum(1 for _ in csv.DictReader(f))

    return [
        {"label": "Pacjenci", "value": patient_count},
        {"label": "Pomiary", "value": measurement_count},
        {"label": "Serie benchmarku", "value": he_ops_count},
    ]


def build_dashboard_events(db: Session) -> list[str]:
    events: list[str] = []

    latest_measurements = (
        db.query(Measurement)
        .order_by(Measurement.taken_at.desc())
        .limit(3)
        .all()
    )
    for measurement in latest_measurements:
        events.append(
            f"Dodano pomiar typu {measurement.kind} dla pacjenta #{measurement.patient_id}."
        )

    if Path("benchmark_summary.csv").exists():
        events.append("Dostępne są wyniki benchmarku HE vs plaintext.")

    if not events:
        events.append("Brak danych startowych. Dodaj pacjentów i pomiary, aby rozpocząć demo.")

    return events


def dashboard_quickstart() -> list[str]:
    return [
        "python client/client.py keygen",
        "python seed_demo.py --reset",
        "python run_benchmark_reps.py",
        "uvicorn app.main:app --reload",
    ]

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, active="/")
    ctx.update(
        {
            "stats": build_dashboard_stats(db),
            "events": build_dashboard_events(db),
            "key_status": key_status(),
            "quickstart": dashboard_quickstart(),
        }
    )
    return templates.TemplateResponse("dashboard.html", ctx)

@app.get("/patients", response_class=HTMLResponse)
def patients(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, active="/patients")
    ctx["patients"] = db.query(Patient).order_by(Patient.id.desc()).all()
    if request.query_params.get("created") == "1":
        ctx["success"] = "Pacjent został dodany."
    return templates.TemplateResponse("patients.html", ctx)

@app.post("/patients", response_class=HTMLResponse)
def patients_create(
    request: Request,
    name: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    ctx = common_context(request, active="/patients")
    ctx["patients"] = db.query(Patient).order_by(Patient.id.desc()).all()

    clean_name = name.strip()
    if len(clean_name) < 2:
        ctx["error"] = "Imię i nazwisko musi mieć co najmniej 2 znaki."
        return templates.TemplateResponse("patients.html", ctx, status_code=400)

    p = Patient(name=clean_name, note=(note.strip() or None))
    db.add(p)
    db.commit()
    return RedirectResponse(url="/patients?created=1", status_code=303)

@app.get("/measurements", response_class=HTMLResponse)
def measurements(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, active="/measurements")
    ctx["patients"] = load_patients(db)
    ctx["measurements"] = load_measurements(db)
    ctx["measurement_kinds"] = MEASUREMENT_KINDS
    ctx["key_status"] = key_status()
    if request.query_params.get("created") == "1":
        ctx["success"] = "Pomiar został zapisany."
    return templates.TemplateResponse("measurements.html", ctx)

@app.post("/measurements", response_class=HTMLResponse)
def measurements_create(
    request: Request,
    patient_id: int = Form(...),
    kind: str = Form(...),
    value: str = Form(...),   # <-- było float, zmień na str
    taken_at: str = Form(""),
    db: Session = Depends(get_db),
):
    ctx = common_context(request, active="/measurements")
    ctx["patients"] = load_patients(db)
    ctx["measurements"] = load_measurements(db)
    ctx["measurement_kinds"] = MEASUREMENT_KINDS
    ctx["key_status"] = key_status()

    if db.get(Patient, patient_id) is None:
        ctx["error"] = "Wybrany pacjent nie istnieje."
        return templates.TemplateResponse("measurements.html", ctx, status_code=400)

    if kind not in MEASUREMENT_KINDS:
        ctx["error"] = "Wybrano nieobsługiwany typ pomiaru."
        return templates.TemplateResponse("measurements.html", ctx, status_code=400)

    dt = None
    if taken_at.strip():
        try:
            dt = datetime.fromisoformat(taken_at)
        except ValueError:
            ctx["error"] = "Nieprawidłowy format daty pomiaru."
            return templates.TemplateResponse("measurements.html", ctx, status_code=400)

    numeric_value_raw = value.strip().replace(",", ".")
    try:
        numeric_value = float(numeric_value_raw)
    except ValueError:
        ctx["error"] = "Wartość pomiaru musi być poprawną liczbą, np. 98 lub 98.5."
        return templates.TemplateResponse("measurements.html", ctx, status_code=400)

    try:
        encrypted_value = encrypt_number_demo(numeric_value)
    except Exception as e:
        ctx["error"] = f"Nie udało się zaszyfrować pomiaru: {e}"
        return templates.TemplateResponse("measurements.html", ctx, status_code=500)

    m = Measurement(
        patient_id=patient_id,
        kind=kind.strip(),
        value=encrypted_value,
        taken_at=dt or datetime.utcnow(),
    )
    db.add(m)
    db.commit()
    return RedirectResponse(url="/measurements?created=1", status_code=303)

@app.get("/he", response_class=HTMLResponse)
def he(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, active="/he")
    ctx["patients"] = load_patients(db)
    ctx["result_title"] = None
    ctx["key_status"] = key_status()
    ctx["measurement_kinds"] = MEASUREMENT_KINDS
    return templates.TemplateResponse("he.html", ctx)


@app.get("/benchmark", response_class=HTMLResponse)
def benchmark(request: Request):
    ctx = common_context(request, active="/benchmark")
    summary_path = Path("benchmark_summary.csv")
    bench: list[dict[str, str]] = []

    if summary_path.exists():
        with summary_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                n = int(row["n"])
                plain_ms = float(row["t_plain_mean_ms"])
                enc_ms = float(row["t_enc_mean_ms"])
                he_ms = float(row["t_he_mean_ms"])
                dec_ms = float(row["t_dec_mean_ms"])
                error = float(row["error_mean"])
                ratio = (he_ms / plain_ms) if plain_ms else 0.0
                bench.append(
                    {
                        "n": str(n),
                        "plaintext_ms": f"{plain_ms:.4f}",
                        "enc_ms": f"{enc_ms:.2f}",
                        "he_ms": f"{he_ms:.2f}",
                        "dec_ms": f"{dec_ms:.2f}",
                        "error": f"{error:.3e}",
                        "ratio": f"{ratio:.0f}",
                    }
                )

    ctx["bench"] = bench
    ctx["benchmark_command"] = "python run_benchmark_reps.py"
    if not bench:
        ctx["error"] = "Brak wyników benchmarku. Uruchom najpierw skrypt benchmarku."

    return templates.TemplateResponse("benchmark.html", ctx)


@app.post("/he/sum", response_class=HTMLResponse)
def he_sum(
    request: Request,
    patient_id: int = Form(...),
    kind: str = Form(...),
    db: Session = Depends(get_db),
):
    ctx = common_context(request, active="/he")
    ctx["patients"] = load_patients(db)
    ctx["key_status"] = key_status()
    ctx["measurement_kinds"] = MEASUREMENT_KINDS

    rows = (
        db.query(Measurement)
        .filter(Measurement.patient_id == patient_id, Measurement.kind == kind)
        .order_by(Measurement.taken_at.desc())
        .all()
    )
    cts = [r.value for r in rows]
    if not cts:
        ctx["error"] = "Brak pomiarów dla wybranego pacjenta i typu danych."
        ctx["result_title"] = None
        return templates.TemplateResponse("he.html", ctx, status_code=400)

    try:
        result_ct = add_ciphertexts(cts)
    except Exception as e:
        ctx["error"] = f"Nie udało się wykonać agregacji HE: {e}"
        ctx["result_title"] = None
        return templates.TemplateResponse("he.html", ctx, status_code=500)

    # optional demo decrypt (only for local demo)
    result_plain = None
    try:
        result_plain = decrypt_number_demo(result_ct)
    except Exception:
        # ignore decrypt errors in server; client should decrypt
        result_plain = None

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
    ctx = common_context(request, active="/he")
    ctx["patients"] = load_patients(db)
    ctx["key_status"] = key_status()
    ctx["measurement_kinds"] = MEASUREMENT_KINDS

    rows = (
        db.query(Measurement)
        .filter(Measurement.patient_id == patient_id, Measurement.kind == kind)
        .order_by(Measurement.taken_at.desc())
        .all()
    )
    cts = [r.value for r in rows]
    if not cts:
        ctx["error"] = "Brak pomiarów dla wybranego pacjenta i typu danych."
        ctx["result_title"] = None
        return templates.TemplateResponse("he.html", ctx, status_code=400)

    try:
        result_ct = add_ciphertexts(cts)
    except Exception as e:
        ctx["error"] = f"Nie udało się wykonać agregacji HE: {e}"
        ctx["result_title"] = None
        return templates.TemplateResponse("he.html", ctx, status_code=500)

    total = None
    try:
        total = decrypt_number_demo(result_ct)
    except Exception:
        total = None
    avg = (total / len(cts)) if total is not None else None

    ctx["result_title"] = "Średnia (HE)"
    ctx["result_plain"] = avg
    ctx["result_ct"] = result_ct
    ctx["count"] = len(cts)
    ctx["kind"] = kind
    ctx["patient_id"] = patient_id
    return templates.TemplateResponse("he.html", ctx)
