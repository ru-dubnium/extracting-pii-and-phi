#!/bin/bash
# setup.sh - System and Python dependency setup for PII/PHI Extractor

set -e

echo "=== Setting up PII/PHI Extraction System ==="

# 1. Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# 2. Check and install Tesseract OCR
if command -v tesseract >/dev/null 2>&1; then
    echo "✓ Tesseract-OCR is already installed: $(tesseract --version | head -n 1)"
else
    echo "Tesseract-OCR not found. Attempting to install via apt..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y tesseract-ocr
        echo "✓ Tesseract-OCR installed successfully."
    else
        echo "WARNING: apt-get not found. Please install tesseract-ocr manually using your package manager (e.g., yum, brew, pacman)."
    fi
fi

# 3. Check and install Ollama
if command -v ollama >/dev/null 2>&1; then
    echo "✓ Ollama is already installed: $(ollama --version)"
else
    echo "Ollama not found. Attempting to install via official script..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "✓ Ollama installed successfully."
fi

# 4. Pull the default Ollama model (llama3.2:3b is standard, we'll pull it)
# We won't block the setup if pulling fails or Ollama daemon is not running.
echo "Attempting to pull model 'llama3.2' (approx 2GB)..."
if command -v ollama >/dev/null 2>&1; then
    # Start ollama server in the background if not running
    if ! pgrep -x "ollama" >/dev/null; then
        echo "Starting Ollama service in the background..."
        ollama serve > /dev/null 2>&1 &
        sleep 3
    fi
    ollama pull llama3.2 || echo "WARNING: Failed to pull llama3.2 model. Make sure Ollama service is running and retry: 'ollama pull llama3.2'"
else
    echo "WARNING: Ollama not installed, skipping model pull."
fi

echo "=== Setup Complete ==="
