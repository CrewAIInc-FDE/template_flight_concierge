from pydantic import BaseModel

from .message import Message
from .trip_data import TripData


class FlightConciergeState(BaseModel):
    # inputs
    message: Message | None = None

    # processing
    trip_data: TripData | None = None
    messages: list[Message] = []
