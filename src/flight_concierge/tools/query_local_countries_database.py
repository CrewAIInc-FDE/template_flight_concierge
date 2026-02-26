import json
from pathlib import Path
from typing import Literal, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class QueryLocalCountriesDatabaseInput(BaseModel):
    """Input schema for QueryLocalCountriesDatabase."""

    search_query: str = Field(
        ..., description="Country code or country name to search for"
    )
    filter_by: Literal["code", "name", "auto"] = Field(
        default="auto",
        description="Filter type: 'code' for country code match, 'name' for country name match, 'auto' to search both with priority on code",
    )


class QueryLocalCountriesDatabase(BaseTool):
    name: str = "Query Local Countries Database"
    description: str = (
        "Query the local countries database for country information. "
        "Can filter by country code or country name. "
        "Prioritizes exact country code matches over name matches when using 'auto' mode. "
        "Returns a list of country dictionaries with all fields."
    )
    args_schema: Type[BaseModel] = QueryLocalCountriesDatabaseInput

    def _load_countries_data(self):
        """Load countries data from JSON file."""
        # Get project root (assuming tool is in src/flight_concierge/tools/)
        project_root = Path(__file__).parent.parent.parent.parent
        countries_file = project_root / "db" / "countries.json"

        if not countries_file.exists():
            raise FileNotFoundError(
                f"Countries database not found at {countries_file}. Please run the service to cache data first."
            )

        with open(countries_file, "r") as f:
            return json.load(f)

    def _run(
        self,
        search_query: str,
        filter_by: Literal["code", "name", "auto"] = "auto",
    ) -> list[dict]:
        query_lower = search_query.lower()
        countries = self._load_countries_data()

        # Priority 1: Exact country code match
        if filter_by in ["code", "auto"]:
            code_matches = [
                country
                for country in countries
                if country.get("code") and query_lower == country["code"].lower()
            ]
            if code_matches:
                return code_matches

        # Priority 2: Name matches (partial allowed)
        if filter_by in ["name", "auto"]:
            name_matches = [
                country
                for country in countries
                if country.get("name") and query_lower in country["name"].lower()
            ]
            if name_matches:
                return name_matches

        return []
