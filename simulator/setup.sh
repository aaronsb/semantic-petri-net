#!/bin/bash

echo "Setting up FSM and Petri Net Navigator MCP Servers..."

# Install FSM Navigator
echo "Installing FSM Navigator (JavaScript)..."
cd fsm-navigator
npm install
cd ..

# Install Petri Net Navigator with SNAKES
echo "Installing Petri Net Navigator (Python/SNAKES)..."
cd petri-navigator
pip install -r requirements.txt
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To add these servers to Claude, run:"
echo ""
echo "claude mcp add fsm-navigator node $(pwd)/fsm-navigator/index.js"
echo "claude mcp add petri-navigator python $(pwd)/petri-navigator/index.py"
echo ""
echo "Then restart Claude to use the servers."