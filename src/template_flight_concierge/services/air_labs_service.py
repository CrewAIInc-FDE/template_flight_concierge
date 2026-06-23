import json
from pathlib import Path

from get_flight_airport_codes import GetFlightAirportCodes
from get_flight_city_codes import GetFlightCityCodes
from get_flight_country_codes import GetFlightCountryCodes


class AirLabsService:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.db_folder = self.project_root / "db"
        self.db_folder.mkdir(exist_ok=True)

    def ensure_countries_cached(self):
        countries_file = self.db_folder / "countries.json"

        if not countries_file.exists():
            print("Fetching countries from API...")
            data = GetFlightCountryCodes().run()
            countries_data = data["response"]

            with open(countries_file, "w") as f:
                json.dump(countries_data, f, indent=2)
            print(f"Countries cached to {countries_file}")

    def ensure_cities_cached(self):
        cities_file = self.db_folder / "cities.json"

        if not cities_file.exists():
            print("Fetching cities from API...")
            data = GetFlightCityCodes().run()
            cities_data = data["response"]

            with open(cities_file, "w") as f:
                json.dump(cities_data, f, indent=2)
            print(f"Cities cached to {cities_file}")

    def ensure_airports_cached(self):
        airports_file = self.db_folder / "airports.json"

        if not airports_file.exists():
            print("Fetching airports from API...")
            data = GetFlightAirportCodes().run()
            airports_data = data["response"]

            with open(airports_file, "w") as f:
                json.dump(airports_data, f, indent=2)
            print(f"Airports cached to {airports_file}")
