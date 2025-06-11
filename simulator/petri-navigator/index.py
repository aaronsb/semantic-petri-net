#!/usr/bin/env python3
"""
Petri Net Navigator using SNAKES library
Demonstrates formal Petri net modeling for workflow navigation
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP

try:
    from snakes.nets import *
    from snakes.plugins import load
    load("gv", "snakes.nets", "nets")
    from nets import *
except ImportError:
    print("Warning: SNAKES not installed. Install with: pip install SNAKES")
    # Fallback implementation for testing
    PetriNet = None

# Load workflow data
WORKFLOW_DATA = json.loads(
    Path(__file__).parent.parent.joinpath('workflow-test-dataset.json').read_text()
)

# Create MCP server
mcp = FastMCP("petri-workflow-navigator")

class WorkflowPetriNet:
    """Formal Petri net model of the workflow system"""
    
    def __init__(self):
        if PetriNet is None:
            raise ImportError("SNAKES library required for formal Petri net modeling")
            
        self.net = PetriNet('workflow_system')
        self.tokens = {}  # Track token locations
        self.metrics = {
            'tool_calls': 0,
            'semantic_hints_used': 0,
            'goals_completed': []
        }
        self._build_net()
    
    def _build_net(self):
        """Build the Petri net structure from workflow data"""
        
        # Create places for each task state
        for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
            for state in task['validStates']:
                place_name = f"{task_id}_{state}"
                self.net.add_place(Place(place_name, []))
            
            # Add initial token
            initial_place = f"{task_id}_{task['state']}"
            self.net.place(initial_place).add(task_id)
            self.tokens[task_id] = initial_place
        
        # Create places for bug states
        for bug_id, bug in WORKFLOW_DATA['entities']['bugs'].items():
            for state in bug['validStates']:
                place_name = f"{bug_id}_{state}"
                self.net.add_place(Place(place_name, []))
            
            initial_place = f"{bug_id}_{bug['state']}"
            self.net.place(initial_place).add(bug_id)
            self.tokens[bug_id] = initial_place
        
        # Create transitions for state changes
        self._add_task_transitions()
        self._add_bug_transitions()
        self._add_semantic_transitions()
    
    def _add_task_transitions(self):
        """Add transitions for task state changes"""
        for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
            states = task['validStates']
            
            # Add transitions between consecutive states
            for i in range(len(states) - 1):
                from_state = states[i]
                to_state = states[i + 1]
                trans_name = f"{task_id}_move_{from_state}_to_{to_state}"
                
                self.net.add_transition(Transition(trans_name))
                self.net.add_input(f"{task_id}_{from_state}", trans_name, Variable('token'))
                self.net.add_output(f"{task_id}_{to_state}", trans_name, Variable('token'))
    
    def _add_bug_transitions(self):
        """Add transitions for bug state changes"""
        for bug_id, bug in WORKFLOW_DATA['entities']['bugs'].items():
            states = bug['validStates']
            
            for i in range(len(states) - 1):
                from_state = states[i]
                to_state = states[i + 1]
                trans_name = f"{bug_id}_move_{from_state}_to_{to_state}"
                
                self.net.add_transition(Transition(trans_name))
                self.net.add_input(f"{bug_id}_{from_state}", trans_name, Variable('token'))
                self.net.add_output(f"{bug_id}_{to_state}", trans_name, Variable('token'))
    
    def _add_semantic_transitions(self):
        """Add high-level semantic transitions that cross multiple states"""
        
        # Start working on task (Open -> In Progress with assignment)
        for task_id in WORKFLOW_DATA['entities']['tasks']:
            trans_name = f"start_work_{task_id}"
            self.net.add_transition(Transition(trans_name))
            self.net.add_input(f"{task_id}_Open", trans_name, Variable('token'))
            self.net.add_output(f"{task_id}_In Progress", trans_name, Variable('token'))
        
        # Complete task (any non-Done state -> Done)
        for task_id, task in WORKFLOW_DATA['entities']['tasks'].items():
            for state in task['validStates'][:-1]:  # All states except Done
                trans_name = f"complete_{task_id}_from_{state}"
                self.net.add_transition(Transition(trans_name))
                self.net.add_input(f"{task_id}_{state}", trans_name, Variable('token'))
                self.net.add_output(f"{task_id}_Done", trans_name, Variable('token'))
    
    def get_enabled_transitions(self, entity_id: Optional[str] = None) -> List[str]:
        """Get all currently enabled transitions"""
        enabled = []
        
        for trans in self.net.transitions():
            if trans.enabled(Substitution()):
                if entity_id is None or entity_id in trans.name:
                    enabled.append(trans.name)
        
        return enabled
    
    def fire_transition(self, transition_name: str) -> bool:
        """Execute a transition if enabled"""
        trans = self.net.transition(transition_name)
        if trans and trans.enabled(Substitution()):
            trans.fire(Substitution())
            
            # Update token tracking
            for entity_id, place in self.tokens.items():
                if entity_id in transition_name:
                    # Find new location
                    for p in self.net.places():
                        if entity_id in p.name and len(list(p.tokens)) > 0:
                            self.tokens[entity_id] = p.name
                            break
            
            return True
        return False
    
    def generate_semantic_hints(self, entity_id: str) -> Dict[str, List[str]]:
        """Generate context-aware hints based on Petri net state"""
        current_place = self.tokens.get(entity_id)
        if not current_place:
            return {'nextSteps': [], 'suggestions': []}
        
        # Find enabled transitions from current state
        enabled = self.get_enabled_transitions(entity_id)
        
        # Generate human-readable hints
        next_steps = []
        suggestions = []
        
        for trans in enabled:
            if 'move_' in trans:
                parts = trans.split('_')
                next_state = parts[-1]
                next_steps.append(f"Can move to {next_state}")
            elif 'start_work' in trans:
                suggestions.append("Use startWorkingOn() to begin work")
            elif 'complete' in trans:
                suggestions.append("Use completeTask() to finish")
        
        # Add workflow-specific hints
        if 'Open' in current_place:
            suggestions.append("Task is ready to be started")
        elif 'In Progress' in current_place:
            next_steps.append("Continue development or move to review")
        elif 'Review' in current_place:
            next_steps.append("Complete review and move to testing")
        
        return {
            'nextSteps': next_steps,
            'suggestions': suggestions
        }
    
    def visualize(self, filename: str = "workflow_net.png"):
        """Generate visual representation of the Petri net"""
        if hasattr(self.net, 'draw'):
            self.net.draw(filename)

# Initialize Petri net
petri_net = WorkflowPetriNet()

# Helper functions
def find_entity(identifier: str) -> Optional[Dict[str, Any]]:
    """Find entity by ID or name"""
    
    # Check tasks
    for task in WORKFLOW_DATA['entities']['tasks'].values():
        if identifier in [task['id'], task['name']] or identifier.lower() in task['name'].lower():
            return task
    
    # Check bugs
    for bug in WORKFLOW_DATA['entities']['bugs'].values():
        if identifier in [bug['id'], bug['name']] or identifier.lower() in bug['name'].lower():
            return bug
    
    return None

def get_entity_state(entity_id: str) -> str:
    """Get current state from Petri net"""
    place = petri_net.tokens.get(entity_id, "")
    if '_' in place:
        return place.split('_', 1)[1]
    return "Unknown"

# Define MCP tools
@mcp.tool()
def startWorkingOn(identifier: str) -> str:
    """Start working on a task or bug (multi-entry semantic operation)"""
    petri_net.metrics['tool_calls'] += 1
    
    # Find entity
    entity = find_entity(identifier)
    if not entity:
        return f"Could not find entity: {identifier}"
    
    entity_id = entity['id']
    current_state = get_entity_state(entity_id)
    
    # Try to fire start work transition
    trans_name = f"start_work_{entity_id}"
    if petri_net.fire_transition(trans_name):
        # Generate semantic hints
        hints = petri_net.generate_semantic_hints(entity_id)
        petri_net.metrics['semantic_hints_used'] += 1
        
        return (f"Started working on {entity['name']}\n"
                f"State: Open → In Progress\n"
                f"Next steps: {', '.join(hints['nextSteps'])}\n"
                f"Suggestions: {', '.join(hints['suggestions'])}")
    else:
        # Provide guidance on why it failed
        enabled = petri_net.get_enabled_transitions(entity_id)
        return (f"Cannot start work on {entity['name']} in state {current_state}\n"
                f"Available actions: {', '.join(enabled)}")

@mcp.tool()
def completeTask(identifier: str) -> str:
    """Complete a task from any state"""
    petri_net.metrics['tool_calls'] += 1
    
    entity = find_entity(identifier)
    if not entity:
        return f"Could not find entity: {identifier}"
    
    entity_id = entity['id']
    current_state = get_entity_state(entity_id)
    
    # Find appropriate complete transition
    for trans in petri_net.get_enabled_transitions(entity_id):
        if 'complete' in trans and entity_id in trans:
            if petri_net.fire_transition(trans):
                return (f"Completed {entity['name']}\n"
                        f"State: {current_state} → Done\n"
                        f"This demonstrates multi-entry: reached Done from {current_state}")
    
    return f"Cannot complete {entity['name']} from current state {current_state}"

@mcp.tool()
def getWorkflowState(entity_id: Optional[str] = None) -> str:
    """View current state with Petri net analysis"""
    petri_net.metrics['tool_calls'] += 1
    
    if entity_id:
        current_place = petri_net.tokens.get(entity_id, "Unknown")
        enabled = petri_net.get_enabled_transitions(entity_id)
        
        return (f"Entity: {entity_id}\n"
                f"Current state: {current_place}\n"
                f"Enabled transitions: {', '.join(enabled)}\n"
                f"This shows Petri net modeling of workflow states")
    else:
        # Show all tokens
        states = []
        for eid, place in petri_net.tokens.items():
            states.append(f"{eid}: {place}")
        
        return f"Current Petri net configuration:\n" + "\n".join(states)

@mcp.tool()
def visualizePetriNet() -> str:
    """Generate visual representation of the workflow Petri net"""
    petri_net.metrics['tool_calls'] += 1
    
    try:
        petri_net.visualize("workflow_petri_net.png")
        return ("Generated Petri net visualization: workflow_petri_net.png\n"
                "This shows the formal workflow structure as a Petri net")
    except Exception as e:
        return (f"Could not generate visualization: {e}\n"
                "Ensure graphviz is installed")

@mcp.tool()
def analyzeReachability(entity_id: str) -> str:
    """Analyze what states are reachable from current configuration"""
    petri_net.metrics['tool_calls'] += 1
    
    current_place = petri_net.tokens.get(entity_id, "Unknown")
    
    # Simple reachability check - what states can we reach?
    reachable = []
    enabled = petri_net.get_enabled_transitions(entity_id)
    
    for trans in enabled:
        if 'Done' in trans:
            reachable.append("Done (goal state)")
        elif 'Testing' in trans:
            reachable.append("Testing")
        elif 'Review' in trans:
            reachable.append("Review")
    
    return (f"Reachability analysis for {entity_id}:\n"
            f"Current: {current_place}\n"
            f"Reachable states: {', '.join(reachable) or 'None directly'}\n"
            f"This demonstrates formal verification capabilities")

@mcp.tool()
def checkGoals() -> str:
    """Check which goals have been achieved"""
    petri_net.metrics['tool_calls'] += 1
    
    completed = []
    for goal in WORKFLOW_DATA['goals']:
        if 'entity' in goal['condition']:
            entity_id = goal['condition']['entity']
            target_state = goal['condition']['state']
            
            current = petri_net.tokens.get(entity_id, "")
            if target_state in current:
                completed.append(f"✓ {goal['name']} ({goal['points']} points)")
                if goal['id'] not in petri_net.metrics['goals_completed']:
                    petri_net.metrics['goals_completed'].append(goal['id'])
    
    total_points = len(petri_net.metrics['goals_completed']) * 100
    
    return (f"Goals completed:\n" + "\n".join(completed) + 
            f"\n\nTotal points: {total_points}/800")

@mcp.tool()
def getMetrics() -> str:
    """Get performance metrics"""
    metrics = petri_net.metrics
    goals_count = len(metrics['goals_completed'])
    
    avg_calls = metrics['tool_calls'] / goals_count if goals_count > 0 else 0
    
    return (f"Petri Net Navigator Metrics:\n"
            f"- Tool calls: {metrics['tool_calls']}\n"
            f"- Semantic hints used: {metrics['semantic_hints_used']}\n"
            f"- Goals completed: {goals_count}\n"
            f"- Average calls per goal: {avg_calls:.1f}\n"
            f"- Formal model: SNAKES Petri net library\n"
            f"- Verification capable: Yes")

if __name__ == "__main__":
    mcp.run()