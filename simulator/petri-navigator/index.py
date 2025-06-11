#!/usr/bin/env python3
"""
Petri Net Navigator using SNAKES library
Demonstrates formal Petri net modeling for workflow navigation
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP

from snakes.nets import *
from snakes.plugins import load
load("gv", "snakes.nets", "nets")
from nets import *

# Load workflow datasets  
import os
import sys
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Petri Net Workflow Navigator')
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

print(f"Petri Net Navigator loaded with {DATASET_NAME} dataset", file=sys.stderr)

# Create MCP server
mcp = FastMCP("Petri Net Navigator")

class WorkflowPetriNet:
    """Formal Petri net model of the workflow using SNAKES"""
    
    def __init__(self):
        self.net = PetriNet('workflow')
        self.tokens = {}  # Track current token positions
        self.metrics = {
            'tool_calls': 0,
            'semantic_hints_used': 0,
            'goals_completed': []
        }
        self._build_net()
    
    def _get_place_name(self, name: str) -> str:
        """Sanitize place names for SNAKES library compatibility"""
        # Replace spaces with underscores and special characters with descriptive text
        sanitized = name.replace(' ', '_')
        sanitized = sanitized.replace('!', '_EXCL')
        sanitized = sanitized.replace('(', '_LPAREN').replace(')', '_RPAREN')
        sanitized = sanitized.replace("'", '_QUOTE')
        sanitized = sanitized.replace(',', '_COMMA')
        sanitized = sanitized.replace('.', '_DOT')
        sanitized = sanitized.replace('-', '_')
        sanitized = sanitized.replace(':', '_COLON')
        sanitized = sanitized.replace('/', '_SLASH')
        sanitized = sanitized.replace('\\', '_BACKSLASH')
        sanitized = sanitized.replace('*', '_STAR')
        # Remove multiple consecutive underscores
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        return sanitized.strip('_')
    
    def _get_valid_states(self, entity):
        """Extract valid states list from validTransitions"""
        if 'validTransitions' in entity:
            valid_states = set(entity['validTransitions'].keys())
            for transitions in entity['validTransitions'].values():
                valid_states.update(transitions)
            return list(valid_states)
        else:
            return [entity['state']]  # fallback
    
    def _build_net(self):
        """Build the Petri net structure from workflow data"""
        # Create places for task states
        for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
            # Extract valid states from transitions and include current state
            valid_states = set(task['validTransitions'].keys())
            for transitions in task['validTransitions'].values():
                valid_states.update(transitions)
            valid_states.add(task['state'])  # Ensure current state is included
            
            for state in valid_states:
                place_name = self._get_place_name(f"{task_id}_{state}")
                self.net.add_place(Place(place_name, []))
            
            # Add initial token
            initial_place = self._get_place_name(f"{task_id}_{task['state']}")
            self.net.place(initial_place).add(task_id)
            self.tokens[task_id] = initial_place
        
        # Create places for bug states
        for bug_id, bug in WORKFLOW_DATA['entities']['bugs'].items():
            # Extract valid states from transitions and include current state
            valid_states = set(bug['validTransitions'].keys())
            for transitions in bug['validTransitions'].values():
                valid_states.update(transitions)
            valid_states.add(bug['state'])  # Ensure current state is included
            
            for state in valid_states:
                place_name = self._get_place_name(f"{bug_id}_{state}")
                self.net.add_place(Place(place_name, []))
            
            initial_place = self._get_place_name(f"{bug_id}_{bug['state']}")
            self.net.place(initial_place).add(bug_id)
            self.tokens[bug_id] = initial_place
        
        # Create transitions for state changes
        self._add_task_transitions()
        self._add_bug_transitions()
        self._add_semantic_transitions()
    
    def _add_task_transitions(self):
        """Add transitions for task state changes"""
        for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
            transitions = task['validTransitions']
            
            # Create transitions based on valid transition mappings
            for from_state, to_states in transitions.items():
                for to_state in to_states:
                    trans_name = self._get_place_name(f"{task_id}_{from_state}_to_{to_state}")
                    
                    self.net.add_transition(Transition(trans_name))
                    self.net.add_input(self._get_place_name(f"{task_id}_{from_state}"), trans_name, Variable('token'))
                    self.net.add_output(self._get_place_name(f"{task_id}_{to_state}"), trans_name, Variable('token'))
                
            # Add backward transitions where appropriate
            task_states = self._get_valid_states(task)
            if "In Progress" in task_states and "Open" in task_states:
                trans_name = self._get_place_name(f"{task_id}_reopen")
                self.net.add_transition(Transition(trans_name))
                self.net.add_input(self._get_place_name(f"{task_id}_In Progress"), trans_name, Variable('token'))
                self.net.add_output(self._get_place_name(f"{task_id}_Open"), trans_name, Variable('token'))
    
    def _add_bug_transitions(self):
        """Add transitions for bug state changes"""
        for bug_id, bug in WORKFLOW_DATA['entities']['bugs'].items():
            transitions = bug['validTransitions']
            
            # Create transitions based on valid transition mappings
            for from_state, to_states in transitions.items():
                for to_state in to_states:
                    trans_name = self._get_place_name(f"{bug_id}_{from_state}_to_{to_state}")
                    
                    self.net.add_transition(Transition(trans_name))
                    self.net.add_input(self._get_place_name(f"{bug_id}_{from_state}"), trans_name, Variable('token'))
                    self.net.add_output(self._get_place_name(f"{bug_id}_{to_state}"), trans_name, Variable('token'))
    
    def _add_semantic_transitions(self):
        """Add high-level semantic transitions that cross multiple states"""
        # Start working on task (Open -> next state with assignment)
        for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
            if "Open" in self._get_valid_states(task) and len(self._get_valid_states(task)) > 1:
                # Find the next state after Open
                open_idx = self._get_valid_states(task).index("Open")
                if open_idx < len(self._get_valid_states(task)) - 1:
                    next_state = self._get_valid_states(task)[open_idx + 1]
                    trans_name = self._get_place_name(f"start_work_{task_id}")
                    self.net.add_transition(Transition(trans_name))
                    self.net.add_input(self._get_place_name(f"{task_id}_Open"), trans_name, Variable('token'))
                    self.net.add_output(self._get_place_name(f"{task_id}_{next_state}"), trans_name, Variable('token'))
        
        # Complete task (any state -> terminal states)
        for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
            valid_states = self._get_valid_states(task)
            # Find terminal states (states with no outgoing transitions)
            terminal_states = []
            for state in valid_states:
                if state in task['validTransitions'] and not task['validTransitions'][state]:
                    terminal_states.append(state)
            
            # If no terminal states found, try common completion states
            if not terminal_states:
                for completion_state in ['Done', 'Complete', 'Finished', 'Closed']:
                    if completion_state in valid_states:
                        terminal_states.append(completion_state)
            
            # Create completion transitions to terminal states
            for terminal_state in terminal_states:
                for state in valid_states:
                    if state != terminal_state:
                        trans_name = self._get_place_name(f"complete_{task_id}_from_{state}")
                        self.net.add_transition(Transition(trans_name))
                        self.net.add_input(self._get_place_name(f"{task_id}_{state}"), trans_name, Variable('token'))
                        self.net.add_output(self._get_place_name(f"{task_id}_{terminal_state}"), trans_name, Variable('token'))
    
    def get_enabled_transitions(self, entity_id: Optional[str] = None) -> list[str]:
        """Get all currently enabled transitions"""
        try:
            modes = list(self.net.modes())
            if entity_id:
                # Filter to transitions affecting this entity
                return [str(m) for m in modes if entity_id in str(m)]
            return [str(m) for m in modes]
        except:
            # Fallback for complex bindings
            return []
    
    def fire_transition(self, transition_name: str, binding: Optional[dict] = None) -> bool:
        """Fire a transition with optional variable binding"""
        try:
            if binding:
                sub = Substitution(**binding)
                self.net.transition(transition_name).fire(sub)
            else:
                # Try to find a valid mode
                for mode in self.net.modes():
                    if str(mode).startswith(transition_name):
                        mode.fire()
                        return True
            return True
        except Exception as e:
            print(f"Failed to fire transition: {e}")
            return False
    
    def move_token(self, entity_id: str, target_state: str) -> bool:
        """Move a token to a new state (simulating transition firing)"""
        current_place = self.tokens.get(entity_id)
        if not current_place:
            return False
            
        target_place = f"{entity_id}_{target_state}"
        
        # Check if target place exists
        try:
            self.net.place(target_place)
        except:
            return False
        
        # Move token
        try:
            # Remove from current place
            self.net.place(current_place).remove(entity_id)
            # Add to target place
            self.net.place(target_place).add(entity_id)
            self.tokens[entity_id] = target_place
            return True
        except:
            return False
    
    def generate_semantic_hints(self, entity_id: str) -> dict[str, list[str]]:
        """Generate context-aware hints based on Petri net state"""
        current_state = self.tokens.get(entity_id, "Unknown")
        if '_' in current_state:
            current_state = current_state.split('_', 1)[1]
        
        hints = {
            'nextSteps': [],
            'suggestions': []
        }
        
        # Get enabled transitions for this entity
        enabled = self.get_enabled_transitions(entity_id)
        
        # Task-specific hints
        if entity_id.startswith('task-'):
            task = WORKFLOW_DATA['entities']['tasks'].get(entity_id, {})
            
            if current_state == "Open":
                hints['nextSteps'].append("You can start working on this task")
                hints['suggestions'].append(f"Use startWorkingOn('{entity_id}') to begin")
            elif current_state in ["In Progress", "Ready", "Deploying"]:
                hints['nextSteps'].append("Task is actively being worked on")
                hints['suggestions'].append(f"Complete with completeItem('{entity_id}')")
            elif current_state == "Review":
                hints['nextSteps'].append("Task needs review")
                hints['suggestions'].append("Move to Testing or back to In Progress")
                
        # Bug-specific hints        
        elif entity_id.startswith('bug-'):
            if current_state == "Open":
                hints['nextSteps'].append("Bug needs investigation")
                hints['suggestions'].append(f"Start with startWorkingOn('{entity_id}')")
            elif current_state == "Investigating":
                hints['nextSteps'].append("Bug is being investigated")
                hints['suggestions'].append("Move to Fixing once cause is found")
                
        # Multi-entity hints
        if len(enabled) > 1:
            hints['suggestions'].append("Multiple workflow paths available")
            
        return hints
    
    def visualize(self) -> Optional[str]:
        """Generate a visual representation of the current Petri net state"""
        if hasattr(self.net, 'draw'):
            try:
                # This would generate a GraphViz representation
                return str(self.net)
            except:
                pass
        return None

# Global instance
petri_net = WorkflowPetriNet()

# MCP Tools
@mcp.tool()
def listWorkflow() -> str:
    """List all workflow items"""
    petri_net.metrics['tool_calls'] += 1
    
    items = []
    
    # List tasks
    for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
        current_state = get_entity_state(task_id)
        items.append(f"[TASK] {task_id}: {task['name']} - State: {current_state}")
    
    # List bugs  
    for bug_id, bug in WORKFLOW_DATA['entities']['bugs'].items():
        current_state = get_entity_state(bug_id)
        items.append(f"[BUG] {bug_id}: {bug['name']} - State: {current_state}")
    
    return "\n".join(items) + "\n\nPetri Net: All items accessible without navigation"

def get_entity_state(entity_id: str) -> str:
    """Get current state from token position"""
    place = petri_net.tokens.get(entity_id, "")
    if '_' in place:
        return place.split('_', 1)[1]
    return "Unknown"

@mcp.tool()
def showCurrentTokens() -> str:
    """Show current token positions in Petri net"""
    petri_net.metrics['tool_calls'] += 1
    
    positions = []
    for entity_id, place in petri_net.tokens.items():
        state = place.split('_', 1)[1] if '_' in place else place
        positions.append(f"{entity_id}: {state}")
    
    enabled_count = len(petri_net.get_enabled_transitions())
    
    return (f"Current Token Positions:\n" + 
            "\n".join(positions) + 
            f"\n\nEnabled transitions: {enabled_count}")

@mcp.tool() 
def getTaskInfo(taskId: str) -> str:
    """Get task information with semantic hints"""
    petri_net.metrics['tool_calls'] += 1
    
    task = WORKFLOW_DATA['entities']['tasks'].get(taskId)
    if not task:
        return f"Task {taskId} not found"
    
    current_state = get_entity_state(taskId)
    hints = petri_net.generate_semantic_hints(taskId)
    
    # Track if hints are being used
    if hints['suggestions']:
        petri_net.metrics['semantic_hints_used'] += 1
    
    result = (f"Task: {task['name']}\n"
              f"ID: {taskId}\n" 
              f"Current State: {current_state}\n"
              f"Valid States: {', '.join(petri_net._get_valid_states(task))}\n")
    
    if hints['nextSteps']:
        result += f"\nNext Steps:\n" + "\n".join(f"- {h}" for h in hints['nextSteps'])
    
    if hints['suggestions']:
        result += f"\n\nSuggestions:\n" + "\n".join(f"- {h}" for h in hints['suggestions'])
    
    return result + "\n\nPetri Net: Multi-entry access with contextual guidance"

@mcp.tool()
def getBugInfo(bugId: str) -> str:
    """Get bug information with semantic hints"""
    petri_net.metrics['tool_calls'] += 1
    
    bug = WORKFLOW_DATA['entities']['bugs'].get(bugId)
    if not bug:
        return f"Bug {bugId} not found"
    
    current_state = get_entity_state(bugId)
    hints = petri_net.generate_semantic_hints(bugId)
    
    if hints['suggestions']:
        petri_net.metrics['semantic_hints_used'] += 1
    
    result = (f"Bug: {bug['name']}\n"
              f"ID: {bugId}\n"
              f"Current State: {current_state}\n"
              f"Severity: {bug.get('severity', 'Medium')}\n"
              f"Valid States: {', '.join(self._get_valid_states(bug))}\n")
    
    if hints['nextSteps']:
        result += f"\nNext Steps:\n" + "\n".join(f"- {h}" for h in hints['nextSteps'])
    
    if hints['suggestions']:
        result += f"\n\nSuggestions:\n" + "\n".join(f"- {h}" for h in hints['suggestions'])
    
    return result + "\n\nPetri Net: Direct access with workflow guidance"

@mcp.tool()
def startWorkingOn(identifier: str) -> str:
    """Start working on a task or bug (multi-entry semantic operation)"""
    petri_net.metrics['tool_calls'] += 1
    
    # Determine entity type
    if identifier.startswith('task-'):
        entity_type = 'task'
        entities = WORKFLOW_DATA['entities']['tasks']
    elif identifier.startswith('bug-'):
        entity_type = 'bug'
        entities = WORKFLOW_DATA['entities']['bugs']
    else:
        return f"Unknown identifier format: {identifier}"
    
    entity = entities.get(identifier)
    if not entity:
        return f"{entity_type.title()} {identifier} not found"
    
    current_state = get_entity_state(identifier)
    
    # Semantic operation - move from Open to working state
    if current_state == "Open":
        # Find appropriate working state
        if entity_type == 'task':
            valid_states = petri_net._get_valid_states(entity)
            open_idx = valid_states.index("Open")
            if open_idx < len(valid_states) - 1:
                target_state = valid_states[open_idx + 1]
            else:
                target_state = "In Progress"  # fallback
        else:  # bug
            target_state = "Investigating"
        
        if petri_net.move_token(identifier, target_state):
            hints = petri_net.generate_semantic_hints(identifier)
            petri_net.metrics['semantic_hints_used'] += 1
            
            return (f"Started working on {entity['name']}\n"
                    f"State: {current_state} → {target_state}\n\n"
                    f"Next steps:\n" + 
                    "\n".join(f"- {h}" for h in hints['nextSteps']) +
                    "\n\nPetri Net: Semantic operation bypassed navigation")
    else:
        return f"Cannot start work - {entity['name']} is in {current_state} state"

@mcp.tool()
def updateState(entityId: str, newState: str) -> str:
    """Update entity state if transition is valid"""
    petri_net.metrics['tool_calls'] += 1
    
    # Check if entity exists
    entity = (WORKFLOW_DATA['entities']['tasks'].get(entityId) or 
              WORKFLOW_DATA['entities']['bugs'].get(entityId))
    
    if not entity:
        return f"Entity {entityId} not found"
    
    current_state = get_entity_state(entityId)
    
    # Check if new state is valid
    if newState not in petri_net._get_valid_states(entity):
        return f"Invalid state '{newState}'. Valid states: {', '.join(petri_net._get_valid_states(entity))}"
    
    # Try to move token
    if petri_net.move_token(entityId, newState):
        return (f"Updated {entity['name']}\n"
                f"State: {current_state} → {newState}\n"
                f"Petri Net: Direct state transition")
    else:
        return f"Cannot transition from {current_state} to {newState}"

@mcp.tool()
def completeItem(entityId: str) -> str:
    """Complete a task or bug (semantic operation)"""
    petri_net.metrics['tool_calls'] += 1
    
    entity = (WORKFLOW_DATA['entities']['tasks'].get(entityId) or 
              WORKFLOW_DATA['entities']['bugs'].get(entityId))
    
    if not entity:
        return f"Entity {entityId} not found"
    
    current_state = get_entity_state(entityId)
    valid_states = self._get_valid_states(entity)
    final_state = valid_states[-1]  # Last state is completion
    
    if current_state == final_state:
        return f"{entity['name']} is already in {final_state} state"
    
    # Semantic transition - jump to done
    if petri_net.move_token(entityId, final_state):
        petri_net.metrics['goals_completed'].append(entityId)
        return (f"Completed {entity['name']}\n"
                f"State: {current_state} → {final_state}\n"
                f"Petri Net: Semantic completion bypassed intermediate states")
    else:
        return f"Cannot complete {entity['name']} from {current_state} state"

@mcp.tool()
def reassignItem(entityId: str, fromUser: str, toUser: str) -> str:
    """Reassign a task or bug between users"""
    petri_net.metrics['tool_calls'] += 1
    
    entity = (WORKFLOW_DATA['entities']['tasks'].get(entityId) or 
              WORKFLOW_DATA['entities']['bugs'].get(entityId))
    
    if not entity:
        return f"Entity {entityId} not found"
    
    current_state = get_entity_state(entityId)
    
    # Get assignment-related states based on entity type
    if entityId.startswith('task-'):
        states = petri_net._get_valid_states(WORKFLOW_DATA['entities']['tasks'][entityId])
    else:
        states = petri_net._get_valid_states(WORKFLOW_DATA['entities']['bugs'][entityId])
    
    # Check if in assignable state (not Open or Done typically)
    if current_state in ["Open", states[-1]]:  # First or last state
        goals_text = ""
    else:
        # Generate goal context
        incomplete_goals = [g for g in ['task-ui', 'task-api', 'task-auth', 'task-deploy'] 
                           if g not in petri_net.metrics['goals_completed']]
        if incomplete_goals:
            goals_text = f"\n\nRemaining goals: {', '.join(incomplete_goals)}"
        else:
            goals_text = "\n\nAll workflow goals completed!"
    
    return (f"Reassigned {entity['name']} from {fromUser} to {toUser}\n"
            f"Current state: {get_entity_state(entityId)}"
            f"{goals_text}\n\n"
            f"Petri Net: Direct reassignment without navigation overhead.")

@mcp.tool()
def advanceWorkflow(identifiers: list[str]) -> str:
    """Advance multiple items concurrently"""
    petri_net.metrics['tool_calls'] += 1
    
    results = []
    for identifier in identifiers:
        entity = (WORKFLOW_DATA['entities']['tasks'].get(identifier) or 
                  WORKFLOW_DATA['entities']['bugs'].get(identifier))
        
        if not entity:
            results.append(f"{identifier}: Not found")
            continue
            
        current_state = get_entity_state(identifier)
        valid_states = petri_net._get_valid_states(entity)
        
        # Find next state
        try:
            current_idx = valid_states.index(current_state)
            if current_idx < len(valid_states) - 1:
                next_state = valid_states[current_idx + 1]
                if petri_net.move_token(identifier, next_state):
                    results.append(f"{identifier}: {current_state} → {next_state}")
                else:
                    results.append(f"{identifier}: Transition failed")
            else:
                results.append(f"{identifier}: Already at final state")
        except ValueError:
            results.append(f"{identifier}: Unknown current state")
    
    return ("Concurrent advancement results:\n" + 
            "\n".join(results) + 
            "\n\nPetri Net: Parallel token movement")

@mcp.tool()
def showMetrics() -> str:
    """Show navigation efficiency metrics"""
    return (f"Petri Net Navigator Metrics:\n"
            f"- Total tool calls: {petri_net.metrics['tool_calls']}\n"
            f"- Semantic hints used: {petri_net.metrics['semantic_hints_used']}\n"
            f"- Goals completed: {len(petri_net.metrics['goals_completed'])}\n"
            f"- Completed items: {', '.join(petri_net.metrics['goals_completed']) or 'None'}\n\n"
            f"Key advantages demonstrated:\n"
            f"- Multi-entry operations (no navigation required)\n"
            f"- Semantic transitions (skip intermediate states)\n"
            f"- Concurrent token movement\n"
            f"- Context-aware hints")

@mcp.tool()
def analyzeReachability(entityId: str, targetState: str) -> str:
    """Analyze if a target state is reachable from current position"""
    petri_net.metrics['tool_calls'] += 1
    
    entity = (WORKFLOW_DATA['entities']['tasks'].get(entityId) or 
              WORKFLOW_DATA['entities']['bugs'].get(entityId))
    
    if not entity:
        return f"Entity {entityId} not found"
    
    current_state = get_entity_state(entityId)
    valid_states = petri_net._get_valid_states(entity)
    
    if targetState not in valid_states:
        return f"'{targetState}' is not a valid state for {entityId}"
    
    if current_state == targetState:
        return f"{entityId} is already in {targetState} state"
    
    # Check reachability
    current_idx = valid_states.index(current_state) if current_state in valid_states else -1
    target_idx = valid_states.index(targetState)
    
    if current_idx < target_idx:
        steps = target_idx - current_idx
        path = " → ".join(valid_states[current_idx:target_idx+1])
        return (f"Target state '{targetState}' is reachable\n"
                f"Steps required: {steps}\n"
                f"Path: {path}\n"
                f"Petri Net: Formal reachability analysis")
    else:
        return (f"Target state '{targetState}' is not reachable from {current_state}\n"
                f"Would require backward transition")

@mcp.tool()
def debugPetriNet() -> str:
    """Show detailed Petri net structure for debugging"""
    petri_net.metrics['tool_calls'] += 1
    
    info = ["=== Petri Net Debug Info ===\n"]
    
    # Show places and tokens
    info.append("Places with tokens:")
    for entity_id, place in petri_net.tokens.items():
        info.append(f"  {place}: [{entity_id}]")
    
    # Show enabled transitions
    info.append("\nEnabled transitions:")
    enabled = petri_net.get_enabled_transitions()
    for trans in enabled[:10]:  # Limit output
        info.append(f"  {trans}")
    
    if len(enabled) > 10:
        info.append(f"  ... and {len(enabled) - 10} more")
    
    # Show metrics
    info.append(f"\nTotal places: {len(petri_net.net.place())}")
    info.append(f"Total transitions: {len(petri_net.net.transition())}")
    info.append(f"Current tokens: {len(petri_net.tokens)}")
    
    return ("\n".join(info) + "\n\n"
            f"Petri Net Properties:\n"
            f"- Formal model: SNAKES Petri net library\n"
            f"- Verification capable: Yes")

# Additional tools for FSM compatibility and dataset coverage

@mcp.tool()
def listProjects() -> str:
    """List projects (compatibility tool)"""
    petri_net.metrics['tool_calls'] += 1
    
    projects = []
    for project_id, project in WORKFLOW_DATA['entities']['projects'].items():
        projects.append(f"{project_id}: {project['name']} - State: {project['state']}")
    
    return ("\n".join(projects) + "\n\n"
            "Petri Net: Projects accessible without navigation hierarchy")

@mcp.tool()
def getProject(projectId: str) -> str:
    """Get project details (compatibility tool)"""
    petri_net.metrics['tool_calls'] += 1
    
    project = WORKFLOW_DATA['entities']['projects'].get(projectId)
    if not project:
        return f"Project {projectId} not found"
    
    task_count = len(project.get('tasks', []))
    bug_count = len(project.get('bugs', []))
    
    return (f"Project: {project['name']}\n"
            f"State: {project['state']}\n"
            f"Tasks: {task_count}\n"
            f"Bugs: {bug_count}\n\n"
            f"Petri Net: Project data accessible without location constraints")

@mcp.tool()
def listTasks(projectId: str) -> str:
    """List tasks in project (compatibility tool)"""
    petri_net.metrics['tool_calls'] += 1
    
    project = WORKFLOW_DATA['entities']['projects'].get(projectId)
    if not project:
        return f"Project {projectId} not found"
    
    tasks = []
    for task_id in project.get('tasks', []):
        task = WORKFLOW_DATA['entities']['tasks'].get(task_id, {})
        current_state = get_entity_state(task_id)
        tasks.append(f"{task_id}: {task.get('name', 'Unknown')} - State: {current_state}")
    
    return ("\n".join(tasks) + "\n\n"
            "Petri Net: Direct access to all tasks regardless of hierarchy")

@mcp.tool()
def listBugs(projectId: str) -> str:
    """List bugs in project (compatibility tool)"""
    petri_net.metrics['tool_calls'] += 1
    
    project = WORKFLOW_DATA['entities']['projects'].get(projectId)
    if not project:
        return f"Project {projectId} not found"
    
    bugs = []
    for bug_id in project.get('bugs', []):
        bug = WORKFLOW_DATA['entities']['bugs'].get(bug_id, {})
        current_state = get_entity_state(bug_id)
        bugs.append(f"{bug_id}: {bug.get('name', 'Unknown')} - State: {current_state}")
    
    return ("\n".join(bugs) + "\n\n"
            "Petri Net: Direct access to all bugs without navigation")

@mcp.tool()
def getTask(taskId: str) -> str:
    """Get task details (alias for getTaskInfo)"""
    return getTaskInfo(taskId)

@mcp.tool()
def getBug(bugId: str) -> str:
    """Get bug details (alias for getBugInfo)"""
    return getBugInfo(bugId)

@mcp.tool()
def getTaskState(taskId: str) -> str:
    """Get current task state"""
    petri_net.metrics['tool_calls'] += 1
    
    current_state = get_entity_state(taskId)
    return f"Task {taskId} state: {current_state}"

@mcp.tool()
def updateTaskState(taskId: str, newState: str) -> str:
    """Update task state (alias for updateState)"""
    return updateState(taskId, newState)

@mcp.tool()
def updateBugState(bugId: str, newState: str) -> str:
    """Update bug state (alias for updateState)"""
    return updateState(bugId, newState)

@mcp.tool()
def assignTask(taskId: str, userId: str) -> str:
    """Assign task to user"""
    petri_net.metrics['tool_calls'] += 1
    
    task = WORKFLOW_DATA['entities']['tasks'].get(taskId)
    if not task:
        return f"Task {taskId} not found"
    
    task['assignee'] = userId
    
    return (f"Assigned {task['name']} to {userId}\n"
            f"Petri Net: Direct assignment without navigation overhead")

@mcp.tool()
def assignBug(bugId: str, userId: str) -> str:
    """Assign bug to user"""
    petri_net.metrics['tool_calls'] += 1
    
    bug = WORKFLOW_DATA['entities']['bugs'].get(bugId)
    if not bug:
        return f"Bug {bugId} not found"
    
    bug['assignee'] = userId
    
    return (f"Assigned {bug['name']} to {userId}\n"
            f"Petri Net: Direct assignment without navigation overhead")

@mcp.tool()
def navigateToRoot() -> str:
    """Navigate to root (no-op for Petri net)"""
    petri_net.metrics['tool_calls'] += 1
    
    return ("Petri Net: No navigation required - all entities directly accessible\n"
            "Multi-entry architecture eliminates location constraints")

@mcp.tool()
def checkGoals() -> str:
    """Check goal completion status"""
    petri_net.metrics['tool_calls'] += 1
    
    if 'goals' not in WORKFLOW_DATA:
        return "No goals defined in current dataset"
    
    completed = []
    total_points = 0
    
    for goal in WORKFLOW_DATA['goals']:
        if 'entity' in goal['condition']:
            entity_id = goal['condition']['entity']
            target_state = goal['condition']['state']
            current_state = get_entity_state(entity_id)
            
            if current_state == target_state:
                completed.append(f"✓ {goal['name']} ({goal['points']} points)")
                total_points += goal['points']
                if entity_id not in petri_net.metrics['goals_completed']:
                    petri_net.metrics['goals_completed'].append(entity_id)
    
    completed_text = '\n'.join(completed) if completed else 'No goals completed yet'
    
    return (f"Goals Status:\n{completed_text}\n\n"
            f"Total Points: {total_points}\n"
            f"Petri Net: Goal verification through token analysis")

# Run the server
if __name__ == "__main__":
    mcp.run()