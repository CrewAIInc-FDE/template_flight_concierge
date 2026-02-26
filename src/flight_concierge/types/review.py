from typing import Literal

from pydantic import BaseModel


class Review(BaseModel):
    agent_output: str
    human_feedback: str
    outcome: Literal["approved", "needs_changes"]

    def is_approved(self) -> bool:
        return self.outcome == "approved"
