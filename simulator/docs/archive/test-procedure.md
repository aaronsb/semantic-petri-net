# Test Procedure: FSM vs Petri Net Navigation Comparison

## Prerequisites

1. **Environment Setup**:
   ```bash
   cd /home/aaron/Projects/ai/mcp/semantic-petri-net/simulator
   ./setup.sh  # Install dependencies with uv
   ```

2. **Verify MCP Servers**:
   ```bash
   # Test FSM navigator
   ./fsm-navigator/run-mcp.sh workflow-dataset.json
   # Should show: "FSM Navigator loaded with workflow-dataset dataset"
   # Press Ctrl+C to stop
   
   # Test Petri navigator  
   ./petri-navigator/run-mcp.sh workflow-dataset.json
   # Should show: "Petri Net Navigator loaded with workflow-dataset dataset"
   # Press Ctrl+C to stop
   ```

## Test Execution

### Step 1: Run Automated Test Harness

Choose one dataset and run the comparison:

```bash
# Standard dataset (recommended)
python test-harness.py workflow-dataset.json

# Or test dataset (simpler)
python test-harness.py workflow-test-dataset.json

# Or chaos dataset (complex with semantic traps)
python test-harness.py workflow-chaos-dataset.json
```

### Step 2: Interpret Results

Look for these key metrics in the output:

**Efficiency Gains**:
- FSM Navigator: 16 total calls
- Petri Net Navigator: 6 total calls  
- **Efficiency Gain: 2.7x** ← Key finding

**Success Patterns**:
- FSM: 4/5 scenarios successful (fails on quick access)
- Petri: 5/5 scenarios successful
- **Quick Access scenario**: FSM fails, Petri succeeds ← Architectural advantage

**Call Patterns** (from test-results.json):
```json
"fsm": [["listProjects", "getProject", "getTask", "updateTaskState"]]  // 4 calls
"petri": [["completeItem"]]  // 1 call
```

### Step 3: Interactive Testing with Claude Code

1. **Configure MCP Servers**:
   ```bash
   claude mcp add fsm-navigator "./fsm-navigator/run-mcp.sh" workflow-dataset.json
   claude mcp add petri-navigator "./petri-navigator/run-mcp.sh" workflow-dataset.json
   ```

2. **Restart Claude Code** and verify both servers appear

3. **Test FSM Hierarchical Navigation**:
   - Try: `mcp__fsm-navigator__updateTaskState(taskId="task-201", newState="In Progress")`
   - Should get: "FSM Error: Must be at task location. Use getTask first."
   - Then: `mcp__fsm-navigator__getTask(taskId="task-201")`
   - Then: `mcp__fsm-navigator__updateTaskState(taskId="task-201", newState="In Progress")`
   - Should succeed

4. **Test Petri Multi-Entry Access**:
   - Try: `mcp__petri-navigator__updateState(entityId="task-201", newState="In Progress")`
   - Should succeed immediately (no navigation required)

## Expected Outcomes

**Quantitative Results**:
- Petri net achieves 2.5-4x efficiency gain
- FSM requires hierarchical navigation (3-4 calls per operation)
- Petri enables direct access (1-2 calls per operation)

**Qualitative Differences**:
- **FSM**: "Must be at task location. Use getTask first."
- **Petri**: "Direct state transition" / "Semantic operation bypassed navigation"

**Architecture Validation**:
- FSM enforces single-location state tracking
- Petri net enables multi-entry workflow access
- Semantic hints provide workflow guidance in Petri approach

## Troubleshooting

**If MCP servers fail to start**:
- Check `uv` is installed: `which uv`
- Verify shell scripts are executable: `chmod +x */run-mcp.sh`
- Check dataset file exists: `ls workflow-*.json`

**If test results show all failures**:
- Ensure dataset has `validTransitions` (not `validStates`)
- Check JSON syntax is valid: `python -c "import json; json.load(open('workflow-dataset.json'))"`

This test procedure provides empirical evidence for the research paper's claims about semantic hints and multi-entry workflow navigation advantages.