# Test Methodology: FSM vs Petri Net Navigation Comparison

## Abstract

This document outlines the experimental methodology for comparing Finite State Machine (FSM) and Petri net approaches to workflow navigation in enterprise systems. We describe the test harness design, hypotheses, expected outcomes, and evaluation criteria for quantifying the performance differences between these two architectural patterns.

## 1. Research Questions

The experiment aims to answer three primary questions:

1. **Efficiency**: How many tool calls are required to achieve the same workflow goals using each approach?
2. **Flexibility**: Can each approach handle multi-entry workflows and concurrent operations?
3. **Usability**: How do semantic hints affect navigation efficiency and user experience?

## 2. Experimental Design

### 2.1 Test Environment

- **Dataset**: Eight workflow goals representing common enterprise scenarios
- **Simulators**: Two MCP servers implementing FSM and Petri net navigation
- **Metrics**: Tool call counts, goal completion rates, path analysis, semantic hint usage

### 2.2 Goal Categories

The test suite includes goals designed to stress different aspects of workflow navigation:

1. **Linear Progression Goals** (Goals 1-2)
   - Ship Authentication Feature
   - Fix Critical Bug
   - Expected to show moderate difference between approaches

2. **State Transition Goals** (Goals 3-5)
   - Complete Code Review
   - Ready for Deployment
   - Fix Performance Issue
   - Expected to show significant efficiency gains for Petri net

3. **Efficiency Challenge Goals** (Goals 6-8)
   - Start Any Task Efficiently (< 3 calls)
   - Reassign Work Item (without state check)
   - Advance Multiple Items (< 10 calls)
   - Expected to be impossible or very difficult for FSM

### 2.3 Test Harness Architecture

The test harness simulates both navigation approaches:

```python
class NavigationMetrics:
    tool_calls: int          # Total API calls made
    goals_completed: List    # Successfully achieved goals
    paths_taken: List[List]  # Sequence of calls per goal
    semantic_hints_followed: int  # Guidance usage
    errors_encountered: int  # Failed attempts
```

## 3. Hypotheses

### H1: Tool Call Efficiency
**Hypothesis**: The Petri net navigator will require 60-80% fewer tool calls than the FSM navigator to achieve the same goals.

**Rationale**: Multi-entry operations eliminate navigation overhead, allowing direct access to any workflow entity.

### H2: Goal Completion Rate
**Hypothesis**: The FSM navigator will fail to complete efficiency-focused goals (6-8) within the specified constraints.

**Rationale**: Hierarchical navigation inherently requires more steps than the goal constraints allow.

### H3: Semantic Hint Impact
**Hypothesis**: Semantic hints will reduce the cognitive load and increase goal completion speed in the Petri net approach.

**Rationale**: Contextual guidance eliminates the need to remember valid state transitions.

### H4: Concurrent Operations
**Hypothesis**: Only the Petri net navigator will successfully complete goals requiring parallel state changes.

**Rationale**: FSM's single-state limitation prevents true concurrent operations.

## 4. Expected Outcomes

### 4.1 Quantitative Predictions

| Metric | FSM Navigator | Petri Net Navigator | Expected Ratio |
|--------|---------------|---------------------|----------------|
| Average calls/goal | 8-12 | 1-3 | 4-6x |
| Total tool calls | 80-100 | 15-25 | 4-5x |
| Goals completed | 5-6/8 | 8/8 | - |
| Semantic hints used | 0 | 6-8 | - |

### 4.2 Path Analysis Predictions

**FSM Path Example** (Ship Authentication):
```
listProjects() → getProject() → listTasks() → getTask() → 
getState() → assign() → updateState() → updateState() → 
updateState() → updateState()
```
Total: 10 calls

**Petri Net Path Example** (Ship Authentication):
```
startWorkingOn('task-auth') → completeTask('task-auth')
```
Total: 2 calls

### 4.3 Failure Mode Predictions

FSM Navigator expected failures:
- Goal 6: Cannot start task in < 3 calls (requires minimum 6-8)
- Goal 8: Cannot advance multiple items in < 10 calls (requires 12+)

Petri Net Navigator expected successes:
- All goals achievable within constraints
- Multi-entry eliminates navigation overhead

## 5. Evaluation Criteria

### 5.1 Primary Metrics
1. **Efficiency Ratio**: Total FSM calls / Total Petri net calls
2. **Success Rate**: Goals completed / Total goals
3. **Average Path Length**: Calls per successful goal

### 5.2 Secondary Metrics
1. **Semantic Hint Utilization**: How often guidance influenced decisions
2. **Error Recovery**: Ability to handle invalid states
3. **Cognitive Load Proxy**: Path complexity and decision points

### 5.3 Statistical Significance
While this is a deterministic simulation, the results demonstrate architectural differences that would scale to real-world usage:
- Each additional workflow entity multiplies FSM navigation overhead
- Petri net costs remain constant regardless of system size

## 6. Threats to Validity

### 6.1 Internal Validity
- **Simulation Accuracy**: Real implementations may have additional complexities
- **Goal Selection**: Goals chosen to demonstrate known architectural differences
- **Optimal Paths**: FSM paths assume perfect knowledge of hierarchy

### 6.2 External Validity
- **Enterprise Variety**: Different workflow systems may have unique constraints
- **User Behavior**: Human users might navigate differently than simulated
- **Scale Effects**: Larger systems would amplify the differences

### 6.3 Construct Validity
- **Tool Calls as Proxy**: Assumes each call has equal cost/complexity
- **Semantic Hints**: Value depends on user experience and familiarity

## 7. Implications

### 7.1 For Architecture Design
Results will demonstrate why workflow systems need:
- Multi-entry navigation capabilities
- Semantic operation support
- Concurrent state management

### 7.2 For AI Agent Development
Findings suggest AI agents require:
- Workflow-aware architectures
- Context-preserving operations
- Semantic understanding of goals

### 7.3 For Theory
Validates that:
- Petri net patterns naturally emerge in workflow domains
- FSM limitations are fundamental, not implementation-specific
- Semantic hints bridge the gap between theory and usability

## 8. Conclusion

This experiment provides empirical evidence for the theoretical advantages of Petri net-based workflow navigation. By quantifying the efficiency gains and demonstrating the impossibility of certain operations in FSM-based systems, we establish a clear case for adopting Petri net patterns in enterprise AI agents.

The test harness serves as both a validation tool and a demonstration of the practical implications of choosing the appropriate computational model for workflow navigation.