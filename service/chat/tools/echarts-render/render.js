const echarts = require("echarts");
const path = require("path");
const sharp = require("sharp")

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

const pngPath = path.join(__dirname, "output.png");

// Convert SVG to PNG using sharp
sharp(Buffer.from(svgStr))
  .png()
  .toFile(pngPath)
  .then(() => {
    console.log("PNG chart has been generated as output.png");
    // Dispose the chart
    chart.dispose();
  })
  .catch(err => {
    console.error("Error converting SVG to PNG:", err);
    // Dispose the chart even if conversion fails
    chart.dispose();
    process.exit(1);
  });
