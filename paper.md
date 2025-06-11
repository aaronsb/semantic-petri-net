# Beyond Sequential Thinking: How Building an MCP Server Revealed Why AI Agents Fail at Enterprise Workflows

## Abstract

While building a Model Context Protocol (MCP) server for Targetprocess, we discovered architectural patterns that fundamentally challenge how AI agents navigate complex enterprise workflows. Our implementation revealed that successful AI-assisted workflow navigation requires two key patterns: semantic hints that guide next actions, and multi-entry architectures that allow workflows to begin at any logical point. These patterns naturally align with Petri net theory—a mathematical framework for modeling concurrent, distributed systems. This alignment explains why traditional AI agents, built on finite state machine (FSM) assumptions, systematically fail when confronted with the inherently concurrent and multi-path nature of enterprise workflows. This paper documents our journey from building a practical tool to discovering a theoretical framework that reshapes how we think about AI agent architecture.

## 1. Introduction: The Enterprise Workflow Challenge

Anyone who has tried to use AI agents for complex enterprise tasks knows the frustration. You ask the agent to "update the project status," and it responds with a rigid sequence: first create a project, then add tasks, then assign team members, and finally—after dozens of unnecessary steps—update the status. But you already have a project. You already have tasks. You just wanted to update the status.

### The Phone Tree From Hell

[TODO: Add concrete example showing the painful reality of current AI agents]
```
User: "Move task #123 to In Progress"

AI Agent (Current State):
"To update task status, I need to:
1. List all projects
2. Find your project  
3. List all tasks
4. Find your task
5. Check current status
6. Validate transition
7. Finally update

Processing... (7 API calls later)"

VS.

AI Agent (With Semantic Hints):
"Updating task #123 to 'In Progress'
✓ Task state changed
→ You can now log time using log_time
→ Complete the task when done using complete_task"
```

This pattern repeats across enterprise tools: AI agents assume every interaction starts from zero, following predetermined paths that rarely match how real work happens. Teams don't follow linear workflows. A developer might jump directly to logging time on a bug. A project manager might start by reviewing team capacity. A tester might begin by reopening a supposedly fixed issue. Real workflows have multiple entry points, concurrent activities, and context-dependent paths.

We encountered this challenge firsthand while building an MCP server for Targetprocess, an agile project management platform. What started as a straightforward integration project became a journey of discovery that would fundamentally change how we think about AI agents and enterprise workflows.

The problem wasn't just technical—it was conceptual. Traditional AI agents are built on finite state machine (FSM) principles: start here, follow this path, end there. But enterprise workflows don't work that way. They're more like busy intersections where multiple paths converge and diverge, where the right next step depends on who you are, what you're doing, and where you've been.

This paper tells the story of how we discovered a better way. Through iterative development and real-world testing, we identified two architectural patterns that transformed our MCP server from a frustrating maze into an intuitive assistant. More surprisingly, we realized these patterns weren't new—they aligned perfectly with Petri net theory, a mathematical framework developed in the 1960s for modeling concurrent systems.

This discovery explains not just why our solution worked, but why traditional AI agents systematically fail at enterprise workflows. It's not a bug—it's a fundamental mismatch between tool architecture and workflow reality.

## 2. Visual Comparison: FSM vs Our Discovery

### The Fundamental Mismatch Visualized

[TODO: Add visual diagrams showing side-by-side comparison]

```
FSM Approach:                    Our Discovery (Petri Net Pattern):
                                
Start → Create → Assign → Done   Multiple Entry Points
  ↓                               ↗     ↗     ↗
 Fail                          Create Assign Update
                                 ↘     ↘     ↘
                               [Semantic Context]
                                      ↓
                               Dynamic Next Steps
```

### Why FSMs Fail at Real Workflows

[TODO: Add diagram showing state explosion problem]
- Single active state limitation
- Every combination needs a new state
- No concurrent activities
- Rigid sequential paths

### The Petri Net Advantage

[TODO: Add diagram showing tokens in multiple places]
- Multiple tokens (work items) 
- In multiple places (states) simultaneously
- Natural concurrency support
- Dynamic path discovery

## 3. A Petri Net Primer

[TODO: Add simple, accessible explanation of Petri nets for readers unfamiliar with the concept]

