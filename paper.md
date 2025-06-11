# Beyond Sequential Thinking: How Building an MCP Server Revealed Why AI Agents Fail at Enterprise Workflows

## Abstract

While building a Model Context Protocol (MCP) server for Targetprocess, we discovered architectural patterns that fundamentally challenge how AI agents navigate complex enterprise workflows. Our implementation revealed that successful AI-assisted workflow navigation requires two key patterns: semantic hints that guide next actions, and multi-entry architectures that allow workflows to begin at any logical point. These patterns naturally align with Petri net theory—a mathematical framework for modeling concurrent, distributed systems. This alignment explains why traditional AI agents, built on finite state machine (FSM) assumptions, systematically fail when confronted with the inherently concurrent and multi-path nature of enterprise workflows. This paper documents our journey from building a practical tool to discovering a theoretical framework that reshapes how we think about AI agent architecture.

## 1. Introduction: The Enterprise Workflow Challenge

Anyone who has tried to use AI agents for complex enterprise tasks knows the frustration. You ask the agent to "update the project status," and it responds with a rigid sequence: first create a project, then add tasks, then assign team members, and finally—after dozens of unnecessary steps—update the status. But you already have a project. You already have tasks. You just wanted to update the status.

This pattern repeats across enterprise tools: AI agents assume every interaction starts from zero, following predetermined paths that rarely match how real work happens. Teams don't follow linear workflows. A developer might jump directly to logging time on a bug. A project manager might start by reviewing team capacity. A tester might begin by reopening a supposedly fixed issue. Real workflows have multiple entry points, concurrent activities, and context-dependent paths.

We encountered this challenge firsthand while building an MCP server for Targetprocess, an agile project management platform. What started as a straightforward integration project became a journey of discovery that would fundamentally change how we think about AI agents and enterprise workflows.

The problem wasn't just technical—it was conceptual. Traditional AI agents are built on finite state machine (FSM) principles: start here, follow this path, end there. But enterprise workflows don't work that way. They're more like busy intersections where multiple paths converge and diverge, where the right next step depends on who you are, what you're doing, and where you've been.

This paper tells the story of how we discovered a better way. Through iterative development and real-world testing, we identified two architectural patterns that transformed our MCP server from a frustrating maze into an intuitive assistant. More surprisingly, we realized these patterns weren't new—they aligned perfectly with Petri net theory, a mathematical framework developed in the 1960s for modeling concurrent systems.

This discovery explains not just why our solution worked, but why traditional AI agents systematically fail at enterprise workflows. It's not a bug—it's a fundamental mismatch between tool architecture and workflow reality.

## 2. Building the Solution: The Targetprocess MCP Server

### The Initial Challenge

Our goal seemed straightforward: build an MCP server that would help AI agents interact with Targetprocess. The Model Context Protocol provides a standardized way for AI assistants to access external tools and data sources. In theory, we just needed to wrap Targetprocess's API in MCP-compatible tools.

The first implementation followed conventional patterns. We created tools that mirrored API endpoints:
- `get_projects()` - List all projects
- `create_task(project_id, name, description)` - Create a new task
- `update_task_state(task_id, state)` - Change task state
- `assign_user(task_id, user_id)` - Assign task to user

It worked—technically. But using it felt like navigating a phone tree from hell. Every simple request triggered a cascade of tool calls as the AI agent tried to establish context. "Move task #123 to In Progress" became:
1. List all projects
2. Find the right project
3. List tasks in that project  
4. Find task #123
5. Get task details
6. Check valid state transitions
7. Finally, update the state

### The First Breakthrough: Semantic Hints

Watching the AI struggle, we realized the core issue: tools returned data but no guidance. The agent knew what happened but not what should happen next. It was like giving someone a map with no indication of where they were or where they should go.

We started experimenting with richer return values. Instead of just confirming an action succeeded, tools began providing hints about logical next steps:

```javascript
// Before: Just data
return {
  success: true,
  task: { id: 123, state: "In Progress" }
};

// After: Data plus guidance
return {
  success: true,
  entity: task,
  message: `Started working on ${task.Name}`,
  nextSteps: [
    'Task state updated to In Progress',
    'You can now log time using log_time operation',
    'Complete the task when done using complete_task'
  ],
  suggestions: [
    `log_time 2h "Initial investigation"`,
    `add_comment "Started working on this"`,
    `complete_task`
  ]
};
```

The transformation was immediate. The AI agent stopped wandering through endless tool calls and started following contextual workflows. But this created a new problem: the hints assumed linear progression. What if someone wanted to log time on a task that wasn't "In Progress"? What if they needed to reopen a completed task?

### The Second Breakthrough: Multi-Entry Workflows

