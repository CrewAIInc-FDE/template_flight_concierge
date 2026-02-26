from pydantic import BaseModel

from .interaction import Interaction
from .message import Message
from .trip_data import TripData


class FlightConciergeState(BaseModel):
    # inputs
    message: Message | None = None

    # processing
    trip_data: TripData = TripData()
    messages: list[Message] = []
    interactions: list[Interaction] = []
