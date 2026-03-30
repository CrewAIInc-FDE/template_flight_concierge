#!/usr/bin/env python
import os
from typing import Literal

from arize.otel import register
from crewai.flow import Flow, and_, human_feedback, listen, persist, start
from crewai.flow.human_feedback import HumanFeedbackResult
from openinference.instrumentation.crewai import CrewAIInstrumentor

from flight_concierge.agents.flight_concierge_agent import FlightConciergeAgent
from flight_concierge.events.services import DispatcherEventBusService
from flight_concierge.services import AirLabsService
from flight_concierge.types import FlightConciergeState, Message, Review

tracer_provider = register(
    space_id=os.getenv("ARIZE_SPACE_ID"),
    api_key=os.getenv("ARIZE_API_KEY"),
    project_name=os.getenv("ARIZE_PROJECT_NAME"),
)
CrewAIInstrumentor().instrument(tracer_provider=tracer_provider)


@persist()
class FlightConciergeFlow(Flow[FlightConciergeState]):
    @start()
    def load_initial_context(self):
        self._event_bus_service().append_user_message(self.state.message)
        return self.state.message.content

    @listen(load_initial_context)
    def collect_country_codes(self):
        self._air_labs_service().ensure_countries_cached()

    @listen(load_initial_context)
    def collect_city_codes(self):
        self._air_labs_service().ensure_cities_cached()

    @listen(load_initial_context)
    def collect_airport_codes(self):
        self._air_labs_service().ensure_airports_cached()

    @listen(and_(collect_country_codes, collect_city_codes, collect_airport_codes))
    def acknowledge_user_message(self):
        result = FlightConciergeAgent().acknowledge_message(self.state.messages)
        self._event_bus_service().append_assistant_message(result.assistant_response)
        return self.state.messages[-1].content

    @listen(acknowledge_user_message)
    def process_departure_details(self):
        result = FlightConciergeAgent().process_departure_information(
            self.state.messages
        )
        self.state.trip_data.legs[0].departure = result

    @listen(acknowledge_user_message)
    def process_arrival_details(self):
        result = FlightConciergeAgent().process_arrival_information(self.state.messages)
        self.state.trip_data.legs[0].arrival = result

    @listen(and_(process_departure_details, process_arrival_details))
    @human_feedback(
        message="Please review this trip planning details. Does it meet your needs?",
        emit=["needs_changes", "approved"],
        llm="gpt-5.4-mini",
    )
    def draft_trip_plan(
        self, human_feedback_result
    ) -> Literal["needs_changes", "approved"]:
        result = FlightConciergeAgent().confirm_trip_data_with_user(
            messages=self.state.messages,
            trip_data=self.state.trip_data,
        )
        self.state.trip_data = result.metadata
        self._event_bus_service().append_assistant_feedback_message(
            result.assistant_response
        )
        return result.assistant_response.content

    @listen("needs_changes")
    def acknowledge_trip_plan_feedback(self, feedback_result: HumanFeedbackResult):
        user_message = Message(role="user", content=feedback_result.feedback)
        self._event_bus_service().append_user_message(user_message)
        result = FlightConciergeAgent().acknowledge_trip_plan_feedback(
            messages=self.state.messages,
        )
        self.state.trip_data.reviews.append(
            Review(
                agent_output=str(feedback_result.output),
                human_feedback=feedback_result.feedback,
                outcome=feedback_result.outcome,
            )
        )
        self._event_bus_service().append_assistant_message(result.assistant_response)
        return self.state.messages[-1].content

    @listen(acknowledge_trip_plan_feedback)
    @human_feedback(
        message="Please review the latest trip planning details. Is it better now?",
        emit=["needs_changes", "approved"],
        llm="gpt-5.4-mini",
    )
    def act_on_trip_plan_feedback(self) -> Literal["needs_changes", "approved"]:
        result = FlightConciergeAgent().act_on_trip_plan_feedback(
            messages=self.state.messages,
            trip_data=self.state.trip_data,
        )
        self.state.trip_data = result.metadata
        self._event_bus_service().append_assistant_feedback_message(
            result.assistant_response
        )
        return result.assistant_response.content

    @listen("approved")
    def booking_route(self, feedback_result: HumanFeedbackResult):
        self._event_bus_service().append_user_message(
            Message(role="user", content=feedback_result.feedback)
        )

        result = FlightConciergeAgent().acknowledge_final_trip_planning_details(
            self.state.messages
        )
        self._event_bus_service().append_assistant_message(result.assistant_response)
        return self.state.messages[-1].content

    @listen(booking_route)
    @human_feedback(
        message="Please review the flight options. Do any of these work for you?",
        emit=["search_flights_again", "flights_selected"],
        llm="gpt-5.4-mini",
    )
    def look_for_best_flights(
        self, human_feedback_result
    ) -> Literal["search_flights_again", "flights_selected"]:
        result = FlightConciergeAgent().look_for_best_flights(
            trip_data=self.state.trip_data,
        )
        self._event_bus_service().append_assistant_feedback_message(
            result.assistant_response
        )
        return result.assistant_response.content

    @listen("search_flights_again")
    def acknowledge_flight_feedback(self, feedback_result: HumanFeedbackResult):
        user_message = Message(role="user", content=feedback_result.feedback)
        self._event_bus_service().append_user_message(user_message)
        result = FlightConciergeAgent().acknowledge_flight_feedback(
            messages=self.state.messages,
        )
        self.state.trip_data.reviews.append(
            Review(
                agent_output=str(feedback_result.output),
                human_feedback=feedback_result.feedback,
                outcome=feedback_result.outcome,
            )
        )
        self._event_bus_service().append_assistant_message(result.assistant_response)
        return self.state.messages[-1].content

    @listen(acknowledge_flight_feedback)
    @human_feedback(
        message="Please select which flight options you want to book or ask for other options.",
        emit=["search_flights_again", "flights_selected"],
        llm="gpt-5.4-mini",
    )
    def act_on_flight_feedback(
        self,
    ) -> Literal["search_flights_again", "flights_selected"]:
        result = FlightConciergeAgent().act_on_flight_feedback(
            messages=self.state.messages,
            trip_data=self.state.trip_data,
        )
        self._event_bus_service().append_assistant_feedback_message(
            result.assistant_response
        )
        return result.assistant_response.content

    @listen("flights_selected")
    def confirm_booking(self, feedback_result: HumanFeedbackResult):
        self._event_bus_service().append_user_message(
            Message(role="user", content=feedback_result.feedback)
        )

        result = FlightConciergeAgent().confirm_booking(self.state.messages)
        self._event_bus_service().append_assistant_message(
            result.assistant_response,
            keep_processing=False,
            end_of_conversation=True,
        )
        return self.state.messages[-1].content

    def _air_labs_service(self) -> AirLabsService:
        return AirLabsService()

    def _event_bus_service(self) -> DispatcherEventBusService:
        return DispatcherEventBusService(
            id=self.state.id,
            messages=self.state.messages,
        )


def kickoff():
    FlightConciergeFlow().kickoff(
        inputs={
            "message": {
                "role": "user",
                "content": "Gostaria de viajar de Recife para Campinas em 2 dias e retornar 3 dias depois",
            },
        }
    )


def plot():
    FlightConciergeFlow().plot()


if __name__ == "__main__":
    kickoff()
