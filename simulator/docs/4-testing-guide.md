# Comprehensive Testing Guide

Multiple ways to test and compare FSM vs Petri net navigators.

## Automated Testing with Test Harness

### Basic Usage

```bash
# Run default 5 tests on standard dataset
python test-harness.py workflow-dataset.json

# Run 20 tests with specific seed for reproducibility
python test-harness.py workflow-dataset.json -n 20 -s 42

# List all available tests in a dataset
python test-harness.py workflow-dataset.json --list-all
```

### Dataset Options

1. **Test Dataset** (`workflow-test-dataset.json`)
   - 31 possible tests
   - Simple, clear workflows
   - Good for initial testing

2. **Standard Dataset** (`workflow-dataset.json`)
   - 113 possible tests
   - Realistic enterprise workflows
   - Best for benchmarking

3. **Chaos Dataset** (`workflow-chaos-dataset.json`)
   - 139 possible tests
   - Complex states with special characters
   - Circular references (Canadian politeness loop)
   - Tests edge cases

### Understanding Test Types

The harness generates four types of tests:

1. **Single Transitions**: Move entity from current state to valid next state
2. **Completions**: Move entity to terminal state (Done, Fixed, etc.)
3. **Direct Access**: Test efficiency of bypassing navigation
4. **Reassignments**: Change entity assignment between users

### Interpreting Results

```
Total Tool Calls:
  FSM Navigator: 32      # Total API calls made
  Petri Net Navigator: 10  # Significantly fewer
  Efficiency Gain: 3.2x   # Petri is 3.2x more efficient
```

## Interactive Testing with Claude

### Setup MCP Servers

```bash
# Add both navigators to Claude
claude mcp add fsm-navigator "./fsm-navigator/run-mcp.sh" workflow-dataset.json
claude mcp add petri-navigator "./petri-navigator/run-mcp.sh" workflow-dataset.json

# Restart Claude to load servers
```

### Test Scenarios

#### Scenario 1: Direct State Update
```
FSM: mcp__fsm-navigator__updateTaskState(taskId="task-201", newState="In Progress")
Result: Error - Must be at task location

Petri: mcp__petri-navigator__updateState(entityId="task-201", newState="In Progress") 
Result: Success - Direct transition
```

#### Scenario 2: Complete Workflow
```
FSM: 
1. mcp__fsm-navigator__listProjects()
2. mcp__fsm-navigator__getProject(projectId="project-web")
3. mcp__fsm-navigator__getTask(taskId="task-201")
4. mcp__fsm-navigator__updateTaskState(taskId="task-201", newState="Done")
Total: 4 calls

Petri:
1. mcp__petri-navigator__completeItem(entityId="task-201")
Total: 1 call
```

#### Scenario 3: Bulk Operations
```
Task: Update 5 tasks to "In Progress"

FSM: 20 calls (4 per task)
Petri: 5 calls (1 per task)
```

### Sample Claude Prompts

```
"Compare updating task-201 to 'In Progress' using both navigators"

"Show me how many calls it takes to reassign all tasks from user-alice to user-bob"

"Demonstrate the efficiency difference for completing 10 tasks"
```

## Manual Testing

### Direct MCP Server Testing

```bash
# Start FSM server
cd fsm-navigator
uv run python index.py ../workflow-dataset.json

# In another terminal, send JSON-RPC commands
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | nc localhost 3000
```

### Performance Testing

```bash
# Run increasing test sizes
for n in 5 10 20 50 100; do
    echo "Testing with $n scenarios..."
    python test-harness.py workflow-dataset.json -n $n -s 42
done
```

### Edge Case Testing

```bash
# Test with chaos dataset special characters
python test-harness.py workflow-chaos-dataset.json -n 10

# Look for:
# - Proper handling of "Duck Season!" vs "Duck Season"
# - Canadian politeness circular references
# - States with spaces and special characters
```

## Expected Results by Dataset

### Test Dataset (Simple)
- Efficiency Gain: 3.5-4.0x
- FSM calls per operation: 3-4
- Petri calls per operation: 1

### Standard Dataset (Realistic)
- Efficiency Gain: 2.7-3.5x
- More complex state transitions
- Multiple valid paths

### Chaos Dataset (Edge Cases)
- Efficiency Gain: 2.0-3.0x
- Tests error handling
- Validates special character support

## Troubleshooting

### MCP Servers Won't Start
```bash
# Check Python environment
which uv
uv --version

# Verify dataset path
ls workflow-*.json

# Check for port conflicts
lsof -i :3000
```

### Different Results Than Expected
- Use seed (`-s`) for reproducible tests
- Check dataset hasn't been modified
- Ensure both servers using same dataset

### Test Harness Errors
```bash
# Run with single test to isolate issues
python test-harness.py workflow-dataset.json -n 1

# Check MCP server logs
tail -f ~/.claude/logs/mcp-*.log
```

## Advanced Testing

### Custom Test Selection
```python
# Modify test-harness.py to run specific test types
scenarios = [s for s in all_tests if s['test_type'] == 'reassignment']
```

### Benchmark Mode
```bash
# Run same test 10 times, average results
for i in {1..10}; do
    python test-harness.py workflow-dataset.json -n 50 -s 42
done | grep "Efficiency Gain" | awk '{sum+=$3; count++} END {print sum/count}'
```

### Generate Test Report
```bash
# Run comprehensive test suite
python test-harness.py workflow-dataset.json -n 100 > report.txt
python test-harness.py workflow-test-dataset.json -n 30 >> report.txt
python test-harness.py workflow-chaos-dataset.json -n 50 >> report.txt
```