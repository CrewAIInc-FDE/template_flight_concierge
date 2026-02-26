import os
from typing import Literal, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from serpapi import GoogleSearch


class GetFlightsFromGoogleFlightsInput(BaseModel):
    """Input schema for FindFlights."""

    departure_id: str = Field(
        ...,
        description="The IATA airport code of the departure airport (e.g. REC, GRU, etc.) REQUIRED",
    )
    arrival_id: str = Field(
        ...,
        description="The IATA airport code of the arrival airport (e.g. REC, GRU, etc.) REQUIRED",
    )
    currency: str = Field(
        ...,
        description="The currency used to pay for the flights (e.g. USD, EUR, BRL, etc.) REQUIRED",
    )
    trip_type: Literal["one-way", "round-trip"] = Field(
        ...,
        description="The type of the trip (one-way or round-trip) REQUIRED",
    )
    outbound_date: str = Field(
        ...,
        description="The date of the outbound flight in ISO format (YYYY-MM-DD) REQUIRED",
    )
    return_date: str | None = Field(
        None,
        description="The date of the return flight in ISO format (YYYY-MM-DD). OPTIONAL (only needed for round-trips)",
    )


class GetFlightsFromGoogleFlights(BaseTool):
    name: str = "Find Flights"
    description: str = """Search for the best available flights between two airports using Google Flights.
    This tool finds flight options with pricing, schedules, and airline information for both one-way
    and round-trip journeys. It returns the most relevant flight results including departure/arrival
    times, duration, stops, and fare details to help users make informed travel decisions."""
    args_schema: Type[BaseModel] = GetFlightsFromGoogleFlightsInput

    def _run(
        self,
        departure_id: str,
        arrival_id: str,
        currency: str,
        trip_type: str,
        outbound_date: str,
        return_date: str | None = None,
    ) -> dict:
        params = {
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "currency": currency,
            "outbound_date": outbound_date,
            "type": "1" if trip_type == "round-trip" else "2",
            "api_key": os.getenv("SERPAPI_API_KEY"),
        }
        if trip_type == "round-trip" and return_date:
            params["return_date"] = return_date

        results = GoogleSearch(params).get_dict()

        if "best_flights" in results and results["best_flights"]:
            return results["best_flights"]
        else:
            return results
