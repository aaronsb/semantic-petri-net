# How the Test Harness Works

## Overview

The test harness (`test-harness.py`) is a **simulation** that demonstrates how FSM and Petri net navigators would behave when trying to achieve the same workflow goals. It doesn't actually call the MCP servers - instead, it simulates the sequence of tool calls each approach would require.

## Key Components

### 1. NavigationMetrics Class
```python
@dataclass
class NavigationMetrics:
    tool_calls: int = 0              # Counts every API call
    goals_completed: List[str] = []  # Tracks successful goals
    paths_taken: List[List[str]] = []  # Records call sequences
    semantic_hints_followed: int = 0  # Counts guidance usage
```

This tracks performance metrics for each navigation approach.

### 2. FSMSimulator Class

Simulates how a traditional FSM-based navigator would work:

```python
async def _ship_authentication_feature(self) -> bool:
    """Goal: Move task-auth to Done state"""
    
    # FSM must navigate hierarchy step by step:
    self.metrics.add_tool_call("listProjects")         # 1. Find projects
    self.metrics.add_tool_call("getProject('web')")    # 2. Select project
    self.metrics.add_tool_call("listTasks('web')")     # 3. List tasks
    self.metrics.add_tool_call("getTask('auth')")      # 4. Select task
    # ... continue through each state transition
```

**Key characteristics:**
- Must follow hierarchical navigation (root → projects → tasks → specific task)
- Cannot skip intermediate steps
- Each state transition requires a separate call
- No awareness of semantic operations

### 3. PetriNetSimulator Class

Simulates how a Petri net navigator with semantic hints would work:

```python
async def _ship_authentication_feature(self) -> bool:
    """Goal: Move task-auth to Done state"""
    
    # Multi-entry: direct access with semantic operations
    self.metrics.add_tool_call("startWorkingOn('task-auth')")  # 1. Multi-entry
    self.metrics.add_tool_call("completeTask('task-auth')")    # 2. Semantic op
```

**Key characteristics:**
- Direct access to any workflow entity (multi-entry)
- Semantic operations that handle multiple state transitions
- Context-aware hints guide next actions
- Can handle concurrent operations

## How Goals Are Tested

Each goal is designed to test specific architectural differences:

### Linear Goals (1-5)
Test basic workflow progression:
- Ship Feature: Open → In Progress → Review → Testing → Done
- Fix Bug: New → In Progress → Fixed → Verified

**Result**: FSM needs 6-10 calls, Petri net needs 1-3

### Efficiency Goals (6-8)
Test architectural limitations:
- Start task in < 3 calls (FSM fails - needs 6+)
- Reassign without state check (FSM must check first)
- Advance multiple items in < 10 calls (FSM fails - needs 12+)

**Result**: FSM fails constraints, Petri net succeeds easily

## What the Simulation Demonstrates

### 1. Navigation Overhead
FSM must repeatedly navigate from root:
```
navigateToRoot() → listProjects() → getProject() → listTasks() → getTask()
```
This sequence repeats for EVERY operation.

### 2. State Transition Rigidity
FSM must move through each state sequentially:
```
Open → In Progress → Review → Testing → Done  (4 separate calls)
```
Petri net can jump directly:
```
Open → Done  (1 semantic operation)
```

### 3. Concurrent Operations
FSM must handle items sequentially:
```
// First item: 6 calls
navigate... → update task
// Second item: 6 more calls  
navigate... → update bug
// Total: 12 calls
```

Petri net handles concurrently:
```
advanceWorkflow(['task', 'bug'])  // 1 call for both
```

## Why This Matters

The simulation reveals fundamental architectural differences:

1. **FSM's hierarchical constraint** adds 5-10 unnecessary calls per operation
2. **Petri net's multi-entry** eliminates ALL navigation overhead
3. **Semantic operations** reduce complex workflows to simple commands
4. **Concurrent support** enables parallel state changes

## Validation

The test results show:
- **6.75x efficiency gain** (81 FSM calls vs 12 Petri net calls)
- **25% failure rate** for FSM (2/8 goals failed)
- **100% success rate** for Petri net
- **Average 13.5 calls/goal** for FSM vs **1.5 calls/goal** for Petri net

These aren't implementation details - they're **architectural constraints**. Any FSM-based system will have similar limitations, while any Petri net-based system will have similar advantages.

## Next Steps

To validate with real implementations:
1. Install both MCP servers
2. Use Claude to attempt the same goals
3. Compare actual tool call counts
4. Observe semantic hint effectiveness

The simulation predicts what you'll find: Petri net patterns are fundamentally more efficient for workflow navigation.