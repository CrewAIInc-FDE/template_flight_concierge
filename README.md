# Flight Concierge

An intelligent AI-powered travel assistant built with [crewAI](https://crewai.com) that helps users find the best flight options through a conversational interface with human feedback loops.

## Overview

Flight Concierge is a CrewAI Flow application that guides users through trip planning by:
- Understanding travel requests in natural language (supports multiple languages)
- Identifying optimal departure and arrival airports based on proximity and convenience
- Gathering and confirming trip details through interactive feedback
- Searching for the best available flights via Google Flights

The system uses a stateful flow architecture with human-in-the-loop feedback to ensure accuracy and user satisfaction at each stage of the planning process.

## Features

- **Multi-language Support**: Responds in the user's preferred language
- **Intelligent Location Processing**: Identifies countries, cities, and nearby airports using a local database and external APIs
- **Airport Recommendations**: Suggests convenient airports within 30km of target cities, filtering by popularity
- **Human Feedback Loops**: Confirms trip details before proceeding with flight searches
- **Flight Search Integration**: Queries Google Flights for best available options (one-way and round-trip)
- **Persistent State**: Maintains conversation history and trip data throughout the flow

## Prerequisites

- Python >=3.10 <3.14
- [UV](https://docs.astral.sh/uv/) package manager

## Installation

Install UV if you haven't already:

```bash
pip install uv
```

Install project dependencies:

```bash
crewai install
```

Configure environment variables by copying `.env.example` to `.env`:

```bash
cp .env.example .env
```

Add your API keys to `.env`:

```env
AIRLABS_API_KEY=your_airlabs_key
OPENAI_API_KEY=your_openai_key
SERPAPI_API_KEY=your_serpapi_key
```

## Usage

Run the flight concierge flow:

```bash
crewai run
```

Or use the Python entry point:

```bash
python -m flight_concierge.main
```

Visualize the flow structure:

```bash
crewai plot
```

## Architecture

### Flow Structure

The application implements a CrewAI Flow with the following stages:

1. **Load Initial Context**: Initializes services and agents
2. **Collect Location Data**: Fetches and caches countries, cities, and airports databases
3. **Acknowledge Message**: Greets user and confirms request understanding
4. **Process Departure/Arrival**: Extracts location and date information in parallel
5. **Draft Trip Plan**: Presents trip details for user review (human feedback)
6. **Feedback Loop**: Iterates on changes until user approves
7. **Search Flights**: Queries Google Flights for best available options

### Key Components

- **FlightConciergeAgent**: Main agent orchestrating the travel planning process
- **AirLabsService**: Manages caching of location databases (countries, cities, airports)
- **Custom Tools**:
  - `QueryLocalCountriesDatabase`: Searches local country codes
  - `QueryLocalCitiesDatabase`: Searches local city codes with coordinates
  - `QueryLocalAirportsDatabase`: Searches local airport codes
  - `GetFlightAirportsNearby`: Finds nearby airports using coordinates (API call)
  - `GetFlightsFromGoogleFlights`: Searches flight options via SerpAPI

### State Management

The flow maintains a `FlightConciergeState` containing:
- Conversation messages
- Trip data (legs, airports, dates)
- User interactions and reviews
- Human feedback history

## Project Structure

```
flight_concierge/
├── src/flight_concierge/
│   ├── agents/
│   │   └── flight_concierge_agent.py
│   ├── services/
│   │   └── air_labs_service.py
│   ├── tools/
│   │   ├── get_flights_from_google_flights.py
│   │   ├── query_local_airports_database.py
│   │   ├── query_local_cities_database.py
│   │   └── query_local_countries_database.py
│   ├── types/
│   │   ├── airport.py
│   │   ├── arrival_data.py
│   │   ├── departure_data.py
│   │   ├── flight_concierge_state.py
│   │   └── ...
│   └── main.py
├── db/                    # Auto-generated location databases
├── .env.example
├── pyproject.toml
└── README.md
```

## Support

- [crewAI Documentation](https://docs.crewai.com)
- [crewAI GitHub](https://github.com/joaomdmoura/crewai)
- [Join Discord](https://discord.com/invite/X4JWnZnxPb)
