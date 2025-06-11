#!/bin/bash

echo "=================================="
echo "FSM vs Petri Net Navigation Test"
echo "=================================="
echo ""
echo "This test compares the efficiency of FSM and Petri net approaches"
echo "for navigating enterprise workflows."
echo ""
echo "Running test harness..."
echo ""

python3 test-harness.py

echo ""
echo "Test complete. See test-results.json for detailed metrics."
echo ""
echo "To include in the research paper:"
echo "1. Review test-methodology.md for the experimental design"
echo "2. Run this test to generate test-results.json"
echo "3. Add both as appendices to the paper"