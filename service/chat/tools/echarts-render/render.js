const echarts = require("echarts");
const path = require("path");
const sharp = require("sharp")

// Get the chart options from command line arguments
const chartOptions = JSON.parse(process.argv[2]);

// Get optional width and height from command line arguments, with defaults
const width = process.argv[3] ? parseInt(process.argv[3]) : 500;
const height = process.argv[4] ? parseInt(process.argv[4]) : 400;

// Get optional output path from command line arguments, with default
const pngPath = process.argv[5] ? process.argv[5] : path.join(__dirname, "output.png");

// Use the SVG renderer directly
const chart = echarts.init(null, null, {
  renderer: "svg",
  ssr: true,
  width: width,
  height: height,
});

// Set chart options
chart.setOption(chartOptions);

// Get the SVG string
const svgStr = chart.renderToSVGString();

// Convert SVG to PNG using sharp with high quality settings
sharp(Buffer.from(svgStr))
  .png({
    compressionLevel: 6,
    quality: 100,
  })
  .withMetadata({ density: 300 }) // Set DPI to 300 for print quality
  .toFile(pngPath)
  .then(() => {
    console.log(`PNG chart has been generated: ${pngPath}`);
    // Dispose the chart
    chart.dispose();
  })
  .catch(err => {
    console.error("Error converting SVG to PNG:", err);
    // Dispose the chart even if conversion fails
    chart.dispose();
    process.exit(1);
  });
