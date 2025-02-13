import asyncio
import json
import os

import numpy as np
from playwright.async_api import async_playwright

# Generate HTML for FusionCharts
html_template = """
<html>
<head>
    <script type="text/javascript" src="https://cdn.fusioncharts.com/fusioncharts/latest/fusioncharts.js"></script>
    <script type="text/javascript" src="https://cdn.fusioncharts.com/fusioncharts/latest/themes/fusioncharts.theme.fusion.js"></script>
</head>
<body>
    <div id="chart-container"></div>
    <script type="text/javascript">
        FusionCharts.ready(function() {{
            var chartObj = new FusionCharts(CHART_CONFIG);
            chartObj.render();
        }});
    </script>
</body>
</html>
"""


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.datetime64):
            return obj.astype(str)
        elif hasattr(
            obj, "isoformat"
        ):  # This covers datetime.datetime and pandas.Timestamp
            return obj.isoformat()
        return super().default(obj)


async def render_chart_async(chart_config):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            chart_config_json = json.dumps(chart_config, cls=NumpyEncoder)
            html = html_template.replace("CHART_CONFIG", chart_config_json)
            await page.set_content(html)
            await page.wait_for_timeout(5000)  # Wait for chart to render

            # Capture screenshot
            chart_image = await page.screenshot()
            print("Chart rendered and screenshot captured successfully")
        finally:
            await browser.close()

    # if "dev" environment, save the image to a file
    if os.getenv("ENV") == "dev":
        with open("/tmp/chart.png", "wb") as f:
            f.write(chart_image)

    return chart_image


def render_chart(chart_config):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(render_chart_async(chart_config))
    finally:
        loop.close()


# No cleanup function needed in this simplified version