Traditional workflow systems enforce entry points. You must create a project before adding tasks. You must assign a task before logging time. These constraints make sense for data integrity but create terrible user experiences.

We redesigned our tools to work from any starting point. Each tool became intelligent enough to handle missing context:

- `start_task(identifier)` - Accepts task ID, task name, or even partial matches
- `log_time(identifier, duration, description)` - Works whether the task is assigned or not
- `find_my_work()` - Starts from the user's perspective, not the system's hierarchy

The implementation required each tool to be more sophisticated:

```javascript
async function startTask(identifier) {
  // Find the task by ID, name, or partial match
  let task = await findTask(identifier);
  
  // Check if user is assigned
  if (!task.Assignments.includes(currentUser)) {
    // Automatically assign if not already
    await assignTask(task.id, currentUser.id);
  }
  
  // Transition to In Progress if needed
  if (task.State !== "In Progress") {
    await transitionTask(task.id, "In Progress");
  }
  
  // Return rich context
  return {
    success: true,
    entity: task,
    message: `Started working on ${task.Name}`,
    nextSteps: generateNextSteps(task, currentUser),
    suggestions: generateSuggestions(task, currentUser)
  };
}
```

This pattern—tools that adapt to context rather than enforcing preconditions—transformed the user experience. The AI agent could now handle requests the way humans actually work.

### Role-Based Adaptation

Different users interact with Targetprocess differently. We implemented persona-based tool selection and hint generation:

- **Developers** see code-related tools and technical suggestions
- **Project Managers** get planning tools and team overview hints  
- **Testers** receive testing workflows and bug tracking guidance

This wasn't just about filtering tools—the semantic hints themselves adapted to role context.

### The Architecture That Emerged

By the end of development, our MCP server had evolved far from a simple API wrapper. Key architectural patterns included:

1. **Semantic Response Objects**: Every tool returned structured guidance
2. **Context-Aware Entry Points**: Tools worked from any starting state
3. **Dynamic Workflow Discovery**: Next steps generated based on current state
4. **Role-Based Adaptation**: Different paths for different users
5. **Stateless Intelligence**: Each tool call contained full context

The result was an MCP server that felt intelligent without maintaining complex state. The AI agent could jump into any part of a workflow and immediately understand what to do next.

## 3. Pattern Discovery: The Architecture Emerges

Looking back at the git history, the evolution is clear. What started as a "straightforward MCP server" (commit `a1143db`) transformed through iterative discovery into something fundamentally different.

### The Semantic Hints Revelation

The breakthrough came in early June 2025. Commit `7d1e48b` marks the moment we recognized that semantic operations weren't just a feature—they were the core pattern that made the system work:

> "Semantic layer adds workflow intelligence vs raw API wrapping"

The key insight: tools shouldn't just execute operations; they should understand workflow context and guide users to the next logical step. This wasn't planned—it emerged from watching AI agents struggle with raw API tools.

### Discovering Multi-Entry Workflows

The multi-entry pattern emerged from a different frustration. Traditional workflow systems assume linear progression: create project → add tasks → assign users → update status. But commit `4de916d` reveals our realization:

> "Real workflows have multiple valid starting positions"

We discovered this by implementing features like `start-working-on`, which accepts:
- Task IDs (for users who know exactly what they want)
- Task names (for fuzzy matching)
- Natural language ("that bug about login")

Each tool became smart enough to establish its own context rather than depending on prior setup.

### The Pattern Synthesis

By commit `f99b1f3`, we had synthesized these discoveries into a coherent architecture:

```javascript
// Before: Tools that just wrap APIs
async function updateTaskState(taskId, state) {
  return await api.update(`/tasks/${taskId}`, { state });
}

// After: Semantic operations with workflow intelligence
async function startWorkingOn(identifier, context) {
  // Find the task flexibly
  const task = await findTask(identifier);
  
  // Establish necessary context
  if (!isAssigned(task, context.user)) {
    await assignTask(task, context.user);
  }
  
  // Transition to appropriate state
  const targetState = await discoverState("In Progress");
  if (task.state !== targetState) {
    await transitionTask(task, targetState);
  }
  
  // Return semantic guidance
  return {
    success: true,
    entity: task,
    message: `Started working on ${task.name}`,
    nextSteps: generateWorkflowSteps(task, context),
    suggestions: generateContextualSuggestions(task, context)
  };
}
```

### Role-Based Evolution

The personality system (commits `af2a8c9`, `7a7e538`) wasn't initially about roles—it was about reducing tool clutter. But we discovered that different users need different semantic contexts:

- **Developers** need: "log time", "link commit", "update branch"
- **Testers** need: "fail test", "add test case", "link defect"  
- **Managers** need: "review capacity", "adjust sprint", "track velocity"

