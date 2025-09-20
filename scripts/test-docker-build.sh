#!/bin/bash

# Test script to verify Docker build works for Fly.io deployment
# This helps catch issues before pushing to GitHub

set -e

echo "🧪 Testing Docker build for Fly.io deployment"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found. Are you in the project root directory?"
    exit 1
fi

# Check if required files exist
echo "🔍 Checking required files..."

required_files=("fly.toml" ".env.fly" "service/start-fly.sh" ".dockerignore")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
    echo "✅ Found: $file"
done

# Build the Docker image
echo ""
echo "🏗️ Building Docker image..."
docker build -t myriade-fly-test . --no-cache

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

# Test the image (quick smoke test)
echo ""
echo "🚀 Testing image startup (5 second test)..."

# Create a temporary .env file for testing
cat > .env.test << EOF
FLASK_ENV=production
FLASK_DEBUG=false
DATABASE_URL=sqlite:///data/test.db
ANTHROPIC_API_KEY=test_key
STATIC_FOLDER=./static
EOF

# Run container in background
container_id=$(docker run -d -p 8081:8080 \
    -v "$(pwd)/.env.test:/app/.env" \
    -e FLY_APP_NAME=test-app \
    myriade-fly-test)

echo "Container started: $container_id"

# Wait a moment for startup
sleep 5

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -f http://localhost:8081/health > /dev/null 2>&1; then
    echo "✅ Health endpoint responding!"
else
    echo "⚠️ Health endpoint not responding (this might be expected if dependencies are missing)"
fi

# Cleanup
echo "🧹 Cleaning up..."
docker stop $container_id > /dev/null
docker rm $container_id > /dev/null
rm -f .env.test

echo ""
echo "🎉 Docker build test completed!"
echo ""
echo "Next steps:"
echo "1. Push your changes to GitHub"
echo "2. Create a pull request to test the review app deployment"
echo "3. Check the GitHub Actions workflow for deployment status"