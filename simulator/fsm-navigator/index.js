#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
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

// Check if goals are achieved after an operation
function checkGoalsAfterOperation() {
  const achievedGoals = [];
  
  for (const goal of workflowData.goals) {
    if (currentState.goalsFound.includes(goal.id)) continue;
    
    if (goal.condition.entity) {
      const entity = workflowData.entities.tasks[goal.condition.entity] || 
                     workflowData.entities.bugs[goal.condition.entity];
      
      if (entity && entity.state === goal.condition.state) {
        currentState.goalsFound.push(goal.id);
        achievedGoals.push(goal);
      }
    }
  }
  
  return achievedGoals;
}

// Create MCP server
const server = new McpServer({
  name: 'fsm-workflow-navigator',
  version: '1.0.0',
});

// Handler for tool listing
server.handleListTools(async () => {
  return {
    tools: [
      {
        name: 'listProjects',
        description: 'List all projects (FSM: always start here)',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        },
      },
      {
        name: 'getProject',
        description: 'Get project details and navigate to it',
        inputSchema: {
          type: 'object',
          properties: {
            projectId: { type: 'string', description: 'Project ID' }
          },
          required: ['projectId']
        },
      },
      {
        name: 'listTasks',
        description: 'List tasks in current project',
        inputSchema: {
          type: 'object',
          properties: {
            projectId: { type: 'string', description: 'Project ID' }
          },
          required: ['projectId']
        },
      },
      {
        name: 'listBugs',
        description: 'List bugs in current project',
        inputSchema: {
          type: 'object',
          properties: {
            projectId: { type: 'string', description: 'Project ID' }
          },
          required: ['projectId']
        },
      },
      {
        name: 'getTask',
        description: 'Get task details and navigate to it',
        inputSchema: {
          type: 'object',
          properties: {
            taskId: { type: 'string', description: 'Task ID' }
          },
          required: ['taskId']
        },
      },
      {
        name: 'getBug',
        description: 'Get bug details and navigate to it',
        inputSchema: {
          type: 'object',
          properties: {
            bugId: { type: 'string', description: 'Bug ID' }
          },
          required: ['bugId']
        },
      },
      {
        name: 'getTaskState',
        description: 'Check current state of a task',
        inputSchema: {
          type: 'object',
          properties: {
            taskId: { type: 'string', description: 'Task ID' }
          },
          required: ['taskId']
        },
      },
      {
        name: 'updateTaskState',
        description: 'Update task state (must be at task location)',
        inputSchema: {
          type: 'object',
          properties: {
            taskId: { type: 'string', description: 'Task ID' },
            newState: { type: 'string', description: 'New state' }
          },
          required: ['taskId', 'newState']
        },
      },
      {
        name: 'updateBugState',
        description: 'Update bug state (must be at bug location)',
        inputSchema: {
          type: 'object',
          properties: {
            bugId: { type: 'string', description: 'Bug ID' },
            newState: { type: 'string', description: 'New state' }
          },
          required: ['bugId', 'newState']
        },
      },
      {
        name: 'assignTask',
        description: 'Assign task to user',
        inputSchema: {
          type: 'object',
          properties: {
            taskId: { type: 'string', description: 'Task ID' },
            userId: { type: 'string', description: 'User ID' }
          },
          required: ['taskId', 'userId']
        },
      },
      {
        name: 'assignBug',
        description: 'Assign bug to user',
        inputSchema: {
          type: 'object',
          properties: {
            bugId: { type: 'string', description: 'Bug ID' },
            userId: { type: 'string', description: 'User ID' }
          },
          required: ['bugId', 'userId']
        },
      },
      {
        name: 'navigateToRoot',
        description: 'Return to root location',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        },
      },
      {
        name: 'checkGoals',
        description: 'Check which goals have been achieved',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        },
      },
      {
        name: 'getMetrics',
        description: 'Get FSM navigation metrics',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        },
      }
    ],
  };
});

