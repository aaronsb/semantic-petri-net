#!/bin/bash

echo "Setting up FSM and Petri Net Navigator MCP Servers..."
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed."
    echo ""
    echo "Please install uv first using one of these methods:"
    echo ""
    echo "  # Using the installer script:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "  # Or using your system's package manager:"
    echo "  brew install uv          # macOS"
    echo "  sudo apt install uv      # Ubuntu/Debian"
    echo "  pipx install uv          # Using pipx"
    echo ""
    echo "For more options visit: https://github.com/astral-sh/uv"
    echo ""
    echo "Then run this setup script again."
    exit 1
fi

# Install FSM Navigator
echo "📦 Installing FSM Navigator (JavaScript)..."
cd fsm-navigator
npm install
cd ..
echo "✅ FSM Navigator ready"

# Install Petri Net Navigator with uv
echo "📦 Installing Petri Net Navigator (Python/SNAKES)..."
cd petri-navigator
uv pip install -r requirements.txt
cd ..
echo "✅ Petri Net Navigator ready"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To add these servers to Claude, run:"
echo ""
echo "claude mcp add fsm-navigator node $(pwd)/fsm-navigator/index.js"
echo "claude mcp add petri-navigator uv run python $(pwd)/petri-navigator/index.py"
echo ""
echo "Then restart Claude to use the servers."