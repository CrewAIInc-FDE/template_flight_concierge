from pydantic import BaseModel


class Airport(BaseModel):
    name: str | None = None
    iata_code: str | None = None
    icao_code: str | None = None
    city: str | None = None
    city_code: str | None = None
    lat: float | None = None
    lng: float | None = None
    country_code: str | None = None

    def is_valid(self) -> bool:
        return (
            self.lat is not None
            and self.lng is not None
            and (self.iata_code is not None or self.icao_code is not None)
        )
