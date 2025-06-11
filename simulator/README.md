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
# Run the setup script (installs uv if needed)
./setup.sh

# Or manually:
cd fsm-navigator && npm install
cd ../petri-navigator && uv pip install -r requirements.txt
```

2. Add to Claude using the CLI:

```bash
# Add FSM Navigator
claude mcp add fsm-navigator node /home/aaron/Projects/ai/mcp/semantic-petri-net/simulator/fsm-navigator/index.js

# Add Petri Net Navigator  
claude mcp add petri-navigator uv run python /home/aaron/Projects/ai/mcp/semantic-petri-net/simulator/petri-navigator/index.py
```

Or if you're in the simulator directory:
```bash
claude mcp add fsm-navigator node ./fsm-navigator/index.js
claude mcp add petri-navigator uv run python ./petri-navigator/index.py
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

## Testing Architecture

We provide two complementary testing approaches to validate the FSM vs Petri net architectural differences:

### 1. Static Baseline Tests (`test-harness.py`)

The test harness connects directly to both MCP servers using the MCP protocol and runs controlled tests to measure baseline performance. This provides consistent, repeatable measurements of the architectural differences.

**Features:**
- Direct MCP protocol communication with both servers
- Controlled goal execution in isolated environments
- Precise measurement of tool calls, timing, and success rates
- Semantic hint usage tracking
- Error detection and analysis

**Running:**
```bash
# Run the complete comparison using real MCP servers
uv run python test-harness.py

# Or use the convenience script
./run-test.sh
```

### 2. Real Agent Iteration Tests (Future)

Future tests will use actual AI agents (like Claude Code) interacting with the MCP servers in realistic scenarios. This will provide more naturalistic performance data showing how real agents benefit from the different architectural approaches.

### Test Results

Both test types save results to `test-results.json` with:
- Tool call counts for each approach
- Goal completion rates and success patterns
- Average efficiency metrics per goal type
- Detailed execution paths taken
- Timing data and semantic hint usage

### Sample Static Test Output

```
WORKFLOW NAVIGATION COMPARISON: FSM vs PETRI NET
Using Real MCP Server Calls
===============================================

Starting MCP servers...
✓ Both MCP servers started successfully

Goal: Ship Authentication Feature
  FSM: ✓ (8 calls, 0.24s)
  Petri Net: ✓ (2 calls, 0.12s)
  Efficiency gain: 4.0x

Goal: Start Task in Under 3 Calls
  FSM: ✗ (6 calls, 0.18s)  # Fails due to navigation overhead
  Petri Net: ✓ (1 calls, 0.06s)
  Efficiency gain: 6.0x

RESULTS SUMMARY
===============
Total Tool Calls:
  FSM Navigator: 34
  Petri Net Navigator: 7
  Efficiency Gain: 4.9x

Goals Completed:
  FSM Navigator: 4/5  # Some goals impossible due to FSM constraints
  Petri Net Navigator: 5/5
```

### Key Differences Demonstrated

1. **FSM Navigator**: Requires hierarchical navigation (root → projects → project → tasks → task) for every operation
2. **Petri Navigator**: Provides direct multi-entry access with semantic operations that bypass navigation
3. **Performance**: Petri net approach shows 4-6x efficiency gain in tool calls
4. **Capabilities**: Some goals impossible for FSM due to navigation overhead
5. **Semantic Hints**: Petri navigator provides contextual guidance, FSM provides only procedural steps

### Test Documentation
- `test-methodology.md` - Experimental design and hypotheses
- `test-harness-explanation.md` - How the MCP-based testing works
- `claude-testing-guide.md` - Instructions for live testing with Claude

## Research Value

This comparison demonstrates:
1. Why FSM-based AI agents struggle with enterprise workflows
2. How semantic hints reduce navigation complexity
3. The value of multi-entry architectures
4. Why Petri net patterns better match real work

The dramatic difference in tool calls (6:1 ratio for simple tasks) provides concrete evidence for the paper's thesis.