The same underlying operations, but with different semantic wrappers and workflow guidance.

### The Architecture That Emerged

What emerged wasn't designed—it was discovered through building and rebuilding. The final architecture (documented in commit `1b49c07`) centered on:

1. **Semantic Response Protocol**: Every operation returns structured guidance
2. **Flexible Entry Points**: Every tool works from any starting context
3. **Dynamic Discovery**: No hardcoded states, priorities, or workflows
4. **Contextual Intelligence**: Hints adapt to user role and current state
5. **Graceful Degradation**: Falls back to raw tools when semantic layer fails

## 4. The Theoretical Connection: Why It Worked

As we documented these patterns, something nagged at us. The architecture felt familiar, but we couldn't place it. Then, while writing the architecture guide, it clicked: we had accidentally implemented a Petri net.

### The Petri Net Parallel

Petri nets, developed by Carl Adam Petri in 1962, model concurrent, asynchronous systems using:
- **Places**: Possible states or conditions
- **Transitions**: Events that move between states
- **Tokens**: Markers that flow through the network
- **Arcs**: Connections that define valid flows

Our architecture mapped perfectly:
- **Places**: Task states, user contexts, workflow positions
- **Transitions**: Semantic operations that move between states
- **Tokens**: The actual work items (tasks, bugs, stories)
- **Arcs**: The nextSteps and suggestions that guide flow

### Why FSM-Based Agents Fail

Traditional AI agents are built on finite state machine principles:
- Single current state
- Deterministic transitions
- Sequential execution
- Global state tracking

But enterprise workflows are inherently concurrent:
- Multiple tasks in different states
- Parallel work streams
- Context-dependent transitions
- Local state with global coordination

The mismatch is fundamental. It's like trying to model highway traffic with a single-lane road—the model can't represent the reality.

### The Accidental Solution

Without knowing it, we built a Petri net executor:

```javascript
// This is essentially a Petri net transition
async function completeTask(identifier, context) {
  const task = await findTask(identifier);
  
  // Check preconditions (input places have tokens)
  if (!canComplete(task, context)) {
    return generateBlockedResponse(task, context);
  }
  
  // Fire transition (move tokens)
  await transitionTask(task, "Done");
  
  // Generate postconditions (output places)
  return {
    success: true,
    entity: task,
    // These are the output arcs
    nextSteps: [
      'Task marked as complete',
      'You can now create a pull request',
      'Consider updating test documentation'
    ],
    // These are alternative transitions
    suggestions: [
      'create_pr "Implements ' + task.name + '"',
      'find_related_tests',
      'start_next_task'
    ]
  };
}
```

### The Theory Explains the Practice

Understanding the Petri net connection explained so much:

1. **Why semantic hints work**: They encode the Petri net structure (places and transitions)
2. **Why multi-entry succeeds**: Petri nets naturally support concurrent entry points
3. **Why roles matter**: Different views of the same Petri net structure
4. **Why discovery is essential**: Real Petri nets are dynamic, not static

## 5. Implementation Insights: What We Learned

Building this system taught us practical lessons that go beyond theory.

### Discovery Over Configuration

Early attempts hardcoded states, priorities, and workflows. Every enterprise Targetprocess instance was different. The solution: dynamic discovery.

```javascript
// Don't do this
const VALID_STATES = ['Open', 'In Progress', 'Done'];

// Do this
async function discoverStates(entityType) {
  try {
    const metadata = await api.getMetadata(entityType);
    return metadata.states.map(s => s.name);
  } catch (error) {
    // Graceful fallback
    return ['Open', 'In Progress', 'Done'];
  }
}
```

### Semantic Hints as Documentation

The most unexpected benefit: semantic hints became living documentation. Instead of maintaining separate docs, the system self-documents through its responses:

```javascript
return {
  success: true,
  message: 'Created bug report',
  entity: bug,
  nextSteps: [
    'Bug created with ID #' + bug.id,
    'Assigned to QA team for verification',
    'Priority set based on severity'
  ],
  suggestions: [
    'add_test_case "Reproduction steps for bug #' + bug.id + '"',
    'link_to_story ' + bug.relatedStory,
    'assign_to_developer'
  ]
};
```

New users learn the workflow by using it. The AI agent learns what to do next by reading the hints.

### Graceful Degradation Matters

Not every operation needs semantic wrapping. We learned to provide both:
- Semantic operations for common workflows
- Raw tools for discovery and edge cases

This hybrid approach meant the system remained useful even when semantic operations didn't match the user's needs.

### Performance Through Statelessness

Early versions tried to maintain workflow state between calls. This created complexity and bugs. The solution: make each operation stateless but context-aware:

