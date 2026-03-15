from pydantic import BaseModel, Field
from datetime import datetime

class PatientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    note: str | None = Field(default=None, max_length=300)

class MeasurementCreate(BaseModel):
    patient_id: int
    kind: str = Field(min_length=2, max_length=50)   # glucose, pressure_sys, heart_rate
    value: float
    taken_at: datetime | None = None
