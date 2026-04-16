#!/usr/bin/env bash
# Render Build Script for Sports Diary Backend

set -o errexit

echo "🔧 Starting build process..."

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies with no cache and prefer binary wheels
echo "📦 Installing dependencies..."
pip install --no-cache-dir --prefer-binary -r requirements.txt

echo "✅ Build completed successfully!"