```javascript
// Each operation establishes its own context
async function logTime(identifier, duration, description) {
  const task = await findTask(identifier);
  const user = await getCurrentUser();
  const timeEntity = await discoverTimeEntity();
  
  // No assumption about prior state
  if (!task.assignees.includes(user)) {
    await assignTask(task, user);
  }
  
  // ... rest of operation
}
```

### The Power of Personality-Based Injection

What started as a way to reduce tool clutter became a powerful architecture pattern. Different roles see different tools, but more importantly, they get different semantic contexts:

```javascript
// Same operation, different personality
function generateNextSteps(task, personality) {
  switch(personality) {
    case 'developer':
      return [
        'Task updated',
        'Remember to update your branch',
        'Run tests before marking complete'
      ];
    case 'tester':
      return [
        'Task updated', 
        'Test cases should be updated',
        'Check related bugs before closing'
      ];
    case 'manager':
      return [
        'Task updated',
        'Sprint burndown updated',
        'Team capacity adjusted'
      ];
  }
}
```

## 6. Implications: Rethinking AI Agent Architecture

This journey from a simple API wrapper to discovering Petri net patterns has profound implications for AI agent design.

### The Workflow Mismatch is Fundamental

It's not that current AI agents are poorly implemented—they're solving the wrong problem. FSM-based architectures cannot model concurrent workflows. No amount of prompt engineering or fine-tuning will fix this fundamental mismatch.

### Semantic Layers Enable AI Comprehension

Raw APIs are too low-level for AI agents to use effectively. Semantic operations provide the right abstraction level:
- High enough to understand intent
- Low enough to execute precisely
- Rich enough to guide next actions

### Multi-Entry is Not Optional

Real users don't follow scripts. They jump into workflows at arbitrary points with partial context. Systems must be designed for this reality, not fight against it.

### Discovery Beats Configuration

Enterprise systems are too varied and dynamic for static configuration. Building discovery into the architecture makes systems adaptive rather than brittle.

### The Future of AI Agents

The next generation of AI agents needs:
1. **Concurrent workflow models** (Petri nets, not FSMs)
2. **Semantic operation layers** (guidance, not just execution)
3. **Multi-entry architectures** (context-aware, not sequential)
4. **Dynamic discovery** (adaptive, not configured)
5. **Role-based contexts** (personalized workflows)

### A New Pattern Language

We need a new vocabulary for AI agent capabilities:
- **Workflow-aware**: Understands concurrent, multi-path processes
- **Semantically guided**: Provides next-step intelligence
- **Context-adaptive**: Works from any entry point
- **Role-sensitive**: Adapts to user perspective

## 7. Conclusion: From Practice to Theory and Back

This paper tells an unusual story. We didn't start with Petri net theory and implement it. We built a practical tool, discovered patterns that worked, and only later realized we had rediscovered fundamental computer science principles.

The journey teaches us several lessons:

**Listen to the Pain**: The patterns emerged from real frustrations—AI agents getting lost in API calls, users fighting linear workflows, teams working differently. The pain points guided us to solutions.

**Patterns Emerge from Practice**: We didn't design semantic hints or multi-entry workflows. They emerged from iterative development and user feedback. The best architectures often aren't designed—they're discovered.

**Theory Validates Practice**: Finding that our patterns aligned with Petri net theory wasn't just intellectually satisfying. It explained why they worked and suggested future improvements.

**The Mismatch Matters**: Understanding why FSM-based agents fail at enterprise workflows isn't academic. It's the key to building better tools. You can't fix what you don't understand.

### The Real Innovation

The real innovation isn't any single pattern but their synthesis:
- Semantic hints without multi-entry would still force linear workflows
- Multi-entry without semantic guidance would leave users lost
- Both without dynamic discovery would break on enterprise variation
- All three without role adaptation would ignore how teams actually work

Together, they create something new: an AI agent architecture that works with human workflows rather than against them.

### Open Questions

This work raises questions for future research:
- Can these patterns extend beyond project management tools?
- How do we formalize semantic hint generation?
- What's the right balance between semantic and raw operations?
- How do we measure workflow comprehension in AI systems?

### Final Thoughts

Building the Targetprocess MCP server taught us that the best discoveries come from building real systems for real users. We didn't set out to challenge FSM-based agent architectures or rediscover Petri nets. We just wanted to help AI agents navigate Targetprocess without getting lost.

Sometimes the most profound insights come not from theoretical research but from the humble act of building something useful and asking why it works.

The code is open source. The patterns are documented. Now it's time to see what others discover when they build on these ideas.

---

*The Targetprocess MCP Server is available at [github.com/aaronsb/apptio-target-process-mcp](https://github.com/aaronsb/apptio-target-process-mcp). This paper documents patterns discovered during its development from February to June 2025.*