### What Are Petri Nets?

For readers unfamiliar with Petri nets, here's a simple explanation:

- **Places**: Possible states or conditions (circles)
- **Transitions**: Actions that change state (rectangles)
- **Tokens**: Markers representing work items (dots)
- **Arcs**: Connections showing valid flows (arrows)

The key difference from FSMs: **multiple tokens can exist in multiple places simultaneously**, naturally modeling concurrent workflows.

### Why This Matters for AI Agents

Traditional FSM-based agents can only track one state at a time. But in enterprise workflows:
- A developer might have 5 tasks in different states
- Teams work on parallel streams
- Context switches are the norm, not the exception

## 4. The Evolution: From API Wrapper to Petri Net Executor

### Month 1: The Naive Beginning

We started with conventional patterns, creating tools that mirrored API endpoints:

```javascript
// Simple API wrapper approach
async function updateTaskState(taskId, state) {
  return await api.update(`/tasks/${taskId}`, { state });
}
```

It worked—technically. But using it felt like navigating a phone tree from hell. Every simple request triggered a cascade of tool calls as the AI agent tried to establish context.

### Month 3: The Semantic Hints Emergence

Watching the AI struggle, we realized the core issue: tools returned data but no guidance. The agent knew what happened but not what should happen next.

```javascript
// Semantic hints emerge
async function updateTaskState(taskId, state) {
  const result = await api.update(`/tasks/${taskId}`, { state });
  return {
    ...result,
    message: `Task updated to ${state}`,
    nextSteps: [
      'Task state changed successfully',
      'You can now log time if working on it',
      'Consider updating related tasks'
    ],
    suggestions: [
      `log_time ${taskId} "2h" "Working on implementation"`,
      `add_comment ${taskId} "Started work"`,
      `complete_task ${taskId}`
    ]
  };
}
```

### Month 5: Full Multi-Entry Pattern

The final evolution: tools that work from any starting point:

```javascript
// Full Petri net pattern implementation
async function startWorkingOn(identifier, context) {
  // Find the task flexibly (ID, name, or partial match)
  const task = await findTask(identifier);
  
  // Establish necessary context (check preconditions)
  if (!isAssigned(task, context.user)) {
    await assignTask(task, context.user);
  }
  
  // Transition to appropriate state (fire transition)
  const targetState = await discoverState("In Progress");
  if (task.state !== targetState) {
    await transitionTask(task, targetState);
  }
  
  // Return semantic guidance (output arcs!)
  return {
    success: true,
    entity: task,
    message: `Started working on ${task.name}`,
    nextSteps: generateWorkflowSteps(task, context),      // These ARE Petri net arcs!
    suggestions: generateContextualSuggestions(task, context)  // These ARE enabled transitions!
  };
}
```

## 5. The "Aha" Moment: Recognizing Petri Nets

### The Semantic Hints ARE Petri Net Arcs

As we documented these patterns, it clicked: we had accidentally implemented a Petri net executor:

```javascript
// This looks like a simple return structure...
return {
  success: true,
  entity: task,
  nextSteps: [        // But these ARE the output arcs!
    'Task marked as complete',
    'You can now create a pull request',
    'Consider updating test documentation'
  ],
  suggestions: [      // And these ARE the enabled transitions!
    'create_pr "Implements ' + task.name + '"',
    'find_related_tests',
    'start_next_task'
  ]
};
```

### Mapping to Petri Net Theory

Our architecture mapped perfectly to Petri net concepts:

| Our Implementation | Petri Net Concept | Why It Works |
|-------------------|-------------------|--------------|
| Task states | Places | Multiple states can be active |
| Semantic operations | Transitions | Context-aware firing rules |
| Work items | Tokens | Flow through the network |
| nextSteps/suggestions | Arcs | Guide token movement |

## 6. Building the Solution: The Full Journey

### The Initial Challenge

Our goal seemed straightforward: build an MCP server that would help AI agents interact with Targetprocess. The Model Context Protocol provides a standardized way for AI assistants to access external tools and data sources. In theory, we just needed to wrap Targetprocess's API in MCP-compatible tools.

