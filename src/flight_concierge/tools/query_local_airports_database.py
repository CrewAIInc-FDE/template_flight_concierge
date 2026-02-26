import json
from pathlib import Path
from typing import Literal, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class QueryLocalAirportsDatabaseInput(BaseModel):
    """Input schema for QueryLocalAirportsDatabase."""

    search_query: str = Field(
        ...,
        description="Airport name, city code, IATA code, or ICAO code to search for",
    )
    filter_by: Literal["iata_code", "icao_code", "name", "city_code", "auto"] = Field(
        default="auto",
        description="Filter type: 'iata_code' for IATA code match, 'icao_code' for ICAO code match, 'name' for airport name match, 'city_code' for city code match, 'auto' to search all fields with priority on codes",
    )


class QueryLocalAirportsDatabase(BaseTool):
    name: str = "Query Local Airports Database"
    description: str = (
        "Query the local airports database for airport information. "
        "Can filter by IATA code, ICAO code, airport name, or city code. "
        "Prioritizes exact code matches over name matches when using 'auto' mode. "
        "Returns a list of airport dictionaries with all fields."
    )
    args_schema: Type[BaseModel] = QueryLocalAirportsDatabaseInput

    def _load_airports_data(self):
        """Load airports data from JSON file."""
        # Get project root (assuming tool is in src/flight_concierge/tools/)
        project_root = Path(__file__).parent.parent.parent.parent
        airports_file = project_root / "db" / "airports.json"

        if not airports_file.exists():
            raise FileNotFoundError(
                f"Airports database not found at {airports_file}. Please run the service to cache data first."
            )

        with open(airports_file, "r") as f:
            return json.load(f)

    def _run(
        self,
        search_query: str,
        filter_by: Literal[
            "iata_code", "icao_code", "name", "city_code", "auto"
        ] = "auto",
    ) -> list[dict]:
        query_lower = search_query.lower()
        airports = self._load_airports_data()

        # Priority 1: Exact IATA code match (always check first)
        if filter_by in ["iata_code", "auto"]:
            iata_matches = [
                airport
                for airport in airports
                if airport.get("iata_code")
                and query_lower == airport["iata_code"].lower()
            ]
            if iata_matches:
                return iata_matches

        # Priority 2: Exact ICAO code match
        if filter_by in ["icao_code", "auto"]:
            icao_matches = [
                airport
                for airport in airports
                if airport.get("icao_code")
                and query_lower == airport["icao_code"].lower()
            ]
            if icao_matches:
                return icao_matches

        # Priority 3: Exact city code match
        if filter_by in ["city_code", "auto"]:
            city_code_matches = [
                airport
                for airport in airports
                if airport.get("city_code")
                and query_lower == airport["city_code"].lower()
            ]
            if city_code_matches:
                return city_code_matches

        # Priority 4: Name matches (partial allowed)
        if filter_by in ["name", "auto"]:
            name_matches = [
                airport
                for airport in airports
                if airport.get("name") and query_lower in airport["name"].lower()
            ]
            if name_matches:
                return name_matches

        return []
