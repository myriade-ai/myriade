import json
import os
import subprocess
import uuid

from PIL import Image

from back.data_warehouse import AbstractDatabase
from chat.tools.chart_types import ChartOptions
from models import Chart, ConversationMessage, Database, Query


class EchartsTool:
    def __init__(
        self,
        session,
        database: Database,
        data_warehouse: AbstractDatabase,
    ):
        self.session = session
        self.database = database
        # Reuse provided data_warehouse instance or create new one
        self.data_warehouse = data_warehouse

    def __llm__(self):
        return "Render Echarts Tool"

    def list_chart_types(self) -> dict:
        """
        List all available ECharts chart types with descriptions.

        Returns:
            dict: A dictionary containing chart types categorized by their use case
        """
        return {
            "basic_charts": {
                "line": {
                    "description": "Line chart for showing trends over time or continuous data",
                    "use_cases": [
                        "Time series",
                        "Trends",
                        "Continuous data comparison",
                    ],
                    "supports_multiple_series": True,
                },
                "bar": {
                    "description": "Bar chart for comparing values across categories",
                    "use_cases": ["Category comparison", "Rankings", "Distribution"],
                    "supports_multiple_series": True,
                },
                "pie": {
                    "description": "Pie chart for showing proportions and percentages",
                    "use_cases": [
                        "Proportions",
                        "Percentages",
                        "Part-to-whole relationships",
                    ],
                    "supports_multiple_series": False,
                },
                "scatter": {
                    "description": "Scatter plot for showing correlation between two variables",
                    "use_cases": ["Correlation", "Distribution", "Clustering"],
                    "supports_multiple_series": True,
                },
            },
            "advanced_charts": {
                "boxplot": {
                    "description": "Box plot for statistical analysis showing quartiles and outliers",
                    "use_cases": [
                        "Statistical distribution",
                        "Outlier detection",
                        "Data spread",
                    ],
                    "supports_multiple_series": True,
                },
                "candlestick": {
                    "description": "Candlestick chart for financial data (open, close, high, low)",
                    "use_cases": ["Financial data", "Stock prices", "OHLC data"],
                    "supports_multiple_series": False,
                },
                "heatmap": {
                    "description": "Heatmap for showing magnitude of values in a matrix",
                    "use_cases": [
                        "Matrix data",
                        "Correlation matrices",
                        "Calendar data",
                    ],
                    "supports_multiple_series": False,
                },
                "treemap": {
                    "description": "Treemap for hierarchical data with nested rectangles",
                    "use_cases": [
                        "Hierarchical data",
                        "Part-to-whole with hierarchy",
                        "File systems",
                    ],
                    "supports_multiple_series": False,
                },
                "sunburst": {
                    "description": "Sunburst chart for multi-level hierarchical data",
                    "use_cases": ["Multi-level hierarchies", "Nested proportions"],
                    "supports_multiple_series": False,
                },
                "sankey": {
                    "description": "Sankey diagram for flow and relationship visualization",
                    "use_cases": ["Flow analysis", "Energy transfer", "Process flows"],
                    "supports_multiple_series": False,
                },
                "funnel": {
                    "description": "Funnel chart for showing stages in a process",
                    "use_cases": [
                        "Conversion rates",
                        "Process stages",
                        "Sales funnels",
                    ],
                    "supports_multiple_series": True,
                },
                "gauge": {
                    "description": "Gauge chart for showing single value within a range",
                    "use_cases": ["KPIs", "Progress indicators", "Single metrics"],
                    "supports_multiple_series": False,
                },
                "radar": {
                    "description": "Radar chart for multivariate data comparison",
                    "use_cases": [
                        "Multi-dimensional comparison",
                        "Profiles",
                        "Skills assessment",
                    ],
                    "supports_multiple_series": True,
                },
                "graph": {
                    "description": "Graph/Network diagram for relationships and connections",
                    "use_cases": [
                        "Networks",
                        "Relationships",
                        "Connections",
                        "Social graphs",
                    ],
                    "supports_multiple_series": False,
                },
            },
            "map_charts": {
                "map": {
                    "description": "Geographic map visualization",
                    "use_cases": [
                        "Geographic data",
                        "Regional analysis",
                        "Location-based metrics",
                    ],
                    "supports_multiple_series": True,
                },
            },
        }

    def get_chart_configuration(self, chart_type: str) -> dict:
        """
        Get detailed configuration options for a specific chart type.

        Args:
            chart_type: The type of chart (e.g., 'line', 'bar', 'pie', 'scatter')

        Returns:
            dict: Detailed configuration options for the chart type
        """
        configurations = {
            "line": {
                "series_options": {
                    "type": "line",
                    "smooth": "Whether to smooth the line (boolean or number 0-1)",
                    "symbol": "Symbol type for data points: 'circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow', 'none'",
                    "symbolSize": "Size of the symbol (number or array [width, height])",
                    "lineStyle": {
                        "color": "Line color",
                        "width": "Line width",
                        "type": "'solid', 'dashed', or 'dotted'",
                    },
                    "areaStyle": "Add to fill area under line (object or null)",
                    "stack": "Stack multiple series (string identifier)",
                    "step": "Step line: 'start', 'middle', 'end', or false",
                    "encode": {
                        "x": "Column name for x-axis",
                        "y": "Column name for y-axis",
                    },
                },
                "axis_options": {
                    "xAxis": {
                        "type": "'category', 'value', 'time', or 'log'",
                        "name": "Axis name",
                        "boundaryGap": "Gap on both sides (boolean)",
                    },
                    "yAxis": {
                        "type": "'value', 'category', 'time', or 'log'",
                        "name": "Axis name",
                        "min": "Minimum value",
                        "max": "Maximum value",
                    },
                },
                "common_options": {
                    "title": {
                        "text": "Chart title",
                        "left": "Position: 'left', 'center', 'right'",
                    },
                    "tooltip": {
                        "trigger": "'axis' or 'item'",
                        "formatter": "Custom formatter",
                    },
                    "legend": {
                        "data": "Array of series names",
                        "orient": "'horizontal' or 'vertical'",
                    },
                    "grid": {
                        "left": "Left margin",
                        "right": "Right margin",
                        "top": "Top margin",
                        "bottom": "Bottom margin",
                    },
                    "dataZoom": "Enable zoom/pan (array of zoom configs)",
                },
            },
            "bar": {
                "series_options": {
                    "type": "bar",
                    "barWidth": "Width of bars (number or percentage string)",
                    "barGap": "Gap between bars in same category (percentage string, e.g., '30%')",
                    "barCategoryGap": "Gap between categories (percentage string)",
                    "stack": "Stack multiple series (string identifier)",
                    "itemStyle": {
                        "color": "Bar color",
                        "borderRadius": "Border radius (number or array)",
                    },
                    "label": {
                        "show": "Show labels on bars (boolean)",
                        "position": "'top', 'left', 'right', 'bottom', 'inside', etc.",
                        "formatter": "Label formatter using {@column_name} syntax",
                    },
                    "encode": {
                        "x": "Column name for x-axis",
                        "y": "Column name for y-axis",
                    },
                },
                "axis_options": {
                    "xAxis": {
                        "type": "'category' for vertical bars, 'value' for horizontal",
                        "name": "Axis name",
                        "axisLabel": {
                            "rotate": "Rotate labels (degrees)",
                            "interval": "Label interval",
                        },
                    },
                    "yAxis": {
                        "type": "'value' for vertical bars, 'category' for horizontal",
                        "name": "Axis name",
                        "min": "Minimum value",
                        "max": "Maximum value",
                    },
                },
                "common_options": {
                    "title": {"text": "Chart title"},
                    "tooltip": {"trigger": "'axis' recommended for bars"},
                    "legend": {"data": "Array of series names"},
                    "grid": {"containLabel": "Include labels in grid (boolean)"},
                },
            },
            "pie": {
                "series_options": {
                    "type": "pie",
                    "radius": "Pie radius (string '50%' or array ['40%', '70%'] for donut)",
                    "center": "Pie center position (array ['50%', '50%'])",
                    "roseType": "Rose diagram: false, 'radius', or 'area'",
                    "label": {
                        "show": "Show labels (boolean)",
                        "position": "'outside', 'inside', or 'center'",
                        "formatter": "Label formatter using {@column_name} syntax",
                    },
                    "labelLine": {
                        "show": "Show label lines (boolean)",
                        "length": "Label line length",
                    },
                    "itemStyle": {
                        "borderRadius": "Border radius for pie sectors",
                        "borderColor": "Border color",
                        "borderWidth": "Border width",
                    },
                    "emphasis": {
                        "itemStyle": {"shadowBlur": "Shadow effect on hover"},
                    },
                    "encode": {
                        "itemName": "Column name for item names",
                        "value": "Column name for values",
                    },
                },
                "common_options": {
                    "title": {"text": "Chart title"},
                    "tooltip": {"trigger": "'item' for pie charts"},
                    "legend": {
                        "orient": "'vertical' or 'horizontal'",
                        "left": "Legend position",
                    },
                },
            },
            "scatter": {
                "series_options": {
                    "type": "scatter",
                    "symbolSize": "Size of scatter points (number or function)",
                    "symbol": "Symbol shape: 'circle', 'rect', 'triangle', etc.",
                    "itemStyle": {
                        "color": "Point color",
                        "opacity": "Point opacity (0-1)",
                    },
                    "label": {
                        "show": "Show labels (boolean)",
                        "formatter": "Label formatter",
                    },
                    "encode": {
                        "x": "Column name for x-axis",
                        "y": "Column name for y-axis",
                    },
                },
                "axis_options": {
                    "xAxis": {
                        "type": "Usually 'value' for scatter",
                        "name": "Axis name",
                        "scale": "Scale axis (boolean)",
                    },
                    "yAxis": {
                        "type": "Usually 'value' for scatter",
                        "name": "Axis name",
                        "scale": "Scale axis (boolean)",
                    },
                },
                "common_options": {
                    "title": {"text": "Chart title"},
                    "tooltip": {"trigger": "'item' for scatter"},
                    "dataZoom": "Enable zoom for large datasets",
                },
            },
            "heatmap": {
                "series_options": {
                    "type": "heatmap",
                    "label": {
                        "show": "Show values in cells (boolean)",
                    },
                    "itemStyle": {
                        "borderWidth": "Cell border width",
                        "borderColor": "Cell border color",
                    },
                    "encode": {
                        "x": "Column for x-axis categories",
                        "y": "Column for y-axis categories",
                    },
                },
                "axis_options": {
                    "xAxis": {
                        "type": "'category'",
                        "splitArea": {"show": "Show split areas"},
                    },
                    "yAxis": {
                        "type": "'category'",
                        "splitArea": {"show": "Show split areas"},
                    },
                },
                "common_options": {
                    "visualMap": {
                        "min": "Minimum value for color mapping",
                        "max": "Maximum value for color mapping",
                        "calculable": "Show draggable handles (boolean)",
                        "orient": "'vertical' or 'horizontal'",
                        "inRange": {"color": "Color range (array of colors)"},
                    },
                    "tooltip": {"position": "'top'"},
                },
            },
            "radar": {
                "series_options": {
                    "type": "radar",
                    "areaStyle": "Fill area (object or null)",
                    "lineStyle": {"width": "Line width"},
                    "itemStyle": {"color": "Point color"},
                },
                "radar_options": {
                    "indicator": "Array of {name, max} objects for each axis",
                    "shape": "'polygon' or 'circle'",
                    "splitNumber": "Number of split segments",
                    "center": "Radar center position",
                    "radius": "Radar radius",
                },
                "common_options": {
                    "title": {"text": "Chart title"},
                    "legend": {"data": "Array of series names"},
                    "tooltip": {"trigger": "'item'"},
                },
            },
            "funnel": {
                "series_options": {
                    "type": "funnel",
                    "sort": "'ascending', 'descending', or 'none'",
                    "gap": "Gap between funnel pieces",
                    "label": {
                        "show": "Show labels",
                        "position": "'left', 'right', 'inside'",
                    },
                    "funnelAlign": "'left', 'center', or 'right'",
                },
                "common_options": {
                    "title": {"text": "Chart title"},
                    "tooltip": {"trigger": "'item'"},
                    "legend": {"data": "Array of stage names"},
                },
            },
        }

        if chart_type not in configurations:
            available_types = list(configurations.keys())
            return {
                "error": f"Chart type '{chart_type}' configuration not available",
                "available_types": available_types,
                "note": "For other chart types, refer to ECharts documentation at https://echarts.apache.org/en/option.html",
            }

        return configurations[chart_type]

    def preview_render(
        self,
        chart_options: ChartOptions,
        query_id: str,
        from_response: ConversationMessage,
    ):
        """
        Render a chart (using Echarts 6).
        This is not shown to the user, but this will create a chart object
        That you can reference in the answer response.
        ---
        Provide the chart_options without the "dataset" parameter
        We will fill the dataset.source automatically with the SQL result
        Don't forget to Map from Data to Charts (series.encode) using the correct names
        Don't use specific color in the chart_options unless the user asked for it
        When creating bar charts with ECharts, make sure to set the correct axis types.

        IMPORTANT: When using formatters with encoded data, use the {@column_name} syntax.
        For example:
        - For labels: "formatter": "{@nps_score}%"
        - For tooltips: "formatter": "Mois: {@mois}<br/>Score NPS: {@nps_score}%"
        - NOT: "formatter": "{c}%" (this will show [Object Object])

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

        query = (
            self.session.query(Query).filter(Query.id == uuid.UUID(query_id)).first()
        )
        rows, *_ = self.data_warehouse.query(query.sql, role="llm")
        chart_options = chart_options.copy()
        chart_options["dataset"] = {  # type: ignore
            "source": rows,  # Already serialized at the data layer
        }
        json_str = json.dumps(chart_options)  # Convert to string
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
            output_path = os.path.join(current_dir, "echarts-render", "output.png")
            try:
                return Image.open(output_path)
            except FileNotFoundError:
                return f"Error: Could not find output PNG file. \
                    Node.js output: {result.stdout}\nErrors: {result.stderr}"
            except Exception as e:
                return f"Error reading PNG file: {str(e)}"
        except subprocess.CalledProcessError as e:
            return f"Error executing Node.js script: {e.stderr}"
        except Exception as e:
            return f"Unexpected error running chart renderer: {str(e)}"