The first implementation followed conventional patterns. We created tools that mirrored API endpoints:
- `get_projects()` - List all projects
- `create_task(project_id, name, description)` - Create a new task
- `update_task_state(task_id, state)` - Change task state
- `assign_user(task_id, user_id)` - Assign task to user

### The First Breakthrough: Semantic Hints

[Content from original paper sections 2.2]

### The Second Breakthrough: Multi-Entry Workflows

[Content from original paper section 2.3]

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

## 7. The Theory-Practice Bridge: Why This Matters

### Current State of AI Agents
"AI agents fail at enterprise workflows because they assume single-threaded, sequential processes"

### Our Discovery  
"Real workflows are multi-threaded, concurrent, and context-dependent - exactly what Petri nets model"

### The Bridge
"By accidentally implementing Petri net patterns, we solved the fundamental mismatch"

[TODO: Expand this section with concrete examples of how the theory explains the practice]

## 8. Implementation Insights: Lessons Learned

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

The most unexpected benefit: semantic hints became living documentation. Instead of maintaining separate docs, the system self-documents through its responses.

### Performance Through Statelessness

Early versions tried to maintain workflow state between calls. This created complexity and bugs. The solution: make each operation stateless but context-aware.

### The Power of Personality-Based Injection

What started as a way to reduce tool clutter became a powerful architecture pattern. Different roles see different tools, but more importantly, they get different semantic contexts.

## 9. Validation Possibilities: Formal Verification

[TODO: Add section on how Petri net analysis tools could validate these workflows]

### What Could Be Proven

Using formal Petri net analysis, we could verify:
- **Deadlock Freedom**: No workflow gets stuck
- **Liveness**: All transitions can eventually fire
- **Boundedness**: Finite state space
- **Soundness**: Proper termination guarantees

### Why This Matters for Enterprise

Formal verification means:
- Predictable behavior at scale
- Compliance guarantees
- Reduced testing burden
- Mathematical confidence in correctness

## 10. Interactive Elements

[TODO: Placeholder for interactive demonstrations]
- Interactive FSM vs Petri net comparison
- Workflow builder showing multi-entry points
- Semantic hints generator
- Live demo of the MCP server

## 11. The "So What?" - Implications and Call to Action

### For Developers
**Stop building FSM-based agents for workflows.** The mismatch is fundamental and unfixable. Start thinking in terms of concurrent, multi-entry systems.

### For Researchers
**Investigate Petri net patterns for AI agents.** This paper shows one successful application, but the pattern likely generalizes.

### For Standards Bodies
**The MCP spec should guide toward these patterns.** Current examples lead developers toward simple API wrappers that will fail at scale.

### For Enterprises
**Demand workflow-aware AI tools.** Don't accept agents that force linear workflows on your inherently concurrent processes.

## 12. Conclusion: From Practice to Theory and Back

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

## References

### From Our Research

[1] Lo Bianco, G., Ilieva, N., Fanti, M. P., Bandinelli, R., & Schenone, V. (2023). Action-Evolution Petri Nets: a Framework for Modeling and Solving Dynamic Task Assignment Problems. ArXiv. https://arxiv.org/abs/2306.02910

[2] Brooks, R., Arbib, M., & Metta, G. (2008). Comparison of Petri Net and Finite State Machine Discrete Event Control of Distributed Surveillance Network. ResearchGate. https://www.researchgate.net/publication/220505189

[3] Stack Overflow Community. (2019). What's the difference of Petri Nets and Finite State Machines? Stack Overflow. https://stackoverflow.com/questions/53980748/whats-the-difference-of-petri-nets-and-finite-state-machines

[4] O'Reilly Media. (1995). Petri Nets for State Machines - Field-Programmable Gate Arrays: Reconfigurable Logic for Rapid Prototyping and Implementation of Digital Systems. O'Reilly. https://www.oreilly.com/library/view/field-programmable-gate-arrays/9780471556657/s27-27.html

[5] LastMile AI. (2025). mcp-agent: Build effective agents using Model Context Protocol and simple workflow patterns. GitHub. https://github.com/lastmile-ai/mcp-agent

[6] Hooopo. (2025). petri_flow: Petri Net Workflow Engine for Ruby. GitHub. https://github.com/hooopo/petri_flow

