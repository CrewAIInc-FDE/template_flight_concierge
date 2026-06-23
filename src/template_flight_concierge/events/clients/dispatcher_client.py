import requests

from template_flight_concierge.types import Dispatcher


class DispatcherClient:
    def __init__(self, dispatcher_data: Dispatcher):
        self.dispatcher_data = dispatcher_data
        self.request_headers = {
            "Authorization": f"Bearer {self.dispatcher_data.key}",
            "Content-Type": "application/json",
        }

    def dispatch(self, event_payload: dict):
        try:
            response = requests.post(
                self.dispatcher_data.url,
                headers=self.request_headers,
                json=event_payload,
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Error dispatching event to {self.dispatcher_data.url}: {e}")
            raise
