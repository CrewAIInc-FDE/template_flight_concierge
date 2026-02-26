from datetime import datetime

from crewai import Agent
from get_flight_airports_nearby import GetFlightAirportsNearby

from flight_concierge.tools import (
    GetFlightsFromGoogleFlights,
    QueryLocalAirportsDatabase,
    QueryLocalCitiesDatabase,
    QueryLocalCountriesDatabase,
)
from flight_concierge.types import (
    ArrivalData,
    DepartureData,
    Interaction,
    TripData,
)
from flight_concierge.types.message import Message


class FlightConciergeAgent:
    def __init__(self):
        self._agent = Agent(
            role="CrewAI Senior Travel Concierge",
            goal=f"""Find the most convenient flight routes and airport options for traveling FDEs,
            considering proximity, accessibility, and travel efficiency in a fluid conversational
            interface that respects the idiom being utilized by the user. You are also always
            aware of the current date - which is {datetime.now().strftime("%Y-%m-%d")}""".strip(),
            backstory="""You are a dedicated and professional travel concierge specializing in
            supporting CrewAI's Field Development Engineers (FDEs) who travel extensively around
            the globe. With years of experience in corporate travel logistics, you excel at
            identifying the most convenient airports, optimal routes, and practical travel options.
            You understand that FDEs value efficiency, proximity to city centers, and seamless
            connections. Your friendly yet professional approach ensures that every traveler feels
            supported and confident in their journey. You prioritize finding airports that minimize
            travel time and maximize convenience, always keeping the traveler's experience at the
            forefront of your recommendations.""".strip(),
            tools=[
                QueryLocalCountriesDatabase(),
                QueryLocalCitiesDatabase(),
                QueryLocalAirportsDatabase(),
                GetFlightAirportsNearby(),
                GetFlightsFromGoogleFlights(),
            ],
            llm="gpt-4.1",
        )

    def _latest_messages(self, messages: list[Message]):
        return "\n".join(
            [f"{msg.role.upper()}: {msg.content}" for msg in messages[-10:]]
        )

    def _latest_user_message(self, messages: list[Message]):
        return [msg for msg in messages if msg.role == "user"][-1]

    def acknowledge_message(self, messages: list[Message]):
        prompt = f"""
        As a Senior Travel Concierge, acknowledge the user's latest message in a warm, professional way.

        CONVERSATION HISTORY:
        {self._latest_messages(messages)}

        YOUR TASK:
        - Acknowledge what the user just said
        - Let them know you're processing their travel request
        - Keep it brief, friendly, and reassuring
        - Set expectations that you'll find the best flight options

        Return ONLY:
        - assistant_response: Your brief acknowledgment message (1-2 sentences max)
        """

        return self._agent.kickoff(prompt.strip(), response_format=Interaction).pydantic

    def process_departure_information(self, messages: list[Message]):
        prompt = f"""
        As a Senior Travel Concierge, focus on extracting and processing DEPARTURE information only.

        CONVERSATION HISTORY:
        {self._latest_messages(messages)}

        YOUR TASK: Extract departure details using TOP-DOWN approach:

        1. DEPARTURE COUNTRY
           - Identify departure country from conversation
           - Use Query Local Countries Database to verify and get country code

        2. DEPARTURE CITY
           - Identify departure city from conversation
           - Use Query Local Cities Database to get: city_code, lat, lng, country_code
           - Verify country code matches step 1

        3. DEPARTURE AIRPORTS
           - Use Query Local Airports Database with city_code (FREE, try first)
           - If no results, use Get Flight Airports Nearby with lat/lng (PAID, max once)
           - Distance: 30 km, ignore heliports and low popularity airports

        4. DEPARTURE DATE
           - Extract departure date from conversation (format: YYYY-MM-DD)

        Return only the departure information.
        """

        return self._agent.kickoff(
            prompt.strip(), response_format=DepartureData
        ).pydantic

    def process_arrival_information(self, messages: list[Message]):
        """Process arrival location details: country, city, and airports."""
        prompt = f"""
        As a Senior Travel Concierge, focus on extracting and processing ARRIVAL information only.

        CONVERSATION HISTORY:
        {self._latest_messages(messages)}

        YOUR TASK: Extract arrival details using TOP-DOWN approach:

        1. ARRIVAL COUNTRY
           - Identify arrival country from conversation
           - Use Query Local Countries Database to verify and get country code

        2. ARRIVAL CITY
           - Identify arrival city from conversation
           - Use Query Local Cities Database to get: city_code, lat, lng, country_code
           - Verify country code matches step 1

        3. ARRIVAL AIRPORTS
           - Use Query Local Airports Database with city_code (FREE, try first)
           - If no results, use Get Flight Airports Nearby with lat/lng (PAID, max once)
           - Distance: 30 km, ignore heliports and low popularity airports

        4. ARRIVAL DATE
           - Extract arrival date from conversation (format: YYYY-MM-DD)

        Return only the departure information.
        """

        return self._agent.kickoff(prompt.strip(), response_format=ArrivalData).pydantic

    def confirm_trip_data_with_user(self, messages: list[Message], trip_data: TripData):
        prompt = f"""
        As a Senior Travel Concierge, compile the trip details, present them to the user,
        and review them if necessary.

        CONVERSATION HISTORY:
        {self._latest_messages(messages)}

        DEPARTURE INFORMATION:
        {trip_data.legs[0].departure.model_dump_json()}

        ARRIVAL INFORMATION:
        {trip_data.legs[0].arrival.model_dump_json()}

        YOUR TASK:
        1. Review all departure and arrival information gathered
        2. Present a comprehensive summary with:
           - Complete departure details (country, city, airport options, date)
           - Complete arrival details (country, city, airport options, date)
        3. Highlight the most convenient airport options based on proximity and popularity
        4. Ask if the traveler needs any clarification or has preferences

        CRITICAL RULES:
        - Never suggest airports more than 30 km away from the cities the user is interested in
        - Ignore heliports and airports with low popularity scores

        RETURN:
        - assistant_response: A friendly, professional summary of the trip details.
        The intent with this message is to confirm the trip details before proceeding with the
        booking process. It is very important that in the message you highlight all details
        split in the following sections:
            * First leg: departure and arrival details (with both city/airports along with dates)
            * Second leg: same as the first one (if applicable in case it is a round trip)
        - metadata: The complete TripData information with all known information filled

        If any critical information is still missing, clearly ask for it.
        """

        return self._agent.kickoff(prompt.strip(), response_format=Interaction).pydantic

    def acknowledge_trip_plan_feedback(self, messages: list[Message]):
        prompt = f"""
        As a Senior Travel Concierge, acknowledge the trip plan feedback from the user.

        USER MESSAGE:
        {self._latest_user_message(messages).content}

        YOUR TASK:
        - Thank and acknowledge what the user just said
        - Let them know you will act on the feedback
        - Keep it brief, friendly, and reassuring
        - Respond on the same language as the user's message

        Return ONLY:
        - assistant_response: Your brief acknowledgment message (1-2 sentences max)
        """

        return self._agent.kickoff(prompt.strip(), response_format=Interaction).pydantic

    def act_on_trip_plan_feedback(self, messages: list[Message], trip_data: TripData):
        prompt = f"""
        As a Senior Travel Concierge, act on the trip plan feedback from the user.

        LATEST TRIP DATA:
        {trip_data.model_dump_json()}

        LATEST REVIEW:
        {trip_data.reviews[-1].model_dump_json()}

        YOUR TASK:
        1. Analyze the human feedback from the latest review
        2. Identify specific changes requested (dates, locations, preferences, etc.)
        3. Update the trip data accordingly based on the feedback
        4. If the feedback requires clarification, ask follow-up questions
        5. Provide a clear response explaining what changes were made

        CRITICAL RULES:
        - Address each point of feedback specifically
        - Maintain all previously confirmed details unless explicitly changed
        - If feedback is unclear, ask for clarification rather than guessing
        - Keep airport recommendations within 30km of target cities
        - Continue to ignore airports with low popularity scores
        - Preserve user preferences from previous interactions

        RETURN:
        - assistant_response: A friendly, professional summary of the trip details.
        The intent with this message is to confirm the trip details before proceeding with the
        booking process. It is very important that in the message you highlight all details
        split in the following sections:
            * First leg: departure and arrival details (with both city/airports along with dates)
            * Second leg: same as the first one (if applicable in case it is a round trip)
        - metadata: The complete TripData information with all known information filled
        """

        return self._agent.kickoff(prompt.strip(), response_format=Interaction).pydantic

    def acknowledge_final_trip_planning_details(self, messages: list[Message]):
        prompt = f"""
        As a Senior Travel Concierge, acknowledge the final trip planning details from the user.

        USER MESSAGE:
        {self._latest_user_message(messages).content}

        YOUR TASK:
        - Thank and acknowledge what the user just said
        - Let them know you will start looking for the best flights available
        - Keep it brief, friendly, and reassuring
        - Respond on the same language as the user's message

        RETURN:
        - assistant_response: Your brief acknowledgment message (1-2 sentences max)
        """

        return self._agent.kickoff(prompt.strip(), response_format=Interaction).pydantic

    def look_for_best_flights(self, trip_data: TripData):
        prompt = f"""
        As a Senior Travel Concierge, look for the best flights available for the trip.

        FINAL TRIP DATA:
        {trip_data.model_dump_json()}

        YOUR TASK:
        - Look for the best flights available
        - Use 'Find Flights' tool to do this
        - This tool can be used for round-trips and one-way trips
          * In case the legs differ in terms of departure and arrival airports,
          you should call the tool twice (once for each leg as an one-way trip each)
          * In case the legs are the same airports-wise, you should call the tool once (two-way trip)
        - Return the best flights available

        RETURN:
        - assistant_response: Your message with the best flights available for each leg of the trip
        written down in a friendly and professional way on the same language as the user's message.
        """

        return self._agent.kickoff(prompt.strip(), response_format=Interaction).pydantic
