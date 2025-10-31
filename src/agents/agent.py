from enum import Enum
import io
import json
import os

import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel, Field

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.tool_context import ToolContext
from mcp import StdioServerParameters

from tools import geoglows_tools

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GeoglowsAgentOutput(BaseModel):
    data_request: str = Field(description="The type of data request to the MCP server.")
    reach_id: int = Field(description="ID for the reach or river the data is valid for.")
    data: str = Field(description="Raw JSON data returned from the MCP server.")

geoglows_data_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='geoglows_data_agent',
    instruction="""
        Help the user access streamflow data from geoglows service. 
        You must first use one of the MCP tools based on the user query and 
        return all of the data from the service.
        Provide what type of data that was requested from geoglows.
        When returning the data, return only the raw json string to
        the data structure.

        The following are examples of schemas for the different methods and must
        be formatted as shown below:

        --- get_forecasted_streamflow ---
        [
          {
            "time": "2025-10-24T00:00:00+00:00",
            "flow_uncertainty_upper": 3752.610107421875,
            "flow_median": 3752.610107421875,
            "flow_uncertainty_lower": 3752.610107421875
          },
          {
            "time": "2025-10-24T03:00:00+00:00",
            "flow_uncertainty_upper": 3773.43994140625,
            "flow_median": 3773.43994140625,
            "flow_uncertainty_lower": 3773.43994140625
          },
          {
            "time": "2025-10-24T06:00:00+00:00",
            "flow_uncertainty_upper": 3799.820068359375,
            "flow_median": 3799.820068359375,
            "flow_uncertainty_lower": 3799.81005859375
          },
          {
            "time": "2025-10-24T09:00:00+00:00",
            "flow_uncertainty_upper": 3830.780029296875,
            "flow_median": 3830.77001953125,
            "flow_uncertainty_lower": 3830.760009765625
          },
          {
            "time": "2025-10-24T12:00:00+00:00",
            "flow_uncertainty_upper": 3864.8701171875,
            "flow_median": 3864.85009765625,
            "flow_uncertainty_lower": 3864.820068359375
          },
          {
            "time": "2025-10-24T15:00:00+00:00",
            "flow_uncertainty_upper": 3900.570068359375,
            "flow_median": 3900.5400390625,
            "flow_uncertainty_lower": 3900.489990234375
          },
          {
            "time": "2025-10-24T18:00:00+00:00",
            "flow_uncertainty_upper": 3936.75,
            "flow_median": 3936.7099609375,
            "flow_uncertainty_lower": 3936.6298828125
          },
          {
            "time": "2025-10-24T21:00:00+00:00",
            "flow_uncertainty_upper": 3972.669921875,
            "flow_median": 3972.6201171875,
            "flow_uncertainty_lower": 3972.52001953125
          },
          {
            "time": "2025-10-25T00:00:00+00:00",
            "flow_uncertainty_upper": 4007.68994140625,
            "flow_median": 4007.6201171875,
            "flow_uncertainty_lower": 4007.5
          },
          {
            "time": "2025-10-25T03:00:00+00:00",
            "flow_uncertainty_upper": 4041.199951171875,
            "flow_median": 4041.110107421875,
            "flow_uncertainty_lower": 4041.0
          }
        ]

        --- get_historical_streamflow ---
        [
          {
            "time": "1940-01-01T07:00:00+00:00",
            "760701588": 4099.68994140625
          },
          {
            "time": "1940-01-01T08:00:00+00:00",
            "760701588": 4108.91015625
          },
          {
            "time": "1940-01-01T09:00:00+00:00",
            "760701588": 4118.259765625
          },
          {
            "time": "1940-01-01T10:00:00+00:00",
            "760701588": 4127.56982421875
          },
          {
            "time": "1940-01-01T11:00:00+00:00",
            "760701588": 4136.83984375
          },
          {
            "time": "1940-01-01T12:00:00+00:00",
            "760701588": 4146.0400390625
          },
          {
            "time": "1940-01-01T13:00:00+00:00",
            "760701588": 4154.64013671875
          },
          {
            "time": "1940-01-01T14:00:00+00:00",
            "760701588": 4162.08984375
          },
          {
            "time": "1940-01-01T15:00:00+00:00",
            "760701588": 4168.93017578125
          },
          {
            "time": "1940-01-01T16:00:00+00:00",
            "760701588": 4175.68994140625
          }
        ]

        --- get_forecast_stats ---
        [
          {
            "time": "2025-10-24T00:00:00+00:00",
            "flow_min": 3752.610107421875,
            "flow_25p": 3752.610107421875,
            "flow_avg": 3752.610107421875,
            "flow_med": 3752.610107421875,
            "flow_75p": 3752.610107421875,
            "flow_max": 3752.610107421875,
            "high_res": 3746.75
          },
          {
            "time": "2025-10-24T01:00:00+00:00",
            "flow_min": NaN,
            "flow_25p": NaN,
            "flow_avg": NaN,
            "flow_med": NaN,
            "flow_75p": NaN,
            "flow_max": NaN,
            "high_res": 3752.389892578125
          },
          {
            "time": "2025-10-24T02:00:00+00:00",
            "flow_min": NaN,
            "flow_25p": NaN,
            "flow_avg": NaN,
            "flow_med": NaN,
            "flow_75p": NaN,
            "flow_max": NaN,
            "high_res": 3758.68994140625
          },
          {
            "time": "2025-10-24T03:00:00+00:00",
            "flow_min": 3773.43994140625,
            "flow_25p": 3773.43994140625,
            "flow_avg": 3773.439697265625,
            "flow_med": 3773.43994140625,
            "flow_75p": 3773.43994140625,
            "flow_max": 3773.43994140625,
            "high_res": 3765.64990234375
          },
          {
            "time": "2025-10-24T04:00:00+00:00",
            "flow_min": NaN,
            "flow_25p": NaN,
            "flow_avg": NaN,
            "flow_med": NaN,
            "flow_75p": NaN,
            "flow_max": NaN,
            "high_res": 3773.25
          },
          {
            "time": "2025-10-24T05:00:00+00:00",
            "flow_min": NaN,
            "flow_25p": NaN,
            "flow_avg": NaN,
            "flow_med": NaN,
            "flow_75p": NaN,
            "flow_max": NaN,
            "high_res": 3781.469970703125
          },
          {
            "time": "2025-10-24T06:00:00+00:00",
            "flow_min": 3799.81005859375,
            "flow_25p": 3799.81005859375,
            "flow_avg": 3799.818115234375,
            "flow_med": 3799.820068359375,
            "flow_75p": 3799.820068359375,
            "flow_max": 3799.840087890625,
            "high_res": 3790.2900390625
          },
          {
            "time": "2025-10-24T07:00:00+00:00",
            "flow_min": NaN,
            "flow_25p": NaN,
            "flow_avg": NaN,
            "flow_med": NaN,
            "flow_75p": NaN,
            "flow_max": NaN,
            "high_res": 3799.669921875
          },
          {
            "time": "2025-10-24T08:00:00+00:00",
            "flow_min": NaN,
            "flow_25p": NaN,
            "flow_avg": NaN,
            "flow_med": NaN,
            "flow_75p": NaN,
            "flow_max": NaN,
            "high_res": 3809.570068359375
          },
          {
            "time": "2025-10-24T09:00:00+00:00",
            "flow_min": 3830.739990234375,
            "flow_25p": 3830.760009765625,
            "flow_avg": 3830.772705078125,
            "flow_med": 3830.77001953125,
            "flow_75p": 3830.780029296875,
            "flow_max": 3830.830078125,
            "high_res": 3819.929931640625
          }
        ]

        --- get_return_periods ---
        {
          "760701588": {
            "2": 22801.988,
            "5": 29457.746,
            "10": 33551.224,
            "25": 38436.758,
            "50": 41900.588,
            "100": 45235.886
          }
        }

        For the `data_request` field in the response, you must choose one of 
        the following options: 
        [
          `get_forecasted_streamflow`,
          `get_historical_streamflow`,
          `get_forecast_stats`,
          `get_return_periods`
        ]
    """,
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params = StdioServerParameters(
                    command='uv',
                    args=["run", "src/mcp/geoglows_mcp_server.py", "--port", "8080"],
                    cwd= project_root,
                ),
                timeout=1500,
            )
        )
    ],
    # tools = geoglows_tools.tool_list,
    output_key="streamflow_out",
    output_schema=GeoglowsAgentOutput
)


