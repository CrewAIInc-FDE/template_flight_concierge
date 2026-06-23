from pydantic import BaseModel


class City(BaseModel):
    name: str | None = None
    city_code: str | None = None
    lat: float | None = None
    lng: float | None = None
    country_code: str | None = None

    def is_valid(self) -> bool:
        return self.lat is not None and self.lng is not None
