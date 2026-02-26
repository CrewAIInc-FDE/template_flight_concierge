import json
from pathlib import Path
from typing import Literal, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class QueryLocalCitiesDatabaseInput(BaseModel):
    """Input schema for QueryLocalCitiesDatabase."""

    search_query: str = Field(..., description="City name or city code to search for")
    filter_by: Literal["city_code", "name", "auto"] = Field(
        default="auto",
        description="Filter type: 'city_code' for city code match, 'name' for city name match, 'auto' to search both with priority on city code",
    )


class QueryLocalCitiesDatabase(BaseTool):
    name: str = "Query Local Cities Database"
    description: str = (
        "Query the local cities database for city information. "
        "Can filter by city code or city name. "
        "Prioritizes exact city code matches over name matches when using 'auto' mode. "
        "Returns a list of city dictionaries with all fields."
    )
    args_schema: Type[BaseModel] = QueryLocalCitiesDatabaseInput

    def _load_cities_data(self):
        """Load cities data from JSON file."""
        # Get project root (assuming tool is in src/flight_concierge/tools/)
        project_root = Path(__file__).parent.parent.parent.parent
        cities_file = project_root / "db" / "cities.json"

        if not cities_file.exists():
            raise FileNotFoundError(
                f"Cities database not found at {cities_file}. Please run the service to cache data first."
            )

        with open(cities_file, "r") as f:
            return json.load(f)

    def _run(
        self,
        search_query: str,
        filter_by: Literal["city_code", "name", "auto"] = "auto",
    ) -> list[dict]:
        query_lower = search_query.lower()
        cities = self._load_cities_data()

        # Priority 1: Exact city code match
        if filter_by in ["city_code", "auto"]:
            city_code_matches = [
                city
                for city in cities
                if city.get("city_code") and query_lower == city["city_code"].lower()
            ]
            if city_code_matches:
                return city_code_matches

        # Priority 2: Name matches (partial allowed)
        if filter_by in ["name", "auto"]:
            name_matches = [
                city
                for city in cities
                if city.get("name") and query_lower in city["name"].lower()
            ]
            if name_matches:
                return name_matches

        return []
