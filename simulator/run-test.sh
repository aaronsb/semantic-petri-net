#!/bin/bash

echo "=================================="
echo "FSM vs Petri Net Navigation Test"
echo "=================================="
echo ""

# Check for dataset argument
DATASET=${1:-test}

if [[ "$DATASET" == "help" || "$DATASET" == "--help" ]]; then
    echo "Usage: ./run-test.sh [DATASET]"
    echo ""
    echo "Available datasets:"
    echo "  test      - Simple test dataset (default)"
    echo "  standard  - Standard workflow dataset" 
    echo "  chaos     - Chaos dataset with problematic workflows"
    echo ""
    echo "Examples:"
    echo "  ./run-test.sh           # Run test dataset"
    echo "  ./run-test.sh chaos     # Run chaos dataset"
    echo ""
    echo "To test all datasets:"
    echo "  ./run-test.sh test && ./run-test.sh standard && ./run-test.sh chaos"
    exit 0
fi

echo "Testing with $DATASET dataset..."
echo "This compares FSM and Petri net approaches for workflow navigation."

echo ""
echo "Running test harness..."
echo ""

uv run python test-harness.py $DATASET

echo ""
echo "Test complete. See test-results.json for detailed metrics."
echo ""
echo "For research paper inclusion:"
echo "1. Review test-methodology.md for experimental design"
echo "2. Use these results to support architectural claims"
echo "3. The efficiency gains demonstrate Petri net advantages"