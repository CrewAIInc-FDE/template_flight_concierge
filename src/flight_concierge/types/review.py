from typing import Literal

from pydantic import BaseModel


class Review(BaseModel):
    agent_output: str
    human_feedback: str
    outcome: Literal[
        "approved", "needs_changes", "flight_approved", "flight_needs_changes"
    ]
