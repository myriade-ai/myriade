import json
import os
import subprocess

from cairosvg import svg2png
from PIL import Image

from chat.tools.chart_types import ChartOptions
from db import JSONEncoder
from models import Chart, ConversationMessage, Database, Query


class EchartsTool:
    def __init__(self, session, database: Database):
        self.session = session
        self.database = database
        self.datalake = self.database.create_datalake()

    def preview_render(
        self,
        chart_options: ChartOptions,
        query_id: str,
        from_response: ConversationMessage,
    ):
        """
        Render a chart (using Echarts 4).
        This is not shown to the user, but this will create a chart object
        That you can reference in the answer response.
        ---
        Provide the chart_options without the "dataset" parameter
        We will fill the dataset.source automatically with the SQL result
        Don't forget to Map from Data to Charts (series.encode) using the correct names
        Don't use specific color in the chart_options unless the user asked for it
        When creating bar charts with ECharts, make sure to set the correct axis types.
        Args:
            chart_options: The options of the chart. A dict, not a json dump
            query_id: The uuid of the query to execute
        """  # noqa: E501
        if isinstance(chart_options, str):
            try:
                chart_options = json.loads(chart_options)
            except json.JSONDecodeError:
                raise ValueError("chart_options shouldn't be a json dump") from None

        chart = Chart(
            config=chart_options,
            queryId=query_id,
        )
        self.session.add(chart)
        self.session.flush()
        from_response.chartId = chart.id
        self.session.flush()

        query = self.session.query(Query).filter(Query.id == query_id).first()
        rows, _ = self.datalake.query(query.sql, role="llm")
        chart_options = chart_options.copy()
        chart_options["dataset"] = {
            "source": rows,
        }
        json_str = json.dumps(chart_options, cls=JSONEncoder)  # Convert to string
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            render_script_path = os.path.join(
                current_dir, "echarts-render", "render.js"
            )
            result = subprocess.run(
                ["node", render_script_path, json_str],
                capture_output=True,
                text=True,
                check=True,
            )
            render_path = os.path.join(current_dir, "echarts-render", "output.svg")
            output_path = os.path.join(current_dir, "echarts-render", "output.png")
            try:
                with open(render_path, "r") as file:
                    svg_content = file.read()
                svg2png(bytestring=svg_content, write_to=output_path)
                return Image.open(output_path)
            except FileNotFoundError:
                return f"Error: Could not find output SVG file. \
                    Node.js output: {result.stdout}\nErrors: {result.stderr}"
            except Exception as e:
                return f"Error reading SVG file: {str(e)}"
        except subprocess.CalledProcessError as e:
            return f"Error executing Node.js script: {e.stderr}"
        except Exception as e:
            return f"Unexpected error running chart renderer: {str(e)}"

    def __repr__(self):
        return "Render Echarts Tool"
