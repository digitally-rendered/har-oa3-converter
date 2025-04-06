#!/bin/bash

set -e

echo "=== Setting up Rancher Desktop on macOS ==="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH if needed
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

# Update Homebrew
echo "Updating Homebrew..."
brew update

# Install Rancher Desktop via Homebrew Cask
echo "Installing Rancher Desktop..."
brew install --cask rancher

# Wait for Rancher to initialize
echo "Waiting for Rancher Desktop to initialize (this may take a minute)..."

# Check if Rancher Desktop is installed
if ! [ -d "/Applications/Rancher Desktop.app" ]; then
    echo "Error: Rancher Desktop installation failed."
    exit 1
fi

echo "Rancher Desktop installed successfully."

# Open Rancher Desktop
echo "Opening Rancher Desktop. Please complete the setup process in the UI."
open -a "Rancher Desktop"

echo ""
echo "=== Rancher Desktop Setup Instructions ==="
echo "1. In the Rancher Desktop UI, select 'dockerd' as the container runtime."
echo "2. Set your preferred Kubernetes version or disable Kubernetes if not needed."
echo "3. Click 'Accept' to complete the setup."
echo "4. Wait for the initialization process to complete."
echo ""

# Wait for user to confirm setup is complete
read -p "Press Enter after completing the Rancher Desktop setup in the UI..."

# Check if docker command is available
while ! command -v docker &> /dev/null; do
    echo "Waiting for docker command to become available..."
    sleep 5
done

# Test Docker connectivity
echo "Testing Docker connectivity..."
if docker info &>/dev/null; then
    echo "✅ Docker is running correctly!"
else
    echo "❌ Docker is not running. Please check Rancher Desktop status."
    exit 1
fi

# Create test container to verify everything works
echo "Running a test container..."
docker run --rm hello-world

echo ""
echo "=== Rancher Desktop Setup Complete ==="
echo "You can now run Docker containers and use the har-oa3-converter Docker tests."
echo ""
echo "To run the Docker tests for har-oa3-converter:"
echo "  cd $(pwd)"
echo "  ./scripts/run_tests_in_docker.sh"
echo ""
echo "To verify the Docker daemon status anytime, run:"
echo "  docker info"
echo ""
echo "Rancher Desktop can be managed through its UI application in your Applications folder."
