from pydantic import BaseModel


class Country(BaseModel):
    name: str | None = None
    code: str | None = None

    def is_valid(self) -> bool:
        return self.code is not None