[7] LangChain. (2025). LangGraph Documentation. https://langchain-ai.github.io/langgraph/

[8] LangChain Blog. (2025). LangGraph: Multi-Agent Workflows. https://blog.langchain.dev/langgraph/

[9] LangChain. (2025). LangGraph Low-Level Concepts. https://langchain-ai.github.io/langgraph/concepts/low_level/

[10] Microsoft Security. (2025). New whitepaper outlines the taxonomy of failure modes in AI agents. Microsoft Security Blog. https://www.microsoft.com/en-us/security/blog/2025/04/24/new-whitepaper-outlines-the-taxonomy-of-failure-modes-in-ai-agents/

[11] Salesforce Engineering. (2025). Agentforce: Scaling Agentic AI for Enterprise Automation. https://engineering.salesforce.com/agentforce-scaling-agentic-ai-for-enterprise-automation-observability-powering-2-billion-predictions-monthly/

[12] n8n Community. (2025). AI Agent Stuck in Infinite Loop, Repeatedly Triggering Tools. GitHub Issues. https://github.com/n8n-io/n8n/issues/13525

[13] Meirwah. (2025). awesome-workflow-engines: A curated list of awesome open source workflow engines. GitHub. https://github.com/meirwah/awesome-workflow-engines

### From the Architecture Guide

Van der Aalst, W.M.P. (2016). Process Mining: Data Science in Action. Springer. DOI: 10.1007/978-3-662-49851-4

Murata, T. (1989). Petri nets: Properties, analysis and applications. Proceedings of the IEEE, 77(4), 541-580. DOI: 10.1109/5.24143

Van der Aalst, W.M.P., & ter Hofstede, A.H.M. (2005). YAWL: Yet another workflow language. Information Systems, 30(4), 245-275. DOI: 10.1016/j.is.2004.02.002

Oppermann, R., & Rasher, R. (1997). Adaptability and adaptivity in learning support systems. Knowledge Transfer, 2, 173-179.

Jameson, A. (2003). Adaptive interfaces and agents. Human-Computer Interaction: Design Issues, Solutions, and Applications, 105-130.

Benyon, D., & Murray, D. (1993). Adaptive systems: From intelligent tutoring to autonomous agents. Knowledge-based Systems, 6(4), 197-219. DOI: 10.1016/0950-7051(93)90012-P

Georgakopoulos, D., Hornick, M., & Sheth, A. (1995). An overview of workflow management: From process modeling to workflow automation infrastructure. Distributed and Parallel Databases, 3(2), 119-153. DOI: 10.1007/BF01277643

Van der Aalst, W.M.P. (2013). Business process management: A comprehensive survey. ISRN Software Engineering, 2013. DOI: 10.1155/2013/507984

Dumas, M., La Rosa, M., Mendling, J., & Reijers, H.A. (2018). Fundamentals of Business Process Management. Springer. DOI: 10.1007/978-3-662-56509-4

Dey, A.K. (2001). Understanding and using context. Personal and Ubiquitous Computing, 5(1), 4-7. DOI: 10.1007/s007790170019

Chen, G., & Kotz, D. (2000). A survey of context-aware mobile computing research. Technical Report TR2000-381, Dartmouth College.

Russell, N., ter Hofstede, A.H.M., Edmond, D., & van der Aalst, W.M.P. (2005). Workflow data patterns: Identification, representation and tool support. Conceptual Modeling–ER 2005, 353-368. DOI: 10.1007/11568322_23

Van der Aalst, W.M.P., ter Hofstede, A.H.M., Kiepuszewski, B., & Barros, A.P. (2003). Workflow patterns. Distributed and Parallel Databases, 14(1), 5-51. DOI: 10.1023/A:1022883727209

OASIS WSBPEL Technical Committee (2007). Web Services Business Process Execution Language Version 2.0. Available at OASIS: http://docs.oasis-open.org/wsbpel/2.0/wsbpel-v2.0.html

Object Management Group (2011). Business Process Model and Notation (BPMN) Version 2.0. Available at OMG: https://www.omg.org/spec/BPMN/2.0/

## Appendix: Supporting Research

[TODO: Include the research findings about FSM limitations and industry evidence from the separate research document]
