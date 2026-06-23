from datetime import date

from pydantic import BaseModel, Field, field_validator

from .airport import Airport
from .city import City
from .country import Country


class ArrivalData(BaseModel):
    country: Country
    city: City
    airport: Airport
    date: str | None = Field(
        None, description="The date of the arrival in ISO format (YYYY-MM-DD)"
    )

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v):
        """Validate and ensure date is in ISO format string."""
        if v is None:
            return v
        if isinstance(v, date):
            return v.isoformat()
        if isinstance(v, str):
            # Validate the string is a valid date format
            try:
                date.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        raise ValueError(f"Date must be a string or date object, got {type(v)}")

    def is_valid(self) -> bool:
        return (
            self.country.is_valid()
            and self.city.is_valid()
            and self.airport.is_valid()
            and self.date is not None
        )
