from crewai.events import BaseEventListener

from flight_concierge.events.clients import DispatcherClient
from flight_concierge.events.types import UserEvent
from flight_concierge.types import Dispatcher


class DispatcherEventListener(BaseEventListener):
    def __init__(self, dispatcher_data: Dispatcher):
        super().__init__()
        self.dispatcher_client = DispatcherClient(dispatcher_data)

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(UserEvent)
        def on_user_event_triggered(source, event):
            payload = event.to_json()
            self.dispatcher_client.dispatch(payload)
