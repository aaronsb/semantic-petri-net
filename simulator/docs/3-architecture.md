# Technical Architecture

How the FSM and Petri net navigators are implemented.

## Overview

Both navigators implement the MCP (Model Context Protocol) server specification, exposing tools that AI agents can call. They use identical datasets but implement fundamentally different navigation paradigms.

## MCP Server Architecture

```
AI Agent (Claude, etc.)
    ↓ JSON-RPC
MCP Server (FSM or Petri)
    ↓ Process Dataset
Navigation Logic
    ↓ Return Results
AI Agent
```

## FSM Navigator Implementation

### Core Data Structure
```python
class FSMNavigator:
    def __init__(self):
        self.current_location = "root"  # Single location tracking
        self.location_stack = []        # Navigation history
```

### Navigation State
The FSM tracks location hierarchically:
- `root` → Top level
- `project:project-123` → Inside a project
- `task:task-456` → At a specific task

### Required Navigation Flow
```python
# To update a task, must navigate to it first
def updateTaskState(task_id, new_state):
    if self.current_location != f"task:{task_id}":
        raise Error("Must be at task location. Use getTask first.")
    # Update only if at correct location
```

### Tools Exposed
1. `listProjects()` - Navigate to project list
2. `getProject(id)` - Enter specific project
3. `listTasks(project_id)` - List tasks in current project
4. `getTask(id)` - Navigate to specific task
5. `updateTaskState(id, state)` - Update (requires location)
6. `navigateToRoot()` - Return to top level

## Petri Net Navigator Implementation

### Core Data Structure
```python
class WorkflowPetriNet:
    def __init__(self):
        self.net = PetriNet('workflow')  # SNAKES Petri net
        self.tokens = {}                 # Entity ID → Current place
        self._build_net()                # Create places & transitions
```

### Token-Based State
```python
# Each entity has a token in its current state place
tokens = {
    "task-123": "task-123_Open",
    "task-456": "task-456_In_Progress", 
    "bug-789": "bug-789_Fixed"
}
```

### Place Name Sanitization
Special characters in state names are handled:
```python
def _get_place_name(self, name: str) -> str:
    # "Duck Season!" → "Duck_Season_EXCL"
    # "Going Up While Going Down" → "Going_Up_While_Going_Down"
```

### Direct State Transitions
```python
def updateState(entity_id, new_state):
    # No location check needed - direct transition
    current_place = self.tokens[entity_id]
    target_place = f"{entity_id}_{new_state}"
    # Fire transition moving token
```

### Semantic Operations
```python
def completeItem(entity_id):
    # Find terminal state for entity type
    terminal_states = self._find_terminal_states(entity_id)
    # Create multi-hop transition to completion
```

### Tools Exposed
1. `listWorkflow()` - Show all entities and states
2. `updateState(id, state)` - Direct state update
3. `startWorkingOn(id)` - Semantic: move to active state
4. `completeItem(id)` - Semantic: move to terminal state
5. `reassignItem(id, from, to)` - Direct reassignment
6. `advanceWorkflow([ids])` - Concurrent updates

## Test Harness Architecture

### Test Enumeration
```python
def enumerate_all_tests(dataset):
    tests = []
    # 1. Single state transitions
    for task in tasks:
        for from_state, to_states in transitions:
            tests.append(SingleTransition(...))
    
    # 2. Completion workflows  
    for task in tasks:
        if has_terminal_state(task):
            tests.append(CompletionTest(...))
    
    # 3. Efficiency tests
    tests.append(DirectAccessTest(...))
    
    # 4. Reassignments
    for user_from, user_to in user_pairs:
        tests.append(ReassignmentTest(...))
```

### Seeded Selection
```python
def select_tests(all_tests, num_tests, seed):
    random.seed(seed)  # Reproducible
    return random.sample(all_tests, num_tests)
```

### MCP Communication
```python
class MCPClient:
    async def call_tool(self, tool_name, arguments):
        message = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        # Send via stdin, receive via stdout
```

## Dataset Structure

All three datasets follow this schema:
```json
{
  "entities": {
    "projects": { "id": {...} },
    "tasks": {
      "task-123": {
        "id": "task-123",
        "name": "Implement Feature",
        "state": "Open",
        "validTransitions": {
          "Open": ["In Progress", "Blocked"],
          "In Progress": ["Review", "Open"],
          "Review": ["Done", "In Progress"]
        }
      }
    },
    "bugs": { "id": {...} },
    "users": { "id": {...} }
  }
}
```

## Performance Characteristics

### FSM Navigator
- **Time Complexity**: O(depth) for each operation
- **Space Complexity**: O(1) - single location
- **Calls per Operation**: 3-4 (navigation + action)

### Petri Net Navigator  
- **Time Complexity**: O(1) for direct operations
- **Space Complexity**: O(entities) - token per entity
- **Calls per Operation**: 1-2 (usually just action)

## Key Implementation Insights

1. **Place Creation**: Must handle special characters in state names
2. **Token Management**: Track current position for each entity
3. **Transition Firing**: Validate transitions before moving tokens
4. **Semantic Shortcuts**: Implement high-level operations that span multiple states
5. **Concurrent Operations**: Petri nets naturally support parallel transitions