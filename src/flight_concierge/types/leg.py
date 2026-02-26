from pydantic import BaseModel, Field

from .arrival_data import ArrivalData
from .departure_data import DepartureData


class Leg(BaseModel):
    departure: DepartureData | None = None
    arrival: ArrivalData | None = None
    date: str | None = Field(
        None, description="Date of the flight leg in ISO format (YYYY-MM-DD)"
    )
