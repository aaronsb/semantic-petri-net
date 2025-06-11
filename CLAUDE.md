# CLAUDE.md - Semantic Petri Net Research Paper Development

This document guides the development of a research paper based on the actual insights discovered while building the Targetprocess MCP Server.

## Core Truth: What Was Actually Built

We built a Model Context Protocol (MCP) server for Targetprocess that implements:
- **Semantic hints pattern**: Tools return guidance about what to do next
- **Multi-entry workflows**: Users can enter workflows at any logical point
- **Role-based adaptation**: Different tools and guidance based on user role
- **Dynamic discovery**: System adapts to actual Targetprocess configuration

During development, we discovered these patterns naturally align with Petri net theory, explaining why traditional AI agents struggle with enterprise workflows.

## Research Paper Guidelines

### 1. Stay Grounded in Reality

- **DO**: Write about what was actually built and discovered
- **DO**: Reference specific code patterns and architectural decisions
- **DO**: Explain the "aha moment" of discovering Petri net alignment
- **DON'T**: Make up statistics, percentages, or company examples
- **DON'T**: Claim empirical studies that didn't happen
- **DON'T**: Use overly academic language to sound impressive

### 2. The Real Story to Tell

The paper should document this journey:

1. **Building the Tool**: We built an MCP server to help AI agents navigate Targetprocess
2. **Discovering Patterns**: We found that semantic hints and multi-entry workflows worked best
3. **Recognizing Theory**: These patterns matched Petri net concepts (concurrent processes, tokens, transitions)
4. **Understanding Why**: This explains why FSM-based AI agents fail at complex workflows

### 3. Key Concepts to Explain

Based on the actual implementation:

#### Semantic Hints Pattern (from semantic-hints-pattern.md)
- Tools don't just return data - they provide guidance
- Two types: `nextSteps` (workflow guidance) and `suggestions` (specific operations)
- Context-aware generation based on state and role

#### Multi-Entry Architecture (from petri-net-architecture-guide.md)
- Traditional systems force single entry points
- Real workflows have multiple valid starting positions
- Different stakeholders enter at different stages
- System adapts to entry context

#### Role-Based Operations (from personalities configuration)
- Developer, project manager, tester personas
- Different tools exposed based on role
- Contextual guidance changes with persona

### 4. Code Examples to Reference

Use real examples from the implementation:

```javascript
// Semantic hints in action (from operations)
return {
  success: true,
  entity: task,
  message: `Started working on ${task.Name}`,
  nextSteps: [
    'Task state updated to In Progress',
    'You can now log time using log_time operation',
    'Complete the task when done using complete_task'
  ]
};
```

### 5. Writing Style

- **Narrative**: Tell the story of discovery, not a dry technical report
- **Practical**: Focus on why this matters for real AI agent development
- **Honest**: Acknowledge what we learned through building, not research
- **Clear**: Explain concepts simply, avoiding unnecessary complexity

### 6. Structure Guidance

Suggested paper flow:
1. **Introduction**: The challenge of AI agents in enterprise workflows
2. **Building the Solution**: What we set out to build and why
3. **Pattern Discovery**: The semantic hints and multi-entry patterns that emerged
4. **Theoretical Connection**: How these patterns align with Petri net theory
5. **Implementation Insights**: What worked, what didn't, and why
6. **Implications**: What this means for AI agent architecture

### 7. What NOT to Include

- Fabricated empirical data or statistics
- Made-up company case studies
- Complex mathematical proofs
- Claims of comprehensive research studies
- Overly broad generalizations

### 8. Key Message

The core insight: Enterprise workflows are naturally concurrent and multi-entry (like Petri nets), but AI agents are built for sequential, single-entry processes (like FSMs). This mismatch causes systematic failures. We discovered this by building tools that worked around the mismatch.

## Development Commands

When working on the paper:
```bash
# Create a new section
mkdir -p sections
touch sections/introduction.md

# Review actual implementation for examples
ls /home/aaron/Projects/ai/mcp/apptio-target-process-mcp/docs/

# Keep it simple and truthful
```

## Remember

This is a paper about discovering patterns through building, not about conducting formal research. Be proud of the genuine insights without needing to inflate them into something they're not.