from typing import List

from pydantic import BaseModel, Field

from .leg import Leg
from .review import Review


class TripData(BaseModel):
    legs: List[Leg] = Field(default_factory=lambda: [Leg()])
    reviews: List[Review] = []
