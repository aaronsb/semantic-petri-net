# Semantic Petri Net Pattern Discovery

This repository documents the discovery of Petri net patterns while building the Targetprocess MCP Server, and demonstrates why traditional AI agents struggle with enterprise workflows.

## Overview

While building a Model Context Protocol (MCP) server for Targetprocess, we discovered that semantic hints and multi-entry workflows naturally align with Petri net theory. This explains why FSM-based AI agents fail at complex workflows - they're using the wrong computational model.

## Repository Contents

### 📄 Research Paper
- [`paper.md`](paper.md) - Main research paper documenting our journey from API wrapper to Petri net patterns

### 🧪 Workflow Navigator Simulators
- [`simulator/`](simulator/) - Comparison of FSM vs Petri net navigation approaches
  - [`simulator/README.md`](simulator/README.md) - Overview of the simulators
  - [`simulator/test-methodology.md`](simulator/test-methodology.md) - Experimental design and hypotheses
  - [`simulator/test-harness-explanation.md`](simulator/test-harness-explanation.md) - How the test simulation works
  - [`simulator/claude-testing-guide.md`](simulator/claude-testing-guide.md) - Guide for testing with Claude

### 📊 Test Results
- [`simulator/test-results.json`](simulator/test-results.json) - Performance comparison data showing 6.75x efficiency gain

### 🔧 Implementation
- [`simulator/fsm-navigator/`](simulator/fsm-navigator/) - Traditional FSM approach (JavaScript)
- [`simulator/petri-navigator/`](simulator/petri-navigator/) - Petri net approach with SNAKES (Python)

## Key Findings

1. **Semantic hints pattern** reduces navigation complexity by 80-90%
2. **Multi-entry workflows** eliminate hierarchical navigation overhead
3. **Petri net patterns** naturally emerge when building workflow tools
4. **FSM limitations** are architectural, not implementation-specific

## Quick Start

To run the comparison test:

```bash
cd simulator
./setup.sh        # Install dependencies
./run-test.sh     # Run performance comparison
```

## Development Guidelines

See [`CLAUDE.md`](CLAUDE.md) for project-specific instructions on maintaining research integrity and grounding claims in actual implementation experience.

## License

MIT License - see [`LICENSE`](LICENSE) for details.