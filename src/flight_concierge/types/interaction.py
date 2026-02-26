from pydantic import BaseModel

from .arrival_data import ArrivalData
from .departure_data import DepartureData
from .message import Message
from .trip_data import TripData


class Interaction(BaseModel):
    assistant_response: Message
    metadata: DepartureData | ArrivalData | TripData | None = None