async def plot_streamflow(tool_context: ToolContext):
    """Plots streamflow data after it is recieved and saves to artifact"""
    mcp_response = tool_context.state['streamflow_out']
    if isinstance(mcp_response, str):
        mcp_response = json.loads(mcp_response)

    data_request = mcp_response['data_request']
    
    # Do not plot for return periods as it is not a time series
    if data_request == 'get_return_periods':
        return

    # The data from the agent is a JSON string, so we need to parse it
    df = pd.DataFrame(json.loads(mcp_response['data']))

    if 'time' in df.columns:
      df['time'] = pd.to_datetime(df['time'])
      df.set_index('time', inplace=True)

    buffer = io.BytesIO()

    col_to_plot = None
    if data_request == 'get_forecasted_streamflow':
        ax = col_to_plot = 'flow_median'
        ax = df[col_to_plot].plot(label='Median Flow')
        ax.fill_between(
          df.index, 
          df['flow_uncertainty_lower'],
          df['flow_uncertainty_upper'],
          color='silver',
          alpha=0.3,
          label='Uncertainty Bounds'
        )
        ax.legend()


    elif data_request == 'get_historical_streamflow':
        # For historical data, the column name is the reach_id
        col_to_plot = str(mcp_response['reach_id'])
        ax = df[col_to_plot].plot()

    elif data_request == 'get_forecast_stats':
        col_to_plot = 'flow_avg'


    if col_to_plot and col_to_plot in df.columns:
        
        # fig = ax.get_figure()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()

        print(buffer.getvalue())

        await tool_context.save_artifact(
            'geoglows_plot.png',
            types.Part.from_bytes(data=buffer.getvalue(), mime_type='image/png')
        )
    

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='geoglows_agent',
    instruction="""
        Help the user access and plot streamflow data from geoglows service. 
        You must first retrieve data from the subagent before attempting to plot anything.,
    """,
    tools=[
        AgentTool(geoglows_data_agent),
        plot_streamflow,
    ],
)
