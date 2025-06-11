#!/usr/bin/env python3
"""
FSM Workflow Navigator
Demonstrates traditional hierarchical navigation constraints
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP

# Load workflow datasets
import os
import sys
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='FSM Workflow Navigator')
parser.add_argument('dataset', nargs='?', 
                   default='../workflow-dataset.json',
                   help='Path to dataset JSON file (default: ../workflow-dataset.json)')

args = parser.parse_args()

# Load dataset from provided path
dataset_path = Path(args.dataset)
if not dataset_path.is_absolute():
    # If relative, resolve from navigator directory
    dataset_path = Path(__file__).parent.joinpath(dataset_path).resolve()

if not dataset_path.exists():
    print(f"Dataset file not found: {dataset_path}")
    sys.exit(1)

WORKFLOW_DATA = json.loads(dataset_path.read_text())
DATASET_NAME = dataset_path.stem  # Use filename without extension for display

print(f"FSM Navigator loaded with {DATASET_NAME} dataset", file=sys.stderr)

# Create MCP server
mcp = FastMCP("fsm-workflow-navigator")

# FSM State - single current location
class FSMState:
    def __init__(self):
        self.location = 'root'
        self.context = {}
        self.tool_call_count = 0
        self.goals_found = []

# Global state instance
fsm_state = FSMState()

def check_goals_after_operation():
    """Check if any goals were achieved"""
    achieved_goals = []
    
    if 'goals' not in WORKFLOW_DATA:
        return achieved_goals
    
    for goal in WORKFLOW_DATA['goals']:
        if goal['id'] in fsm_state.goals_found:
            continue
            
        if 'entity' in goal['condition']:
            entity_id = goal['condition']['entity']
            target_state = goal['condition']['state']
            
            entity = WORKFLOW_DATA['entities']['tasks'].get(entity_id) or \
                     WORKFLOW_DATA['entities']['bugs'].get(entity_id)
            
            if entity and entity['state'] == target_state:
                fsm_state.goals_found.append(goal['id'])
                achieved_goals.append(goal)
    
    return achieved_goals

# Define MCP tools
@mcp.tool()
def listProjects() -> str:
    """List all projects (FSM: always start here)"""
    fsm_state.tool_call_count += 1
    fsm_state.location = 'projects'
    
    projects = list(WORKFLOW_DATA['entities']['projects'].values())
    
    project_list = '\n'.join([f"- {p['id']}: {p['name']} ({p['state']})" for p in projects])
    
    return (f"Projects ({len(projects)}):\n{project_list}\n\n"
            f"FSM: You are now at projects level. Use getProject to navigate to a specific project.")

@mcp.tool()
def getProject(projectId: str) -> str:
    """Get project details and navigate to it"""
    fsm_state.tool_call_count += 1
    
    project = WORKFLOW_DATA['entities']['projects'].get(projectId)
    if not project:
        return "Project not found. Use listProjects first."
    
    fsm_state.location = projectId
    fsm_state.context['currentProject'] = projectId
    
    return (f"Project: {project['name']}\n"
            f"State: {project['state']}\n"
            f"Tasks: {len(project['tasks'])}\n"
            f"Bugs: {len(project['bugs'])}\n\n"
            f"FSM: You are now in project {project['name']}. Use listTasks or listBugs to see items.")

@mcp.tool()
def listTasks(projectId: str) -> str:
    """List tasks in current project"""
    fsm_state.tool_call_count += 1
    
    if fsm_state.location == 'root':
        return "FSM Error: Must navigate to project first. Use listProjects."
    
    project = WORKFLOW_DATA['entities']['projects'].get(projectId)
    if not project:
        return "Project not found."
    
    tasks = [WORKFLOW_DATA['entities']['tasks'][tid] for tid in project['tasks']]
    task_list = '\n'.join([
        f"- {t['id']}: {t['name']} ({t['state']}{', assigned to ' + t['assignee'] if t.get('assignee') else ''})"
        for t in tasks
    ])
    
    return (f"Tasks in {project['name']}:\n{task_list}\n\n"
            f"FSM: Use getTask to navigate to a specific task.")

@mcp.tool()
def listBugs(projectId: str) -> str:
    """List bugs in current project"""
    fsm_state.tool_call_count += 1
    
    if fsm_state.location == 'root':
        return "FSM Error: Must navigate to project first. Use listProjects."
    
    project = WORKFLOW_DATA['entities']['projects'].get(projectId)
    if not project:
        return "Project not found."
    
    bugs = [WORKFLOW_DATA['entities']['bugs'][bid] for bid in project['bugs']]
    bug_list = '\n'.join([
        f"- {b['id']}: {b['name']} ({b['state']}{', assigned to ' + b['assignee'] if b.get('assignee') else ''})"
        for b in bugs
    ])
    
    return (f"Bugs in {project['name']}:\n{bug_list}\n\n"
            f"FSM: Use getBug to navigate to a specific bug.")

@mcp.tool()
def getTask(taskId: str) -> str:
    """Get task details and navigate to it"""
    fsm_state.tool_call_count += 1
    
    task = WORKFLOW_DATA['entities']['tasks'].get(taskId)
    if not task:
        return "Task not found. Use listTasks first."
    
    fsm_state.location = taskId
    fsm_state.context['currentTask'] = taskId
    
    return (f"Task: {task['name']}\n"
            f"ID: {task['id']}\n"
            f"State: {task['state']}\n"
            f"Assignee: {task.get('assignee', 'None')}\n"
            f"Valid Transitions: {task['validTransitions']}\n\n"
            f"FSM: You are now at task {task['name']}. You can updateTaskState or assignTask.")

@mcp.tool()
def getBug(bugId: str) -> str:
    """Get bug details and navigate to it"""
    fsm_state.tool_call_count += 1
    
    bug = WORKFLOW_DATA['entities']['bugs'].get(bugId)
    if not bug:
        return "Bug not found. Use listBugs first."
    
    fsm_state.location = bugId
    fsm_state.context['currentBug'] = bugId
    
    return (f"Bug: {bug['name']}\n"
            f"ID: {bug['id']}\n"
            f"State: {bug['state']}\n"
            f"Assignee: {bug.get('assignee', 'None')}\n"
            f"Priority: {bug['priority']}\n"
            f"Valid States: {' → '.join(list(bug['validTransitions'].keys()))}\n\n"
            f"FSM: You are now at bug {bug['name']}. You can updateBugState or assignBug.")

@mcp.tool()
def getTaskState(taskId: str) -> str:
    """Check current state of a task"""
    fsm_state.tool_call_count += 1
    
    task = WORKFLOW_DATA['entities']['tasks'].get(taskId)
    if not task:
        return "Task not found."
    
    return f"Task \"{task['name']}\" is currently in state: {task['state']}"

@mcp.tool()
def updateTaskState(taskId: str, newState: str) -> str:
    """Update task state (must be at task location)"""
    fsm_state.tool_call_count += 1
    
    if not fsm_state.location.startswith('task-'):
        return "FSM Error: Must be at task location. Use getTask first."
    
    task = WORKFLOW_DATA['entities']['tasks'].get(taskId)
    if not task:
        return "Task not found."
    
    # FSM requires checking valid transitions
    if newState not in list(task['validTransitions'].keys()):
        return f"Invalid state. Valid states: {', '.join(list(task['validTransitions'].keys()))}"
    
    task['state'] = newState
    achieved_goals = check_goals_after_operation()
    
    goals_text = ""
    if achieved_goals:
        goals_text = f"\n🎯 GOALS ACHIEVED: {', '.join(g['name'] for g in achieved_goals)}!"
    
    return (f"Task {task['name']} updated to {newState}.{goals_text}\n\n"
            f"FSM: Task state updated. Return to project to continue with other tasks.")

@mcp.tool()
def updateBugState(bugId: str, newState: str) -> str:
    """Update bug state (must be at bug location)"""
    fsm_state.tool_call_count += 1
    
    if not fsm_state.location.startswith('bug-'):
        return "FSM Error: Must be at bug location. Use getBug first."
    
    bug = WORKFLOW_DATA['entities']['bugs'].get(bugId)
    if not bug:
        return "Bug not found."
    
    if newState not in list(bug['validTransitions'].keys()):
        return f"Invalid state. Valid states: {', '.join(list(bug['validTransitions'].keys()))}"
    
    bug['state'] = newState
    achieved_goals = check_goals_after_operation()
    
    goals_text = ""
    if achieved_goals:
        goals_text = f"\n🎯 GOALS ACHIEVED: {', '.join(g['name'] for g in achieved_goals)}!"
    
    return (f"Bug {bug['name']} updated to {newState}.{goals_text}\n\n"
            f"FSM: Bug state updated. Return to project to continue.")

@mcp.tool()
def assignTask(taskId: str, userId: str) -> str:
    """Assign task to user"""
    fsm_state.tool_call_count += 1
    
    task = WORKFLOW_DATA['entities']['tasks'].get(taskId)
    if not task:
        return "Task not found. Use getTask first."
    
    task['assignee'] = userId
    
    return (f"Task {task['name']} assigned to {userId}.\n\n"
            f"FSM: Task assigned. Navigate elsewhere to continue.")

@mcp.tool()
def assignBug(bugId: str, userId: str) -> str:
    """Assign bug to user"""
    fsm_state.tool_call_count += 1
    
    bug = WORKFLOW_DATA['entities']['bugs'].get(bugId)
    if not bug:
        return "Bug not found. Use getBug first."
    
    bug['assignee'] = userId
    
    return (f"Bug {bug['name']} assigned to {userId}.\n\n"
            f"FSM: Bug assigned. Navigate elsewhere to continue.")

@mcp.tool()
def navigateToRoot() -> str:
    """Return to root location"""
    fsm_state.tool_call_count += 1
    
    fsm_state.location = 'root'
    fsm_state.context = {}
    
    return ("Returned to root.\n\n"
            "FSM: You must use listProjects to start navigation again.")

@mcp.tool()
def checkGoals() -> str:
    """Check which goals have been achieved"""
    fsm_state.tool_call_count += 1
    
    if 'goals' not in WORKFLOW_DATA:
        return "No goals defined in current dataset"
    
    completed = []
    total_points = 0
    
    for goal in WORKFLOW_DATA['goals']:
        if 'entity' in goal['condition']:
            entity_id = goal['condition']['entity']
            target_state = goal['condition']['state']
            
            entity = WORKFLOW_DATA['entities']['tasks'].get(entity_id) or \
                     WORKFLOW_DATA['entities']['bugs'].get(entity_id)
            
            if entity and entity['state'] == target_state:
                completed.append(f"✓ {goal['name']} ({goal['points']} points)")
                total_points += goal['points']
    
    completed_text = '\n'.join(completed) if completed else 'No goals completed yet'
    
    return (f"Goals Status:\n{completed_text}\n\n"
            f"Total Points: {total_points}/800\n"
            f"Goals Found by FSM: {len(fsm_state.goals_found)}")

@mcp.tool()
def getMetrics() -> str:
    """Get FSM navigation metrics"""
    fsm_state.tool_call_count += 1
    
    efficiency = "No goals yet"
    if fsm_state.goals_found:
        efficiency = f"{fsm_state.tool_call_count / len(fsm_state.goals_found):.1f} calls per goal"
    
    return (f"FSM Navigator Metrics:\n"
            f"- Tool calls: {fsm_state.tool_call_count}\n"
            f"- Goals found: {len(fsm_state.goals_found)}\n"
            f"- Current location: {fsm_state.location}\n"
            f"- Efficiency: {efficiency}")

# Additional tools for dataset compatibility

@mcp.tool()
def listWorkflow() -> str:
    """List all workflow items (FSM equivalent)"""
    fsm_state.tool_call_count += 1
    
    if fsm_state.location != 'root':
        return "FSM Error: Must be at root. Use navigateToRoot first."
    
    items = []
    
    # Must navigate through hierarchy to gather info
    for project_id, project in WORKFLOW_DATA['entities']['projects'].items():
        items.append(f"[PROJECT] {project_id}: {project['name']}")
        
        for task_id in project.get('tasks', []):
            task = WORKFLOW_DATA['entities']['tasks'].get(task_id, {})
            items.append(f"  [TASK] {task_id}: {task.get('name', 'Unknown')}")
            
        for bug_id in project.get('bugs', []):
            bug = WORKFLOW_DATA['entities']['bugs'].get(bug_id, {})
            items.append(f"  [BUG] {bug_id}: {bug.get('name', 'Unknown')}")
    
    return ("\n".join(items) + "\n\n"
            "FSM: Items shown but not accessible without navigation")

@mcp.tool()
def startWorkingOn(identifier: str) -> str:
    """Start working on task/bug (FSM must navigate first)"""
    fsm_state.tool_call_count += 1
    
    # FSM cannot do direct access - must be at the entity location
    if not fsm_state.location.startswith(identifier):
        return (f"FSM Error: Must navigate to {identifier} first.\n"
                f"Current location: {fsm_state.location}\n"
                f"Use getProject → getTask/getBug sequence.")
    
    # Determine entity type and get it
    if identifier.startswith('task-'):
        entity = WORKFLOW_DATA['entities']['tasks'].get(identifier)
        entity_type = 'task'
    elif identifier.startswith('bug-'):
        entity = WORKFLOW_DATA['entities']['bugs'].get(identifier)
        entity_type = 'bug'
    else:
        return f"FSM Error: Unknown entity type for {identifier}"
    
    if not entity:
        return f"FSM Error: {identifier} not found"
    
    current_state = entity['state']
    
    # FSM tries to follow the state machine logic
    valid_transitions = entity.get('validTransitions', {})
    possible_next = valid_transitions.get(current_state, [])
    
    if not possible_next:
        return f"FSM Error: No valid transitions from {current_state}"
    
    # Pick first available transition (FSM limitation - no semantic understanding)
    next_state = possible_next[0]
    entity['state'] = next_state
    
    return (f"Started working on {entity['name']}\n"
            f"State: {current_state} → {next_state}\n"
            f"FSM: Mechanical state transition without semantic understanding")

@mcp.tool()
def completeItem(entityId: str) -> str:
    """Complete a task or bug (FSM must navigate manually)"""
    fsm_state.tool_call_count += 1
    
    if not fsm_state.location.startswith(entityId):
        return f"FSM Error: Must navigate to {entityId} first"
    
    # FSM has to manually step through all states to completion
    entity = (WORKFLOW_DATA['entities']['tasks'].get(entityId) or 
              WORKFLOW_DATA['entities']['bugs'].get(entityId))
    
    if not entity:
        return f"FSM Error: {entityId} not found"
    
    current_state = entity['state']
    valid_transitions = entity.get('validTransitions', {})
    
    # FSM must manually traverse to find completion
    steps = 0
    path = [current_state]
    
    while steps < 10:  # Prevent infinite loops
        possible_next = valid_transitions.get(current_state, [])
        if not possible_next:
            break
            
        # Look for a "completion-like" state
        completion_states = ['Done', 'Completed', 'Verified', 'Closed', 'Finished']
        next_state = None
        
        for state in completion_states:
            if state in possible_next:
                next_state = state
                break
        
        if not next_state:
            next_state = possible_next[0]  # Just pick first available
        
        current_state = next_state
        path.append(current_state)
        steps += 1
        
        if current_state in completion_states:
            break
    
    entity['state'] = current_state
    
    return (f"Completed {entity['name']} (attempted)\n"
            f"Path: {' → '.join(path)}\n"
            f"Steps: {steps}\n"
            f"FSM: Manual state traversal - may not reach true completion")

@mcp.tool()
def updateState(entityId: str, newState: str) -> str:
    """Update entity state (FSM equivalent)"""
    return updateTaskState(entityId, newState) if entityId.startswith('task-') else updateBugState(entityId, newState)

@mcp.tool()
def showMetrics() -> str:
    """Show metrics (alias for getMetrics)"""
    return getMetrics()

if __name__ == "__main__":
    mcp.run()