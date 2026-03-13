import os

from flight_concierge.events.clients import DispatcherClient
from flight_concierge.events.types import UserEvent
from flight_concierge.types import Dispatcher, Message


class DispatcherEventBusService:
    def __init__(
        self,
        id: str,
        messages: list[Message] = [],
    ):
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
        self._dispatcher_client = DispatcherClient(self._dispatcher_data)

    def append_user_message(self, message: Message):
        self._messages.append(message)

    def append_assistant_feedback_message(self, message: Message):
        self._messages.append(message)

    def append_assistant_message(
        self,
        message: Message,
        keep_processing: bool = True,
        end_of_conversation: bool = False,
    ):
        self._messages.append(message)
        self._dispatcher_client.dispatch(
            UserEvent(
                result={
                    "message": message,
                    "keep_processing": keep_processing,
                    "end_of_conversation": end_of_conversation,
                },
                source_fingerprint=self._id,
                source_type="flight_concierge",
                fingerprint_metadata={"id": self._id},
            ).to_json()
        )
