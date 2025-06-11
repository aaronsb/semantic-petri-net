#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load workflow data
const workflowData = JSON.parse(
  await readFile(join(__dirname, '../workflow-test-dataset.json'), 'utf-8')
);

// Petri Net State - multiple concurrent tokens
let petriState = {
  tokens: {}, // Multiple work items can be active
  places: {}, // Current state of each entity
  toolCallCount: 0,
  goalsFound: [],
  semanticHintsUsed: 0
};

// Initialize places from workflow data
for (const [id, task] of Object.entries(workflowData.entities.tasks)) {
  petriState.places[id] = { state: task.state, assignee: task.assignee };
}
for (const [id, bug] of Object.entries(workflowData.entities.bugs)) {
  petriState.places[id] = { state: bug.state, assignee: bug.assignee };
}

const server = new Server(
  {
    name: 'petri-workflow-navigator',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Semantic hint generator
const generateSemanticHints = (entity, action) => {
  const hints = {
    nextSteps: [],
    suggestions: []
  };

  if (entity.type === 'task') {
    switch (entity.state) {
      case 'Open':
        hints.nextSteps = [
          'Task is ready to be started',
          'Assign to a developer to begin work',
          'Check dependencies before starting'
        ];
        hints.suggestions = [
          `startWorkingOn('${entity.id}')`,
          `assignTask('${entity.id}', 'user-alice')`,
          'checkDependencies()'
        ];
        break;
      case 'In Progress':
        hints.nextSteps = [
          'Task is being worked on',
          'Move to Review when complete',
          'You can log time or add comments'
        ];
        hints.suggestions = [
          `completeTask('${entity.id}')`,
          `updateTaskState('${entity.id}', 'Review')`,
          'logTime(2, "Implemented feature")'
        ];
        break;
      case 'Review':
        hints.nextSteps = [
          'Task is ready for testing',
          'Address review feedback if needed',
          'Move to Testing or back to In Progress'
        ];
        hints.suggestions = [
          `updateTaskState('${entity.id}', 'Testing')`,
          `updateTaskState('${entity.id}', 'In Progress')`,
          'getReviewComments()'
        ];
        break;
    }
  }

  return hints;
};

// Tool: Multi-entry semantic operations
server.setRequestHandler('tools/list', async () => ({
  tools: [
    // Semantic operations (multi-entry)
    {
      name: 'startWorkingOn',
      description: 'Start working on any task (assigns if needed, moves to In Progress)',
      inputSchema: {
        type: 'object',
        properties: {
          identifier: { type: 'string', description: 'Task ID or name' },
        },
        required: ['identifier'],
      },
    },
    {
      name: 'completeTask',
      description: 'Mark task as complete (handles state transitions)',
      inputSchema: {
        type: 'object',
        properties: {
          identifier: { type: 'string' },
        },
        required: ['identifier'],
      },
    },
    {
      name: 'workOnBug',
      description: 'Start working on a bug (assigns and transitions)',
      inputSchema: {
        type: 'object',
        properties: {
          identifier: { type: 'string' },
        },
        required: ['identifier'],
      },
    },
    {
      name: 'fixBug',
      description: 'Mark bug as fixed',
      inputSchema: {
        type: 'object',
        properties: {
          identifier: { type: 'string' },
        },
        required: ['identifier'],
      },
    },
    {
      name: 'verifyBug',
      description: 'Verify a bug fix',
      inputSchema: {
        type: 'object',
        properties: {
          identifier: { type: 'string' },
        },
        required: ['identifier'],
      },
    },
    {
      name: 'checkWorkflow',
      description: 'Get current workflow state and suggestions',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    // Direct access operations (Petri net allows jumping to any place)
    {
      name: 'getEntity',
      description: 'Get any entity directly by ID',
      inputSchema: {
        type: 'object',
        properties: {
          entityId: { type: 'string' },
        },
        required: ['entityId'],
      },
    },
    {
      name: 'updateEntity',
      description: 'Update any entity state directly',
      inputSchema: {
        type: 'object',
        properties: {
          entityId: { type: 'string' },
          newState: { type: 'string' },
        },
        required: ['entityId', 'newState'],
      },
    },
    {
      name: 'assignEntity',
      description: 'Assign any entity to a user',
      inputSchema: {
        type: 'object',
        properties: {
          entityId: { type: 'string' },
          userId: { type: 'string' },
        },
        required: ['entityId', 'userId'],
      },
    },
    {
      name: 'checkGoals',
      description: 'Check achieved goals',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'getMetrics',
      description: 'Get navigation metrics',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
  ],
}));

// Check goals after operations
const checkGoalsAfterOperation = () => {
  const newGoals = [];
  for (const goal of workflowData.goals) {
    if (petriState.goalsFound.includes(goal.id)) continue;
    
    if (goal.condition.entity) {
      const place = petriState.places[goal.condition.entity];
      if (place && place.state === goal.condition.state) {
        newGoals.push(goal);
      }
    } else if (goal.condition.action === 'Move any Open task to In Progress') {
      // Check if we just moved an open task
      for (const [id, place] of Object.entries(petriState.places)) {
        if (place.state === 'In Progress' && place.justTransitioned) {
          newGoals.push(goal);
          break;
        }
      }
    }
  }
  
  if (newGoals.length > 0) {
    petriState.goalsFound.push(...newGoals.map(g => g.id));
  }
  return newGoals;
};

// Tool implementations with Petri net patterns
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;
  petriState.toolCallCount++;

  switch (name) {
    case 'startWorkingOn': {
      petriState.semanticHintsUsed++;
      
      // Find task (multi-entry: by ID or name)
      let task = workflowData.entities.tasks[args.identifier];
      if (!task) {
        task = Object.values(workflowData.entities.tasks).find(t => 
          t.name.toLowerCase().includes(args.identifier.toLowerCase())
        );
      }
      
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found.' }] };
      }

      const place = petriState.places[task.id];
      
      // Semantic operation: handle all necessary transitions
      if (!place.assignee) {
        place.assignee = 'user-alice'; // Auto-assign
      }
      
      if (place.state === 'Open') {
        place.state = 'In Progress';
        place.justTransitioned = true;
      }
      
      // Generate semantic hints
      const hints = generateSemanticHints({ ...task, state: place.state, type: 'task' }, 'started');
      const achievedGoals = checkGoalsAfterOperation();
      
      return {
        content: [{
          type: 'text',
          text: `✓ Started working on "${task.name}"
State: ${place.state}
Assigned to: ${place.assignee}
${achievedGoals.length > 0 ? `\n🎯 GOALS ACHIEVED: ${achievedGoals.map(g => g.name).join(', ')}!` : ''}

Next Steps:
${hints.nextSteps.map(s => `- ${s}`).join('\n')}

Suggestions:
${hints.suggestions.map(s => `- ${s}`).join('\n')}`
        }]
      };
    }

    case 'completeTask': {
      petriState.semanticHintsUsed++;
      
      let task = workflowData.entities.tasks[args.identifier];
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found.' }] };
      }

      const place = petriState.places[task.id];
      
      // Semantic completion based on current state
      const transitions = {
        'In Progress': 'Review',
        'Review': 'Testing',
        'Testing': 'Done'
      };
      
      const newState = transitions[place.state] || 'Done';
      place.state = newState;
      
      const hints = generateSemanticHints({ ...task, state: place.state, type: 'task' }, 'completed');
      const achievedGoals = checkGoalsAfterOperation();
      
      return {
        content: [{
          type: 'text',
          text: `✓ Advanced "${task.name}" to ${newState}
${achievedGoals.length > 0 ? `\n🎯 GOALS ACHIEVED: ${achievedGoals.map(g => g.name).join(', ')}!` : ''}

${newState === 'Done' ? '🎉 Task completed!' : `Next Steps:\n${hints.nextSteps.map(s => `- ${s}`).join('\n')}`}

${hints.suggestions.length > 0 ? `\nSuggestions:\n${hints.suggestions.map(s => `- ${s}`).join('\n')}` : ''}`
        }]
      };
    }

    case 'workOnBug': {
      petriState.semanticHintsUsed++;
      
      let bug = workflowData.entities.bugs[args.identifier];
      if (!bug) {
        return { content: [{ type: 'text', text: 'Bug not found.' }] };
      }

      const place = petriState.places[bug.id];
      
      // Auto-assign if needed
      if (!place.assignee) {
        place.assignee = 'user-alice';
      }
      
      // Move to In Progress if New or Assigned
      if (place.state === 'New' || place.state === 'Assigned') {
        place.state = 'In Progress';
      }
      
      return {
        content: [{
          type: 'text',
          text: `✓ Working on bug: "${bug.name}"
State: ${place.state}
Assigned to: ${place.assignee}
Severity: ${bug.severity}

Next Steps:
- Investigate the issue
- Implement a fix
- Mark as fixed when done

Suggestions:
- fixBug('${bug.id}')
- updateEntity('${bug.id}', 'Fixed')
- addComment('${bug.id}', 'Found root cause...')`
        }]
      };
    }

    case 'checkWorkflow': {
      const activeItems = Object.entries(petriState.places)
        .filter(([id, place]) => place.state !== 'Done' && place.state !== 'Closed')
        .map(([id, place]) => {
          const entity = workflowData.entities.tasks[id] || workflowData.entities.bugs[id];
          return { id, name: entity?.name, state: place.state, assignee: place.assignee };
        });

      return {
        content: [{
          type: 'text',
          text: `Current Workflow State (Petri Net):

Active Work Items:
${activeItems.map(item => 
  `- ${item.id}: ${item.name} (${item.state}${item.assignee ? `, ${item.assignee}` : ''})`
).join('\n')}

Available Actions:
${activeItems.slice(0, 3).map(item => {
  if (item.state === 'Open') return `- startWorkingOn('${item.id}')`;
  if (item.state === 'In Progress') return `- completeTask('${item.id}')`;
  if (item.state === 'Review') return `- updateEntity('${item.id}', 'Testing')`;
  return `- getEntity('${item.id}')`;
}).join('\n')}

💡 Petri Net Advantage: You can work on multiple items concurrently!`
        }]
      };
    }

    case 'getEntity': {
      const entity = workflowData.entities.tasks[args.entityId] || 
                    workflowData.entities.bugs[args.entityId];
      
      if (!entity) {
        return { content: [{ type: 'text', text: 'Entity not found.' }] };
      }

      const place = petriState.places[args.entityId];
      const hints = generateSemanticHints({ ...entity, state: place.state, type: entity.severity ? 'bug' : 'task' });

      return {
        content: [{
          type: 'text',
          text: `Entity: ${entity.name}
Type: ${entity.severity ? 'Bug' : 'Task'}
State: ${place.state}
Assignee: ${place.assignee || 'None'}

Next Steps:
${hints.nextSteps.map(s => `- ${s}`).join('\n')}

Suggestions:
${hints.suggestions.map(s => `- ${s}`).join('\n')}`
        }]
      };
    }

    case 'updateEntity': {
      const place = petriState.places[args.entityId];
      if (!place) {
        return { content: [{ type: 'text', text: 'Entity not found.' }] };
      }

      place.state = args.newState;
      const achievedGoals = checkGoalsAfterOperation();

      return {
        content: [{
          type: 'text',
          text: `✓ Updated entity ${args.entityId} to ${args.newState}
${achievedGoals.length > 0 ? `\n🎯 GOALS ACHIEVED: ${achievedGoals.map(g => g.name).join(', ')}!` : ''}

💡 Petri Net: This state change may enable new transitions in connected workflow items.`
        }]
      };
    }

    case 'checkGoals': {
      const achieved = petriState.goalsFound;
      const total = workflowData.goals.length;
      
      return {
        content: [{
          type: 'text',
          text: `Goals Progress: ${achieved.length}/${total}
Tool Calls Made: ${petriState.toolCallCount}
Semantic Hints Used: ${petriState.semanticHintsUsed}
Goals Achieved: ${achieved.join(', ') || 'None yet'}

Petri Net Advantage: Multiple paths to reach goals!`
        }]
      };
    }

    case 'getMetrics': {
      return {
        content: [{
          type: 'text',
          text: `Petri Net Navigator Metrics:
- Tool calls: ${petriState.toolCallCount}
- Goals found: ${petriState.goalsFound.length}
- Semantic hints used: ${petriState.semanticHintsUsed}
- Efficiency: ${petriState.goalsFound.length > 0 ? 
    (petriState.toolCallCount / petriState.goalsFound.length).toFixed(1) + ' calls per goal' : 
    'No goals yet'}
- Semantic usage rate: ${((petriState.semanticHintsUsed / petriState.toolCallCount) * 100).toFixed(0)}%`
        }]
      };
    }

    default:
      return {
        content: [{ type: 'text', text: `Unknown tool: ${name}` }]
      };
  }
});

// Start the server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('Petri Net Workflow Navigator MCP Server running...');