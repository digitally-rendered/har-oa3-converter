#!/bin/bash
# Script to set up pyenv after installing it with Homebrew

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error

echo "Setting up pyenv environment..."

# Ensure pyenv is installed
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew is not installed. Please install Homebrew first."
    exit 1
fi

# Install pyenv if not already installed
if ! brew list pyenv &> /dev/null; then
    echo "Installing pyenv via Homebrew..."
    brew install pyenv
else
    echo "pyenv is already installed, updating..."
    brew upgrade pyenv
fi

# Install pyenv-virtualenv for managing virtualenvs (optional)
if ! brew list pyenv-virtualenv &> /dev/null; then
    echo "Installing pyenv-virtualenv..."
    brew install pyenv-virtualenv
else
    echo "pyenv-virtualenv is already installed, updating..."
    brew upgrade pyenv-virtualenv
fi

# Check which shell is being used
SHELL_NAME=$(basename "$SHELL")
SHELL_CONFIG_FILE=".zshrc"

case "$SHELL_NAME" in
    "bash")
        SHELL_CONFIG_FILE="$HOME/.bashrc"
        # Also check for .bash_profile
        if [ -f "$HOME/.bash_profile" ]; then
            SHELL_CONFIG_FILE="$HOME/.bash_profile"
        fi
        ;;
    "zsh")
        SHELL_CONFIG_FILE="$HOME/.zshrc"
        ;;
    *)
        echo "Warning: Unsupported shell ($SHELL_NAME). You'll need to manually configure your shell for pyenv."
        ;;
esac

# Add pyenv to shell configuration if needed
if [ -n "$SHELL_CONFIG_FILE" ]; then
    echo "Configuring pyenv in $SHELL_CONFIG_FILE..."
    
    # Check if pyenv config already exists
    if ! grep -q "pyenv init" "$SHELL_CONFIG_FILE"; then
        echo "Adding pyenv initialization to $SHELL_CONFIG_FILE..."
        
        cat >> "$SHELL_CONFIG_FILE" << 'EOF'

# pyenv setup
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOF
        
        echo "Shell configuration updated. You'll need to restart your shell or run:"
        echo "  source $SHELL_CONFIG_FILE"
    else
        echo "pyenv configuration already exists in $SHELL_CONFIG_FILE"
    fi
else
    echo "No shell configuration file found. You'll need to manually add pyenv to your shell configuration."
fi

# Source the shell configuration to use pyenv in the current session
if [ -n "$SHELL_CONFIG_FILE" ]; then
    echo "Activating pyenv in current shell..."
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)" || true
fi

# Install Python versions
echo "Which Python versions would you like to install? (space-separated list, e.g., 3.9.16 3.10.11 3.11.5)"
read -r -p "Python versions (leave empty to skip): " PYTHON_VERSIONS

if [ -n "$PYTHON_VERSIONS" ]; then
    for version in $PYTHON_VERSIONS; do
        echo "Installing Python $version..."
        pyenv install "$version" || echo "Failed to install Python $version"
    done
    
    # Set the first version as global
    FIRST_VERSION=$(echo "$PYTHON_VERSIONS" | awk '{print $1}')
    echo "Setting Python $FIRST_VERSION as global default..."
    pyenv global "$FIRST_VERSION"
    
    echo "Python $FIRST_VERSION is now your default Python version."
fi

# Verify installation
echo "Verifying pyenv installation..."
pyenv --version
python --version

echo "pyenv setup complete! You're ready to manage Python versions."
echo "Some helpful commands:"
echo "  - List available Python versions: pyenv install --list"
echo "  - Install a Python version: pyenv install 3.x.y"
echo "  - Set global Python version: pyenv global 3.x.y"
echo "  - Create a virtualenv: pyenv virtualenv 3.x.y myproject"
echo "  - Set local Python version: pyenv local 3.x.y"
