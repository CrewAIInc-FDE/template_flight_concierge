from typing import Any

from crewai.events.base_events import BaseEvent


class UserEvent(BaseEvent):
    type: str = "user_event"

    result: Any | None = None
