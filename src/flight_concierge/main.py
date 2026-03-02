#!/usr/bin/env python
from typing import Literal

from crewai.flow import Flow, and_, human_feedback, listen, persist, start
from crewai.flow.human_feedback import HumanFeedbackResult

from flight_concierge.agents.flight_concierge_agent import FlightConciergeAgent
from flight_concierge.events.services import DispatcherEventBusService
from flight_concierge.services import AirLabsService
from flight_concierge.types import FlightConciergeState, Message, Review


@persist()
class FlightConciergeFlow(Flow[FlightConciergeState]):
    def load_services(self):
        self.air_labs_service = AirLabsService()
        self.dispatcher_event_bus_service = DispatcherEventBusService(
            id=self.state.id, messages=self.state.messages
        )

    @start()
    def load_initial_context(self):
        self.load_services()
        self.dispatcher_event_bus_service.append_message(
            self.state.message, keep_processing=True
        )
        return self.state.message.content

    @listen(load_initial_context)
    def collect_country_codes(self):
        self.air_labs_service.ensure_countries_cached()

    @listen(load_initial_context)
    def collect_city_codes(self):
        self.air_labs_service.ensure_cities_cached()

    @listen(load_initial_context)
    def collect_airport_codes(self):
        self.air_labs_service.ensure_airports_cached()

    @listen(and_(collect_country_codes, collect_city_codes, collect_airport_codes))
    def acknowledge_user_message(self):
        result = FlightConciergeAgent().acknowledge_message(self.state.messages)
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=True
        )
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
        llm="gpt-4.1",
    )
    def draft_trip_plan(
        self, human_feedback_result
    ) -> Literal["needs_changes", "approved"]:
        result = FlightConciergeAgent().confirm_trip_data_with_user(
            messages=self.state.messages,
            trip_data=self.state.trip_data,
        )
        self.state.trip_data = result.metadata
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=False
        )
        self.state.interactions.append(result)
        return result.assistant_response.content

    @listen("needs_changes")
    def acknowledge_trip_plan_feedback(self, feedback_result: HumanFeedbackResult):
        self.load_services()
        user_message = Message(role="user", content=feedback_result.feedback)
        self.dispatcher_event_bus_service.append_message(
            user_message, keep_processing=True
        )
        self.state.trip_data.reviews.append(
            Review(
                agent_output=str(feedback_result.output),
                human_feedback=feedback_result.feedback,
                outcome=feedback_result.outcome,
            )
        )
        result = FlightConciergeAgent().acknowledge_trip_plan_feedback(
            messages=self.state.messages,
        )
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=True
        )
        return self.state.messages[-1].content

    @listen(acknowledge_trip_plan_feedback)
    @human_feedback(
        message="Please review the latest trip planning details. Is it better now?",
        emit=["needs_changes", "approved"],
        llm="gpt-4.1",
    )
    def act_on_trip_plan_feedback(self) -> Literal["needs_changes", "approved"]:
        result = FlightConciergeAgent().act_on_trip_plan_feedback(
            messages=self.state.messages,
            trip_data=self.state.trip_data,
        )
        self.state.trip_data = result.metadata
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=False
        )
        self.state.interactions.append(result)
        return result.assistant_response.content

    @listen("approved")
    def booking_route(self, feedback_result: HumanFeedbackResult):
        self.load_services()
        self.dispatcher_event_bus_service.append_message(
            Message(role="user", content=feedback_result.feedback),
            keep_processing=True,
        )

        result = FlightConciergeAgent().acknowledge_final_trip_planning_details(
            self.state.messages
        )
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=True
        )
        self.state.interactions.append(result)
        return self.state.messages[-1].content

    @listen(booking_route)
    @human_feedback(
        message="Please review the flight options. Do any of these work for you?",
        emit=["flight_needs_changes", "flight_approved"],
        llm="gpt-4.1",
    )
    def look_for_best_flights(
        self, human_feedback_result
    ) -> Literal["flight_needs_changes", "flight_approved"]:
        result = FlightConciergeAgent().look_for_best_flights(
            trip_data=self.state.trip_data,
        )
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=False
        )
        self.state.interactions.append(result)
        return result.assistant_response.content

    @listen("flight_needs_changes")
    def acknowledge_flight_feedback(self, feedback_result: HumanFeedbackResult):
        self.load_services()
        user_message = Message(role="user", content=feedback_result.feedback)
        self.dispatcher_event_bus_service.append_message(
            user_message, keep_processing=True
        )
        self.state.trip_data.reviews.append(
            Review(
                agent_output=str(feedback_result.output),
                human_feedback=feedback_result.feedback,
                outcome=feedback_result.outcome,
            )
        )
        result = FlightConciergeAgent().acknowledge_flight_feedback(
            messages=self.state.messages,
        )
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=True
        )
        return self.state.messages[-1].content

    @listen(acknowledge_flight_feedback)
    @human_feedback(
        message="Please review the updated flight options. Do these work better?",
        emit=["flight_needs_changes", "flight_approved"],
        llm="gpt-4.1",
    )
    def act_on_flight_feedback(
        self,
    ) -> Literal["flight_needs_changes", "flight_approved"]:
        result = FlightConciergeAgent().act_on_flight_feedback(
            messages=self.state.messages,
            trip_data=self.state.trip_data,
        )
        self.dispatcher_event_bus_service.append_message(
            result.assistant_response, keep_processing=False
        )
        self.state.interactions.append(result)
        return result.assistant_response.content

    @listen("flight_approved")
    def confirm_booking(self, feedback_result: HumanFeedbackResult):
        self.load_services()
        self.dispatcher_event_bus_service.append_message(
            Message(role="user", content=feedback_result.feedback),
            keep_processing=False,
            end_of_conversation=True,
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
