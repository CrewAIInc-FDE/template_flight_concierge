from datetime import datetime

from pydantic import BaseModel, Field

from .city import City


class UserRequestData(BaseModel):
    departure_city: City | None = Field(
        None, description="The city where the flight is departing from"
    )
    arrival_city: City | None = Field(
        None, description="The city where the flight is arriving to"
    )
    departure_date: datetime | None = Field(
        None, description="The date and time of the flight departure"
    )
    arrival_date: datetime | None = Field(
        None, description="The date and time of the flight arrival"
    )
