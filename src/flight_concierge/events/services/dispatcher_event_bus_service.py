import os

from crewai.events.event_bus import crewai_event_bus

from flight_concierge.events.listeners import DispatcherEventListener
from flight_concierge.events.types import UserEvent
from flight_concierge.types import Dispatcher, Message

_listener_initialized = False


def _ensure_listener_initialized(dispatcher_data: Dispatcher):
    global _listener_initialized
    if not _listener_initialized:
        DispatcherEventListener(dispatcher_data)
        _listener_initialized = True


class DispatcherEventBusService:
    def __init__(
        self,
        id: str,
        messages: list[Message] = [],
    ):
        self._event_bus = crewai_event_bus
        self._id = id
        self._messages = messages

        dispatcher_url = os.getenv("DISPATCHER_URL")
        dispatcher_key = os.getenv("DISPATCHER_KEY")

        missing_vars = []
        if dispatcher_url is None:
            missing_vars.append("DISPATCHER_URL")
        if dispatcher_key is None:
            missing_vars.append("DISPATCHER_KEY")

        if missing_vars:
            raise ValueError(
                f"Required environment variables are missing: {', '.join(missing_vars)}"
            )
        self._dispatcher_data = Dispatcher(url=dispatcher_url, key=dispatcher_key)

        _ensure_listener_initialized(self._dispatcher_data)

    def append_message(
        self, message: Message, keep_processing: bool, end_of_conversation: bool = False
    ):
        self._messages.append(message)
        self._event_bus.emit(
            self,
            UserEvent(
                result={
                    "message": message,
                    "keep_processing": keep_processing,
                    "end_of_conversation": end_of_conversation,
                },
                source_fingerprint=self._id,
                source_type="flight_concierge",
                fingerprint_metadata={"id": self._id},
            ),
        )
