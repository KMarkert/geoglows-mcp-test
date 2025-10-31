from mcp.server.fastmcp import FastMCP
from geoglows import data
import pandas as pd
from typing import Optional
import json

# Initialize FastMCP server
mcp = FastMCP("geoglows")

def dataframe_to_json_serializable(df: pd.DataFrame) -> list:
    """
    Converts a pandas DataFrame to a JSON serializable list of dictionaries,
    handling Timestamp objects by converting them to ISO format strings.
    """
    df_copy = df.reset_index()
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)
    return df_copy.to_dict(orient="records")

# @mcp.tool()
# async def get_reach_id(lat: float, lon: float) -> dict:
#     """
#     Get the reach_id for a given latitude and longitude.

#     Args:
#         lat: Latitude of the location.
#         lon: Longitude of the location.
#     """
#     return streams.latlon_to_reach(lat, lon).to_json()

@mcp.tool()
async def get_forecasted_streamflow(river_id: int, date: Optional[str] = None) -> dict:
    """
    Get the forecasted streamflow for a given river_id.

    Args:
        river_id: The ID of the river reach.
        date: The date for the forecast in YYYYMMDD format. Defaults to the latest forecast.
    """
    return json.dumps(dataframe_to_json_serializable(
        data.forecast(river_id=river_id, date=date, format="df")
    ), indent=2)

@mcp.tool()
async def get_historical_streamflow(river_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Get the historical streamflow for a given river_id.

    Args:
        river_id: The ID of the river reach.
        start_date: The start date for the historical data in YYYYMMDD format.
        end_date: The end date for the historical data in YYYYMMDD format.
    """
    df = data.retrospective(river_id=river_id, format="df")
    df.index = pd.to_datetime(df.index)
    if start_date:
        df = df[df.index >= pd.to_datetime(start_date, utc=True)]
    if end_date:
        df = df[df.index <= pd.to_datetime(end_date, utc=True)]
    return json.dumps(dataframe_to_json_serializable(
        df
    ), indent=2)

@mcp.tool()
async def get_forecast_stats(river_id: int, date: Optional[str] = None) -> dict:
    """
    Get the forecast statistics for a given river_id.

    Args:
        river_id: The ID of the river reach.
        date: The date for the forecast in YYYYMMDD format. Defaults to the latest forecast.
    """
    return json.dumps(dataframe_to_json_serializable(
        data.forecast_stats(river_id=river_id, date=date, format="df")
    ), indent=2)

@mcp.tool()
async def get_return_periods(river_id: int) -> dict:
    """
    Get the return periods for a given river_id.

    Args:
        river_id: The ID of the river reach.
    """
    return data.return_periods(river_id=river_id, format="df").to_json()

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
