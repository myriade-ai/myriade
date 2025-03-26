const echarts = require("echarts");
const fs = require("fs");
const path = require("path");

// Get the chart options from command line arguments
const chartOptions = JSON.parse(process.argv[2]);

// Use the SVG renderer directly
const chart = echarts.init(null, null, {
  renderer: "svg",
  ssr: true,
  width: 500,
  height: 400,
});

// Set chart options
chart.setOption(chartOptions);

// Get the SVG string
const svgStr = chart.renderToSVGString();

// Write to file
fs.writeFileSync(path.join(__dirname, "output.svg"), svgStr, "utf-8");
console.log("SVG chart has been generated as output.svg");

// Dispose the chart
chart.dispose();
