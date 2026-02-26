from pydantic import BaseModel


class Dispatcher(BaseModel):
    url: str
    key: str
