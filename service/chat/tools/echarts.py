import json
import os
import subprocess

from cairosvg import svg2png
from PIL import Image

from back.datalake import DatalakeFactory
from back.models import Chart, ConversationMessage, Database, JSONEncoder, Query
from chat.tools.chart_types import ChartOptions


class EchartsTool:
    def __init__(self, session, database: Database):
        self.session = session
        self.database = database
        self.datalake = DatalakeFactory.create(
            self.database.engine,
            **self.database.details,
        )

    def preview_render(
        self,
        chart_options: ChartOptions,
        query_id: int,
        from_response: ConversationMessage,
    ):
        """
        Render a chart (using Echarts 4).
        This is not shown to the user, but this will create a chart object
        That you can reference in the answer response.
        ---
        Provide the chart_options without the "dataset" parameter
        We will SQL result to fill the dataset.source automatically
        Don't forget to Map from Data to Charts (series.encode)
        Don't use specific color in the chart_options unless the user asked for it
        When creating bar charts with ECharts, make sure to set the correct axis types.
        For categorical data (like driver names) use 'category' type on the x-axis when displaying bars vertically, or on the y-axis when displaying bars horizontally.
        For numerical data (like wins or points) use 'value' type on the corresponding axis.
        Also verify that the encode properties correctly map your data fields to the appropriate axes ('x' for categories, 'y' for values in vertical bar charts; reversed in horizontal bar charts).
        Args:
            chart_options: The options of the chart. A dict, not a json dump
            query_id: The ID of the query to execute
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
        self.session.commit()

        query = self.session.query(Query).filter(Query.id == query_id).first()
        rows, _ = self.datalake.query(query.sql)
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
