# Workflow Navigator Simulators

This directory contains two MCP servers that demonstrate the difference between FSM and Petri net approaches to workflow navigation.

## FSM Navigator (`fsm-navigator/`)

Traditional finite state machine approach that requires navigating through a strict hierarchy:
- Must start with `listProjects()`
- Navigate through project → tasks → specific task
- Each step requires the previous context
- Single state tracking
- No formal verification possible

### Example FSM Flow:
```
listProjects() → getProject('project-web') → listTasks('project-web') → 
getTask('task-auth') → assignTask('task-auth', 'user-alice') → 
updateTaskState('task-auth', 'In Progress')
```
**Total: 6 tool calls to start working on a task**

## Petri Net Navigator (`petri-navigator/`)

Formal Petri net implementation using SNAKES library:
- **Formal mathematical model** of workflow states and transitions
- Multi-entry approach with semantic hints
- **Reachability analysis** to verify workflow properties
- **Visual generation** of the Petri net structure
- Concurrent token tracking for parallel workflows
- Semantic operations handle multiple steps atomically

### Example Petri Net Flow:
```
startWorkingOn('task-auth')
```
**Total: 1 tool call to achieve the same result**

### Formal Verification Features:
- `analyzeReachability()` - Prove what states can be reached
- `visualizePetriNet()` - Generate graphical representation
- `getWorkflowState()` - Show current Petri net configuration
- Deadlock detection (via SNAKES analysis)
- Liveness verification (all goals reachable)

## Setup Instructions

1. Install dependencies:
```bash
# Run the setup script
./setup.sh

# Or manually:
cd fsm-navigator && npm install
cd ../petri-navigator && pip install -r requirements.txt
```

2. Add to Claude using the CLI:

```bash
# Add FSM Navigator
claude mcp add fsm-navigator node /home/aaron/Projects/ai/mcp/semantic-petri-net/simulator/fsm-navigator/index.js

# Add Petri Net Navigator  
claude mcp add petri-navigator python /home/aaron/Projects/ai/mcp/semantic-petri-net/simulator/petri-navigator/index.py
```

Or if you're in the simulator directory:
```bash
claude mcp add fsm-navigator node ./fsm-navigator/index.js
claude mcp add petri-navigator python ./petri-navigator/index.py
```

## Testing Goals

The workflow dataset includes 8 goals worth 100 points each:
1. Ship Authentication Feature
2. Fix Critical Bug
3. Complete Code Review
4. Ready for Deployment
5. Performance Issue Resolved
6. Start Any Task Efficiently
7. Reassign Work Item
8. Advance Multiple Items

## Metrics to Compare

Use these commands in Claude to compare approaches:
- `checkGoals()` - See which goals have been achieved
- `getMetrics()` - See efficiency metrics

### Key Metrics:
- **Tool calls per goal** - How many operations to reach each goal
- **Semantic hint usage** - How often the AI follows suggestions
- **Time to first goal** - How quickly meaningful work gets done
- **Cognitive load** - How much context the user needs to remember

## Expected Results

**FSM Navigator:**
- High tool call count (5-10 per goal)
- Must maintain mental model of hierarchy
- Difficult to work on multiple items
- No guidance on next steps

**Petri Net Navigator:**
- Low tool call count (1-3 per goal)
- Direct access to any workflow item
- Natural concurrent operations
- Semantic hints guide the process

## Testing and Validation

### Automated Test Harness
Run the simulation to see predicted performance:
```bash
./run-test.sh
```

This generates `test-results.json` with detailed metrics showing ~6.75x efficiency gain.

### Test Documentation
- `test-methodology.md` - Experimental design and hypotheses
- `test-harness-explanation.md` - How the simulation works
- `claude-testing-guide.md` - Instructions for live testing with Claude

### Key Results
- **FSM Navigator**: 81 total calls, 6/8 goals completed
- **Petri Net Navigator**: 12 total calls, 8/8 goals completed
- **Efficiency Gain**: 6.75x fewer calls with Petri nets
- **Semantic Hints**: Critical for achieving efficiency

## Research Value

This comparison demonstrates:
1. Why FSM-based AI agents struggle with enterprise workflows
2. How semantic hints reduce navigation complexity
3. The value of multi-entry architectures
4. Why Petri net patterns better match real work

The dramatic difference in tool calls (6:1 ratio for simple tasks) provides concrete evidence for the paper's thesis.