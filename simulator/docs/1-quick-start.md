# Quick Start Guide

Get the FSM vs Petri net comparison running in under 5 minutes.

## Prerequisites

- Python 3.11+ with `uv` package manager
- Node.js 18+ (for MCP protocol)
- 100MB free disk space

## One-Command Setup

```bash
cd simulator
./setup.sh
```

This installs all dependencies for both navigators and the test harness.

## Run Your First Test

Compare both approaches on 5 test scenarios:

```bash
python test-harness.py workflow-dataset.json -n 5
```

Expected output:
```
================================================================================
WORKFLOW NAVIGATION COMPARISON: FSM vs PETRI NET
================================================================================
...
RESULTS SUMMARY
================================================================================
Total Tool Calls:
  FSM Navigator: 16
  Petri Net Navigator: 6
  Efficiency Gain: 2.7x
```

## What Just Happened?

1. The test harness started both MCP servers
2. It selected 5 random test scenarios from the dataset
3. Each navigator attempted the same tasks
4. FSM required hierarchical navigation (4 calls per task)
5. Petri net used direct access (1-2 calls per task)
6. Results saved to `test-results.json`

## Try Different Tests

```bash
# Run 10 tests with reproducible selection
python test-harness.py workflow-dataset.json -n 10 -s 42

# Test with the chaos dataset (complex workflows)
python test-harness.py workflow-chaos-dataset.json -n 5

# See all available tests in a dataset
python test-harness.py workflow-dataset.json --list-all
```

## Next Steps

- Read [Concepts](2-concepts.md) to understand why Petri nets are more efficient
- Follow the [Testing Guide](4-testing-guide.md) for comprehensive testing
- Review [Architecture](3-architecture.md) to understand the implementation