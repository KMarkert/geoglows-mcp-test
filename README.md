# GEOGLOWS MCP Server and Agent

This project provides a Model Context Protocol (MCP) server for the GEOGLOWS API and an intelligent agent that uses the server to fetch and process global streamflow data.

## About the GEOGLOWS Hydrology Model
The GEOGLOWS Hydrology Model is run each day at midnight (UTC +00). The model is based on the ECMWF ENS and HRES ensemble of meteorology and land surface model forecasts. There are 51 members of the ensemble that drives the model each day. The ERA5 reanalysis dataset is also used to produce a retrospective simulation on each river. The model provides river in units m^3/s over the preceeding interval (1, 3, or 24 hours depending on the dataset).

## Components

### 1. GEOGLOWS MCP Server
The MCP server (`src/mcp/geoglows_mcp_server.py`) provides direct access to the GEOGLOWS API through a set of tools.

#### Available Tools

- **`get_forecasted_streamflow(river_id: int, date: Optional[str] = None)`**: Fetches forecasted streamflow for a given river reach.
- **`get_historical_streamflow(river_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None)`**: Fetches historical streamflow for a given river reach.
- **`get_forecast_stats(river_id: int, date: Optional[str] = None)`**: Fetches forecast statistics for a given river reach.
- **`get_return_periods(river_id: int)`**: Fetches return periods for a given river reach.

### 2. Geoglows Agent
The agent (`src/agents/agent.py`) is a more advanced component that uses the MCP server to fulfill user requests for streamflow data. It consists of two main parts:

- **`geoglows_data_agent`**: An LLM agent that interprets user queries, calls the appropriate tool on the MCP server to get streamflow data, and returns the raw JSON data.
- **`root_agent`**: A higher-level agent that orchestrates the process. It uses the `geoglows_data_agent` to fetch data and then uses a `plot_streamflow` tool to visualize the time-series data, saving the output as a PNG artifact.

### How They Interact

The `geoglows_data_agent` is configured to start the `geoglows_mcp_server.py` as a subprocess using `stdio` for communication. When the agent receives a task (e.g., "get the forecast for river 12345"), it determines which MCP tool to use (`get_forecasted_streamflow`), calls it on the running server, and receives the data. The `root_agent` then takes this data and can perform further actions, like plotting.

This architecture separates the core data-access logic (MCP Server) from the intelligent, task-oriented logic (Agent), making the system modular and extensible.

### Getting Started

#### Prerequisites
- Python 3.12+
- `uv` for package management

#### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/KMarkert/geoglows-mcp-test.git
   cd geoglows-mcp-test
   ```

2. Create a virtual environment and install dependencies using `uv`:
   ```bash
   uv venv
   uv sync
   ```

#### Running the agent dev server

To run the MCP server directly, execute the following command:

```bash
uv run adk web
```
