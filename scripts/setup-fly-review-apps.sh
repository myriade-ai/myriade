#!/bin/bash

# Setup script for Fly.io Review Apps
# This script helps configure the necessary components for review apps

set -e

echo "🚀 Setting up Fly.io Review Apps for Myriade"
echo "============================================="

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   macOS: brew install flyctl"
    echo "   Linux: curl -L https://fly.io/install.sh | sh"
    echo "   Windows: iwr https://fly.io/install.ps1 -useb | iex"
    exit 1
fi

echo "✅ flyctl is installed"

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run:"
    echo "   flyctl auth login"
    exit 1
fi

echo "✅ Logged in to Fly.io"

# Get user info
FLY_USER=$(flyctl auth whoami)
echo "👤 Logged in as: $FLY_USER"

# Generate API token
echo ""
echo "🔑 Generating API token for GitHub Actions..."
echo "Please copy this token and add it as a GitHub Secret named 'FLY_API_TOKEN':"
echo ""
flyctl auth token
echo ""

# Check if we're in the right directory
if [ ! -f "fly.toml" ]; then
    echo "❌ fly.toml not found. Are you in the project root directory?"
    exit 1
fi

echo "✅ Found fly.toml configuration"

# Check GitHub workflow
if [ ! -f ".github/workflows/review-apps.yml" ]; then
    echo "❌ GitHub workflow not found at .github/workflows/review-apps.yml"
    exit 1
fi

echo "✅ Found GitHub Actions workflow"

# Validate fly.toml
echo ""
echo "🔍 Validating Fly.io configuration..."
if flyctl config validate; then
    echo "✅ Fly.io configuration is valid"
else
    echo "❌ Fly.io configuration has errors"
    exit 1
fi

# Show next steps
echo ""
echo "🎉 Setup complete! Next steps:"
echo ""
echo "1. Add the API token above as a GitHub Secret:"
echo "   - Go to your repo → Settings → Secrets and variables → Actions"
echo "   - Add new secret: FLY_API_TOKEN"
echo ""
echo "2. Set up application secrets (required):"
echo "   flyctl secrets set ANTHROPIC_API_KEY=your_key_here"
echo ""
echo "3. Optional secrets:"
echo "   flyctl secrets set OPENAI_API_KEY=your_key_here"
echo "   flyctl secrets set SENTRY_DSN=your_dsn_here"
echo ""
echo "4. Create a pull request to test the review app deployment!"
echo ""
echo "📚 For more information, see docs/fly-review-apps.md"