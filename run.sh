#!/bin/bash

# Android Version Distribution - Self-contained runner
# Fetches Android version data from Google Analytics and updates the visualization

echo "🤖 Android Version Distribution - Data Fetcher & Visualizer"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import google.analytics.data_v1beta" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Run the data fetcher
echo "▶️  Fetching Android version data from Google Analytics..."
echo ""
python fetch_android_versions.py

# Update the HTML with embedded CSV data
if [ -f "android_versions_report.csv" ]; then
    echo ""
    echo "📋 Updating visualization..."
    python update_html.py
    echo ""
    echo "✨ Done! Your visualization is ready."
    echo ""
    echo "📂 Open index.html in your browser:"
    echo "   open index.html"
    echo ""
    echo "   Or double-click index.html in Finder"
else
    echo "❌ Error: android_versions_report.csv was not generated"
    exit 1
fi

