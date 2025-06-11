#!/bin/bash

echo "Setting up FSM and Petri Net Navigator MCP Servers..."

# Install FSM Navigator
echo "Installing FSM Navigator..."
cd fsm-navigator
npm install
cd ..

# Install Petri Net Navigator  
echo "Installing Petri Net Navigator..."
cd petri-navigator
npm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To add these servers to Claude, run:"
echo ""
echo "claude mcp add fsm-navigator node $(pwd)/fsm-navigator/index.js"
echo "claude mcp add petri-navigator node $(pwd)/petri-navigator/index.js"
echo ""
echo "Then restart Claude to use the servers."