// Handler for tool execution
server.handleCallTool(async (request) => {
  const { name, arguments: args } = request;
  currentState.toolCallCount++;
  
  switch (name) {
    case 'listProjects': {
      currentState.location = 'projects';
      const projects = Object.values(workflowData.entities.projects);
      
      return {
        content: [{
          type: 'text',
          text: `Projects (${projects.length}):
${projects.map(p => `- ${p.id}: ${p.name} (${p.state})`).join('\n')}

FSM: You are now at projects level. Use getProject to navigate to a specific project.`
        }]
      };
    }

    case 'getProject': {
      const project = workflowData.entities.projects[args.projectId];
      if (!project) {
        return { content: [{ type: 'text', text: 'Project not found. Use listProjects first.' }] };
      }
      
      currentState.location = args.projectId;
      currentState.context.currentProject = args.projectId;
      
      return {
        content: [{
          type: 'text',
          text: `Project: ${project.name}
State: ${project.state}
Tasks: ${project.tasks.length}
Bugs: ${project.bugs.length}

FSM: You are now in project ${project.name}. Use listTasks or listBugs to see items.`
        }]
      };
    }

    case 'listTasks': {
      if (currentState.location === 'root') {
        return { content: [{ type: 'text', text: 'FSM Error: Must navigate to project first. Use listProjects.' }] };
      }
      
      const project = workflowData.entities.projects[args.projectId];
      if (!project) {
        return { content: [{ type: 'text', text: 'Project not found.' }] };
      }
      
      const tasks = project.tasks.map(tid => workflowData.entities.tasks[tid]);
      
      return {
        content: [{
          type: 'text',
          text: `Tasks in ${project.name}:
${tasks.map(t => `- ${t.id}: ${t.name} (${t.state}${t.assignee ? `, assigned to ${t.assignee}` : ''})`).join('\n')}

FSM: Use getTask to navigate to a specific task.`
        }]
      };
    }

    case 'listBugs': {
      if (currentState.location === 'root') {
        return { content: [{ type: 'text', text: 'FSM Error: Must navigate to project first. Use listProjects.' }] };
      }
      
      const project = workflowData.entities.projects[args.projectId];
      if (!project) {
        return { content: [{ type: 'text', text: 'Project not found.' }] };
      }
      
      const bugs = project.bugs.map(bid => workflowData.entities.bugs[bid]);
      
      return {
        content: [{
          type: 'text',
          text: `Bugs in ${project.name}:
${bugs.map(b => `- ${b.id}: ${b.name} (${b.state}${b.assignee ? `, assigned to ${b.assignee}` : ''})`).join('\n')}

FSM: Use getBug to navigate to a specific bug.`
        }]
      };
    }

    case 'getTask': {
      const task = workflowData.entities.tasks[args.taskId];
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found. Use listTasks first.' }] };
      }
      
      currentState.location = args.taskId;
      currentState.context.currentTask = args.taskId;
      
      return {
        content: [{
          type: 'text',
          text: `Task: ${task.name}
ID: ${task.id}
State: ${task.state}
Assignee: ${task.assignee || 'None'}
Valid States: ${task.validStates.join(' → ')}

FSM: You are now at task ${task.name}. You can updateTaskState or assignTask.`
        }]
      };
    }

    case 'getBug': {
      const bug = workflowData.entities.bugs[args.bugId];
      if (!bug) {
        return { content: [{ type: 'text', text: 'Bug not found. Use listBugs first.' }] };
      }
      
      currentState.location = args.bugId;
      currentState.context.currentBug = args.bugId;
      
      return {
        content: [{
          type: 'text',
          text: `Bug: ${bug.name}
ID: ${bug.id}
State: ${bug.state}
Assignee: ${bug.assignee || 'None'}
Priority: ${bug.priority}
Valid States: ${bug.validStates.join(' → ')}

FSM: You are now at bug ${bug.name}. You can updateBugState or assignBug.`
        }]
      };
    }

    case 'getTaskState': {
      const task = workflowData.entities.tasks[args.taskId];
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found.' }] };
      }
      
      return {
        content: [{
          type: 'text',
          text: `Task "${task.name}" is currently in state: ${task.state}`
        }]
      };
    }

    case 'updateTaskState': {
      if (!currentState.location.startsWith('task-')) {
        return { content: [{ type: 'text', text: 'FSM Error: Must be at task location. Use getTask first.' }] };
      }
      
      const task = workflowData.entities.tasks[args.taskId];
      if (!task) {
        return { content: [{ type: 'text', text: 'Task not found.' }] };
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

    case 'updateBugState': {
      if (!currentState.location.startsWith('bug-')) {
        return { content: [{ type: 'text', text: 'FSM Error: Must be at bug location. Use getBug first.' }] };
      }
      
      const bug = workflowData.entities.bugs[args.bugId];
      if (!bug) {
        return { content: [{ type: 'text', text: 'Bug not found.' }] };
      }
      
      if (!bug.validStates.includes(args.newState)) {
        return { content: [{ type: 'text', text: `Invalid state. Valid states: ${bug.validStates.join(', ')}` }] };
      }
      
      bug.state = args.newState;
      const achievedGoals = checkGoalsAfterOperation();
      
      return {
        content: [{
          type: 'text',
          text: `Bug ${bug.name} updated to ${args.newState}.
${achievedGoals.length > 0 ? `\n🎯 GOALS ACHIEVED: ${achievedGoals.map(g => g.name).join(', ')}!` : ''}

FSM: Bug state updated. Return to project to continue.`
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

FSM: Task assigned. Navigate elsewhere to continue.`
        }]
      };
    }

    case 'assignBug': {
      const bug = workflowData.entities.bugs[args.bugId];
      if (!bug) {
        return { content: [{ type: 'text', text: 'Bug not found. Use getBug first.' }] };
      }
      
      bug.assignee = args.userId;
      
      return {
        content: [{
          type: 'text',
          text: `Bug ${bug.name} assigned to ${args.userId}.

FSM: Bug assigned. Navigate elsewhere to continue.`
        }]
      };
    }

    case 'navigateToRoot': {
      currentState.location = 'root';
      currentState.context = {};
      
      return {
        content: [{
          type: 'text',
          text: `Returned to root. 

FSM: You must use listProjects to start navigation again.`
        }]
      };
    }

    case 'checkGoals': {
      const completed = [];
      let totalPoints = 0;
      
      for (const goal of workflowData.goals) {
        if (goal.condition.entity) {
          const entity = workflowData.entities.tasks[goal.condition.entity] || 
                         workflowData.entities.bugs[goal.condition.entity];
          
          if (entity && entity.state === goal.condition.state) {
            completed.push(`✓ ${goal.name} (${goal.points} points)`);
            totalPoints += goal.points;
          }
        }
      }
      
      return {
        content: [{
          type: 'text',
          text: `Goals Status:
${completed.length > 0 ? completed.join('\n') : 'No goals completed yet'}

Total Points: ${totalPoints}/800
Goals Found by FSM: ${currentState.goalsFound.length}`
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

// Run the server
async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('FSM Workflow Navigator MCP Server running...');
}

run().catch(console.error);