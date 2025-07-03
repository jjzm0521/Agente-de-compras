#!/bin/bash

# Define the name of the virtual environment directory
VENV_DIR=".venv"

# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv $VENV_DIR
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment. Make sure Python 3 and venv are installed."
    exit 1
  fi
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
  echo "Error: Failed to install dependencies."
  # Deactivate virtual environment in case of error during installation
  deactivate
  exit 1
fi

echo "Setup complete. Virtual environment '$VENV_DIR' is ready and dependencies are installed."
echo "To activate the virtual environment in your current shell, run: source $VENV_DIR/bin/activate"
