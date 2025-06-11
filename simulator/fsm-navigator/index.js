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

// FSM State - single current location
let currentState = {
  location: 'root',
  context: {},
  toolCallCount: 0,
  goalsFound: []
};

// FSM Navigation - strict hierarchy
const server = new Server(
  {
    name: 'fsm-workflow-navigator',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool: List all projects (always start here in FSM)
server.setRequestHandler('tools/list', async () => ({
  tools: [
    {
      name: 'listProjects',
      description: 'List all projects',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'getProject',
      description: 'Get project details',
      inputSchema: {
        type: 'object',
        properties: {
          projectId: { type: 'string' },
        },
        required: ['projectId'],
      },
    },
    {
      name: 'listTasks',
      description: 'List tasks in a project',
      inputSchema: {
        type: 'object',
        properties: {
          projectId: { type: 'string' },
        },
        required: ['projectId'],
      },
    },
    {
      name: 'getTask',
      description: 'Get task details',
      inputSchema: {
        type: 'object',
        properties: {
          taskId: { type: 'string' },
        },
        required: ['taskId'],
      },
    },
    {
      name: 'listBugs',
      description: 'List bugs in a project',
      inputSchema: {
        type: 'object',
        properties: {
          projectId: { type: 'string' },
        },
        required: ['projectId'],
      },
    },
    {
      name: 'getBug',
      description: 'Get bug details',
      inputSchema: {
        type: 'object',
        properties: {
          bugId: { type: 'string' },
        },
        required: ['bugId'],
      },
    },
    {
      name: 'updateTaskState',
      description: 'Update task state',
      inputSchema: {
        type: 'object',
        properties: {
          taskId: { type: 'string' },
          newState: { type: 'string' },
        },
        required: ['taskId', 'newState'],
      },
    },
    {
      name: 'assignTask',
      description: 'Assign task to user',
      inputSchema: {
        type: 'object',
        properties: {
          taskId: { type: 'string' },
          userId: { type: 'string' },
        },
        required: ['taskId', 'userId'],
      },
    },
    {
      name: 'updateBugState',
      description: 'Update bug state',
      inputSchema: {
        type: 'object',
        properties: {
          bugId: { type: 'string' },
          newState: { type: 'string' },
        },
        required: ['bugId', 'newState'],
      },
    },
    {
      name: 'assignBug',
      description: 'Assign bug to user',
      inputSchema: {
        type: 'object',
        properties: {
          bugId: { type: 'string' },
          userId: { type: 'string' },
        },
        required: ['bugId', 'userId'],
      },
    },
    {
      name: 'checkGoals',
      description: 'Check if any goals have been achieved',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'getMetrics',
      description: 'Get current navigation metrics',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
  ],
}));

// Tool implementations following FSM pattern
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;
  currentState.toolCallCount++;

  // Check goals after each operation
  const checkGoalsAfterOperation = () => {
    const newGoals = [];
    for (const goal of workflowData.goals) {
      if (currentState.goalsFound.includes(goal.id)) continue;
      
      // Check if goal condition is met
      if (goal.condition.entity) {
        const entity = workflowData.entities.tasks[goal.condition.entity] || 
                      workflowData.entities.bugs[goal.condition.entity];
        if (entity && entity.state === goal.condition.state) {
          newGoals.push(goal);
        }
      }
    }
    
    if (newGoals.length > 0) {
      currentState.goalsFound.push(...newGoals.map(g => g.id));
      return newGoals;
    }
    return [];
  };

  switch (name) {
    case 'listProjects': {
      currentState.location = 'projects';
      const projects = Object.values(workflowData.entities.projects);
      return {
        content: [{
          type: 'text',
          text: `Found ${projects.length} projects:\n${projects.map(p => 
            `- ${p.id}: ${p.name} (${p.state})`
          ).join('\n')}\n\nFSM: You must now select a project to continue.`
        }]
      };
    }

    case 'getProject': {
      const project = workflowData.entities.projects[args.projectId];
      if (!project) {
        return { content: [{ type: 'text', text: 'Project not found. Try listProjects first.' }] };
      }
      currentState.location = `project:${args.projectId}`;
      currentState.context.currentProject = args.projectId;
      
      return {
        content: [{
          type: 'text',
          text: `Project: ${project.name}
State: ${project.state}
Tasks: ${project.tasks.length}
Bugs: ${project.bugs.length}

FSM: You can now list tasks or bugs for this project.`
        }]
      };
    }

    case 'listTasks': {
      if (!currentState.context.currentProject) {
        return { content: [{ type: 'text', text: 'No project selected. Use getProject first.' }] };
      }
      
      const project = workflowData.entities.projects[args.projectId];
      const tasks = project.tasks.map(tid => workflowData.entities.tasks[tid]);
      
      currentState.location = `project:${args.projectId}:tasks`;
      
      return {
        content: [{
          type: 'text',
          text: `Tasks in ${project.name}:\n${tasks.map(t => 
            `- ${t.id}: ${t.name} (${t.state}${t.assignee ? `, assigned to ${t.assignee}` : ', unassigned'})`
          ).join('\n')}\n\nFSM: Select a task to view or modify.`
        }]
      };
    }

    case 'getTask': {
      const task = workflowData.entities.tasks[args.taskId];
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found.' }] };
      }
      
      currentState.location = `task:${args.taskId}`;
      currentState.context.currentTask = args.taskId;
      
      return {
        content: [{
          type: 'text',
          text: `Task: ${task.name}
ID: ${task.id}
State: ${task.state}
Assignee: ${task.assignee || 'None'}
Valid States: ${task.validStates.join(', ')}

FSM: You can now update state or assign this task.`
        }]
      };
    }

    case 'updateTaskState': {
      const task = workflowData.entities.tasks[args.taskId];
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found. Use getTask first.' }] };
      }
      
      // FSM requires checking valid transitions
      if (!task.validStates.includes(args.newState)) {
        return { content: [{ type: 'text', text: `Invalid state. Valid states: ${task.validStates.join(', ')}` }] };
      }
      
      task.state = args.newState;
      const achievedGoals = checkGoalsAfterOperation();
      
      return {
        content: [{
          type: 'text',
          text: `Task ${task.name} updated to ${args.newState}.
${achievedGoals.length > 0 ? `\n🎯 GOALS ACHIEVED: ${achievedGoals.map(g => g.name).join(', ')}!` : ''}

FSM: Task state updated. Return to project to continue with other tasks.`
        }]
      };
    }

    case 'assignTask': {
      const task = workflowData.entities.tasks[args.taskId];
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found. Use getTask first.' }] };
      }
      
      task.assignee = args.userId;
      
      return {
        content: [{
          type: 'text',
          text: `Task ${task.name} assigned to ${args.userId}.

FSM: Task assigned. You may now update its state.`
        }]
      };
    }

    case 'checkGoals': {
      const achieved = currentState.goalsFound;
      const total = workflowData.goals.length;
      
      return {
        content: [{
          type: 'text',
          text: `Goals Progress: ${achieved.length}/${total}
Tool Calls Made: ${currentState.toolCallCount}
Goals Achieved: ${achieved.join(', ') || 'None yet'}

FSM State Machine currently at: ${currentState.location}`
        }]
      };
    }

    case 'getMetrics': {
      return {
        content: [{
          type: 'text',
          text: `FSM Navigator Metrics:
- Tool calls: ${currentState.toolCallCount}
- Goals found: ${currentState.goalsFound.length}
- Current location: ${currentState.location}
- Efficiency: ${currentState.goalsFound.length > 0 ? 
    (currentState.toolCallCount / currentState.goalsFound.length).toFixed(1) + ' calls per goal' : 
    'No goals yet'}`
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
console.error('FSM Workflow Navigator MCP Server running...');