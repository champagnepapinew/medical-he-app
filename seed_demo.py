import argparse
from datetime import datetime, timedelta
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.database import SessionLocal
from app.db.models import Measurement, Patient
from client.client import encrypt


DEMO_PATIENTS = [
    {
        "name": "Anna Kowalska",
        "note": "Pacjentka diabetologiczna - dane demonstracyjne",
        "measurements": {
            "glucose": [98, 103, 107, 111, 105, 109, 101],
            "pressure_sys": [118, 120, 117, 121, 119, 122, 118],
            "heart_rate": [71, 69, 74, 72, 70, 73, 71],
        },
    },
    {
        "name": "Jan Nowak",
        "note": "Pacjent kardiologiczny - dane demonstracyjne",
        "measurements": {
            "glucose": [92, 95, 90, 96, 94, 97, 93],
            "pressure_sys": [135, 138, 140, 137, 136, 139, 141],
            "heart_rate": [79, 82, 80, 81, 83, 78, 80],
        },
    },
    {
        "name": "Maria Zielinska",
        "note": "Pacjentka internistyczna - dane demonstracyjne",
        "measurements": {
            "glucose": [88, 86, 90, 91, 89, 87, 92],
            "pressure_sys": [124, 126, 122, 125, 123, 127, 124],
            "heart_rate": [67, 68, 66, 69, 65, 67, 68],
        },
    },
]


def seed_demo(reset: bool) -> None:
    db = SessionLocal()
    try:
        if reset:
            db.query(Measurement).delete()
            db.query(Patient).delete()
            db.commit()

        if db.query(Patient).count() > 0:
            print("Baza nie jest pusta. Użyj --reset, jeśli chcesz nadpisać dane demo.")
            return

        now = datetime.utcnow()

        for patient_data in DEMO_PATIENTS:
            patient = Patient(name=patient_data["name"], note=patient_data["note"])
            db.add(patient)
            db.flush()

            for kind, values in patient_data["measurements"].items():
                for index, value in enumerate(values):
                    taken_at = now - timedelta(days=(len(values) - index))
                    measurement = Measurement(
                        patient_id=patient.id,
                        kind=kind,
                        value=encrypt(float(value)),
                        taken_at=taken_at,
                    )
                    db.add(measurement)

        db.commit()
        print("Dane demo zostały zapisane do bazy.")
        print(f"Pacjenci: {db.query(Patient).count()}")
        print(f"Pomiary: {db.query(Measurement).count()}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo medical data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wyczyść istniejące rekordy i wstaw pełny zestaw danych demo.",
    )
    args = parser.parse_args()
    seed_demo(reset=args.reset)


if __name__ == "__main__":
    main()
