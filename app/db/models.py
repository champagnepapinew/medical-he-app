from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .database import Base

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    measurements: Mapped[list["Measurement"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan"
    )

class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)

    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # np. "glucose"
    # Pomiar jest przechowywany jako ciphertext (base64), nie plaintext.
    value: Mapped[str] = mapped_column(Text, nullable=False)

    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    patient: Mapped["Patient"] = relationship(back_populates="measurements")
