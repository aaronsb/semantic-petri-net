# Testing Guide: Using Claude to Compare FSM vs Petri Net Navigators

## Overview

This guide explains how to use Claude to test the FSM and Petri Net navigators, demonstrating the real-world performance differences between these approaches.

## Setup

1. **Install the MCP servers**:
   ```bash
   cd simulator
   ./setup.sh
   ```

2. **Add servers to Claude**:
   ```bash
   claude mcp add fsm-navigator node ./fsm-navigator/index.js
   claude mcp add petri-navigator python ./petri-navigator/index.py
   ```

3. **Restart Claude** to load the servers

## Test Scenarios

### Test 1: Ship Authentication Feature

**FSM Approach** (use fsm-navigator tools):
```
Goal: Move task-auth from Open to Done state

Expected sequence:
1. listProjects()
2. getProject('project-web')
3. listTasks('project-web') 
4. getTask('task-auth')
5. getTaskState('task-auth')
6. assignTask('task-auth', 'user-alice')
7. updateTaskState('task-auth', 'In Progress')
8. updateTaskState('task-auth', 'Review')
9. updateTaskState('task-auth', 'Testing')
10. updateTaskState('task-auth', 'Done')

Total: 10 tool calls
```

**Petri Net Approach** (use petri-navigator tools):
```
Goal: Move task-auth from Open to Done state

Expected sequence:
1. startWorkingOn('task-auth')
2. completeTask('task-auth')

Total: 2 tool calls
```

### Test 2: Efficiency Challenge

**FSM Approach**:
```
Goal: Start any open task in less than 3 tool calls

Expected: FAILURE (requires minimum 6-8 calls)
```

**Petri Net Approach**:
```
Goal: Start any open task in less than 3 tool calls

Expected sequence:
1. startWorkingOn('any open task')

Total: 1 tool call - SUCCESS
```

### Test 3: Concurrent Operations

**FSM Approach**:
```
Goal: Advance 2 different items within 10 tool calls

Expected: FAILURE (requires ~12 calls due to navigation overhead)
```

**Petri Net Approach**:
```
Goal: Advance 2 different items within 10 tool calls

Expected sequence:
1. advanceWorkflow(['task-ui', 'bug-performance'])

Total: 1 tool call - SUCCESS
```

## What to Observe

1. **Navigation Overhead**: FSM requires returning to root and navigating hierarchies
2. **Semantic Hints**: Petri net provides guidance on next steps
3. **Multi-Entry**: Petri net can access any entity directly
4. **Formal Model**: Petri net can visualize its structure and analyze reachability

## Sample Claude Prompts

### For FSM Navigator:
```
Using the fsm-navigator tools, please:
1. List all projects
2. Navigate to the Web Application project
3. Find the authentication task
4. Move it from Open to Done state
Count how many tool calls this takes.
```

### For Petri Net Navigator:
```
Using the petri-navigator tools, please:
1. Start working on the authentication task
2. Complete it
Count how many tool calls this takes.
```

### For Comparison:
```
Please complete the goal "Ship Authentication Feature" using:
1. First, the fsm-navigator tools (count the calls)
2. Then, the petri-navigator tools (count the calls)
Compare the efficiency and explain why there's a difference.
```

## Expected Insights

After testing, Claude should observe:

1. **Quantitative Difference**: 6-8x fewer tool calls with Petri net
2. **Qualitative Difference**: More intuitive, less cognitive load
3. **Architectural Insight**: FSM forces unnecessary structure on fluid workflows
4. **Semantic Value**: Hints guide users without requiring workflow memorization

## Recording Results

Ask Claude to:
1. Track exact tool calls for each approach
2. Note any failures or difficulties
3. Compare the user experience
4. Explain why the Petri net approach is more efficient

This real-world testing with Claude as the agent provides empirical validation of the theoretical advantages documented in the research paper.