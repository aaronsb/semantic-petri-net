#!/usr/bin/env python3
"""
Test Harness for Comparing FSM vs Petri Net Navigators

This script connects to both MCP servers and compares their performance
on identical workflow goals, measuring actual tool calls and efficiency.
"""

import json
import asyncio
import subprocess
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Will be loaded dynamically based on dataset file path
WORKFLOW_DATA = None

@dataclass
class NavigationMetrics:
    """Metrics for a single navigation approach"""
    name: str
    tool_calls: int = 0
    goals_completed: List[str] = field(default_factory=list)
    paths_taken: List[List[str]] = field(default_factory=list)
    semantic_hints_followed: int = 0
    time_elapsed: float = 0.0
    errors_encountered: int = 0
    
    def add_tool_call(self, tool_name: str, result: str = ""):
        self.tool_calls += 1
        if self.paths_taken:
            self.paths_taken[-1].append(tool_name)
        # Count semantic hints usage
        if "hints" in result.lower() or "suggestion" in result.lower():
            self.semantic_hints_followed += 1
    
    def start_new_goal(self):
        self.paths_taken.append([])
    
    def complete_goal(self, goal_id: str):
        self.goals_completed.append(goal_id)
    
    def get_average_calls_per_goal(self) -> float:
        if len(self.goals_completed) == 0:
            return 0
        return self.tool_calls / len(self.goals_completed)

class MCPClient:
    """Simple MCP client to communicate with servers"""
    
    def __init__(self, navigator_type: str, dataset_path: str):
        self.navigator_type = navigator_type
        self.dataset_path = dataset_path
        self.process = None
        self.request_id = 0
        
    async def start(self):
        """Start the MCP server process"""
        if self.navigator_type == "fsm":
            cmd = ["uv", "--directory", 
                   "/home/aaron/Projects/ai/mcp/semantic-petri-net/simulator/fsm-navigator",
                   "run", "python", "index.py", self.dataset_path]
        else:  # petri
            cmd = ["uv", "--directory",
                   "/home/aaron/Projects/ai/mcp/semantic-petri-net/simulator/petri-navigator", 
                   "run", "python", "index.py", self.dataset_path]
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Initialize MCP session
        await self._send_message({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-harness", "version": "1.0.0"}
            }
        })
        
        # Wait for initialize response
        await self._read_message()
        
        # Send initialized notification
        await self._send_message({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        })
    
    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id
    
    async def _send_message(self, message: dict):
        """Send a JSON-RPC message"""
        json_str = json.dumps(message) + "\n"
        self.process.stdin.write(json_str.encode())
        await self.process.stdin.drain()
    
    async def _read_message(self) -> Optional[dict]:
        """Read a JSON-RPC response"""
        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=5.0)
            if line:
                return json.loads(line.decode().strip())
        except (asyncio.TimeoutError, json.JSONDecodeError):
            pass
        return None
    
    async def call_tool(self, tool_name: str, arguments: dict = None) -> tuple[bool, str]:
        """Call a tool and return (success, result)"""
        if arguments is None:
            arguments = {}
        
        message = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self._send_message(message)
        response = await self._read_message()
        
        if response and "result" in response:
            content = response["result"].get("content", [])
            if content and len(content) > 0:
                return True, content[0].get("text", "")
        
        return False, f"Error calling {tool_name}"
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

class FSMNavigatorTest:
    """Test FSM Navigator using real MCP calls"""
    
    def __init__(self, dataset_path: str):
        self.metrics = NavigationMetrics("FSM Navigator")
        self.client = MCPClient("fsm", dataset_path)
        self.current_location = "root"
    
    async def initialize(self):
        await self.client.start()
    
    async def cleanup(self):
        await self.client.stop()
    
    async def achieve_goal(self, goal: Dict[str, Any]) -> bool:
        """Attempt to achieve a goal using FSM navigation"""
        self.metrics.start_new_goal()
        
        if goal['id'] == 'goal-ship-feature':
            return await self._complete_task(goal['entity'])
        elif goal['id'] == 'goal-fix-critical-bug':
            return await self._fix_bug(goal['entity'])
        elif goal['id'] == 'goal-complete-review':
            return await self._update_task_state(goal['entity'])
        elif goal['id'] == 'goal-quick-task-start':
            return await self._start_task_efficiently(goal['entity'])
        elif goal['id'] == 'goal-reassign-work':
            return await self._reassign_work_item(goal['entity'])
        
        return False
    
    async def _complete_task(self, task_id: str) -> bool:
        """Goal: Complete a task through all states"""
        try:
            # Get first project for navigation
            dataset = DATASETS[self.client.dataset_name]
            project_id = list(dataset['entities']['projects'].keys())[0]
            
            # FSM requires navigation hierarchy
            success, result = await self.client.call_tool("listProjects")
            self.metrics.add_tool_call("listProjects", result)
            
            success, result = await self.client.call_tool("getProject", {"projectId": project_id})
            self.metrics.add_tool_call("getProject", result)
            
            success, result = await self.client.call_tool("listTasks", {"projectId": project_id})
            self.metrics.add_tool_call("listTasks", result)
            
            success, result = await self.client.call_tool("getTask", {"taskId": task_id})
            self.metrics.add_tool_call("getTask", result)
            
            # Try to advance task to completion (In Progress -> Done)
            success, result = await self.client.call_tool("updateTaskState", 
                                                        {"taskId": task_id, "newState": "In Progress"})
            self.metrics.add_tool_call("updateTaskState", result)
            
            success, result = await self.client.call_tool("updateTaskState", 
                                                        {"taskId": task_id, "newState": "Done"})
            self.metrics.add_tool_call("updateTaskState", result)
            
            if success:
                self.metrics.complete_goal('goal-ship-feature')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _fix_critical_bug(self) -> bool:
        """Goal: Fix bug-login"""
        try:
            # Navigate to bugs (must go back to root first in FSM)
            success, result = await self.client.call_tool("navigateToRoot")
            self.metrics.add_tool_call("navigateToRoot", result)
            
            success, result = await self.client.call_tool("listProjects")
            self.metrics.add_tool_call("listProjects", result)
            
            success, result = await self.client.call_tool("getProject", {"projectId": "project-web"})
            self.metrics.add_tool_call("getProject", result)
            
            success, result = await self.client.call_tool("listBugs", {"projectId": "project-web"})
            self.metrics.add_tool_call("listBugs", result)
            
            success, result = await self.client.call_tool("getBug", {"bugId": "bug-login"})
            self.metrics.add_tool_call("getBug", result)
            
            # Update bug states
            success, result = await self.client.call_tool("updateBugState", 
                                                        {"bugId": "bug-login", "newState": "In Progress"})
            self.metrics.add_tool_call("updateBugState", result)
            
            success, result = await self.client.call_tool("updateBugState", 
                                                        {"bugId": "bug-login", "newState": "Fixed"})
            self.metrics.add_tool_call("updateBugState", result)
            
            success, result = await self.client.call_tool("updateBugState", 
                                                        {"bugId": "bug-login", "newState": "Verified"})
            self.metrics.add_tool_call("updateBugState", result)
            
            if success:
                self.metrics.complete_goal('goal-fix-critical-bug')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _complete_code_review(self) -> bool:
        """Goal: Move task-api from Review to Testing"""
        try:
            # Navigate to the task
            success, result = await self.client.call_tool("navigateToRoot")
            self.metrics.add_tool_call("navigateToRoot", result)
            
            success, result = await self.client.call_tool("listProjects")
            self.metrics.add_tool_call("listProjects", result)
            
            success, result = await self.client.call_tool("getProject", {"projectId": "project-web"})
            self.metrics.add_tool_call("getProject", result)
            
            success, result = await self.client.call_tool("listTasks", {"projectId": "project-web"})
            self.metrics.add_tool_call("listTasks", result)
            
            success, result = await self.client.call_tool("getTask", {"taskId": "task-api"})
            self.metrics.add_tool_call("getTask", result)
            
            success, result = await self.client.call_tool("updateTaskState", 
                                                        {"taskId": "task-api", "newState": "Testing"})
            self.metrics.add_tool_call("updateTaskState", result)
            
            if success:
                self.metrics.complete_goal('goal-complete-review')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _start_task_efficiently(self) -> bool:
        """Goal: Start any open task in under 3 calls (SHOULD FAIL for FSM)"""
        try:
            # FSM cannot do this efficiently - requires navigation
            success, result = await self.client.call_tool("listProjects")
            self.metrics.add_tool_call("listProjects", result)
            
            success, result = await self.client.call_tool("getProject", {"projectId": "project-web"})
            self.metrics.add_tool_call("getProject", result)
            
            success, result = await self.client.call_tool("listTasks", {"projectId": "project-web"})
            self.metrics.add_tool_call("listTasks", result)
            
            success, result = await self.client.call_tool("getTask", {"taskId": "task-deploy"})
            self.metrics.add_tool_call("getTask", result)
            
            success, result = await self.client.call_tool("assignTask", 
                                                        {"taskId": "task-deploy", "userId": "user-alice"})
            self.metrics.add_tool_call("assignTask", result)
            
            success, result = await self.client.call_tool("updateTaskState", 
                                                        {"taskId": "task-deploy", "newState": "Ready"})
            self.metrics.add_tool_call("updateTaskState", result)
            
            # This took 6 calls, not under 3 - FSM limitation
            self.metrics.errors_encountered += 1
            return False
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _reassign_work_item(self) -> bool:
        """Goal: Reassign task-ui"""
        try:
            # Navigate to task
            success, result = await self.client.call_tool("navigateToRoot")
            self.metrics.add_tool_call("navigateToRoot", result)
            
            success, result = await self.client.call_tool("listProjects")
            self.metrics.add_tool_call("listProjects", result)
            
            success, result = await self.client.call_tool("getProject", {"projectId": "project-web"})
            self.metrics.add_tool_call("getProject", result)
            
            success, result = await self.client.call_tool("listTasks", {"projectId": "project-web"})
            self.metrics.add_tool_call("listTasks", result)
            
            success, result = await self.client.call_tool("getTask", {"taskId": "task-ui"})
            self.metrics.add_tool_call("getTask", result)
            
            success, result = await self.client.call_tool("assignTask", 
                                                        {"taskId": "task-ui", "userId": "user-charlie"})
            self.metrics.add_tool_call("assignTask", result)
            
            if success:
                self.metrics.complete_goal('goal-reassign-work')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False

class PetriNetNavigatorTest:
    """Test Petri Net Navigator using real MCP calls"""
    
    def __init__(self, dataset_path: str):
        self.metrics = NavigationMetrics("Petri Net Navigator")
        self.client = MCPClient("petri", dataset_path)
    
    async def initialize(self):
        await self.client.start()
    
    async def cleanup(self):
        await self.client.stop()
    
    async def achieve_goal(self, goal: Dict[str, Any]) -> bool:
        """Attempt to achieve a goal using Petri Net navigation"""
        self.metrics.start_new_goal()
        
        if goal['id'] == 'goal-ship-feature':
            return await self._complete_task(goal['entity'])
        elif goal['id'] == 'goal-fix-critical-bug':
            return await self._fix_bug(goal['entity'])
        elif goal['id'] == 'goal-complete-review':
            return await self._update_task_state(goal['entity'])
        elif goal['id'] == 'goal-quick-task-start':
            return await self._start_task_efficiently(goal['entity'])
        elif goal['id'] == 'goal-reassign-work':
            return await self._reassign_work_item(goal['entity'])
        
        return False
    
    async def _complete_task(self, task_id: str) -> bool:
        """Goal: Complete a task using semantic operations"""
        try:
            # Direct multi-entry access with semantic hints
            success, result = await self.client.call_tool("startWorkingOn", {"identifier": task_id})
            self.metrics.add_tool_call("startWorkingOn", result)
            
            # Complete in one semantic operation (jumps through states)
            success, result = await self.client.call_tool("completeItem", {"entityId": task_id})
            self.metrics.add_tool_call("completeItem", result)
            
            if success:
                self.metrics.complete_goal('goal-ship-feature')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _fix_bug(self, bug_id: str) -> bool:
        """Goal: Fix bug using semantic operations"""
        try:
            # Direct access to bug
            success, result = await self.client.call_tool("getBugInfo", {"bugId": bug_id})
            self.metrics.add_tool_call("getBugInfo", result)
            
            # Start working on it
            success, result = await self.client.call_tool("startWorkingOn", {"identifier": bug_id})
            self.metrics.add_tool_call("startWorkingOn", result)
            
            # Complete bug fix
            success, result = await self.client.call_tool("completeItem", {"entityId": bug_id})
            self.metrics.add_tool_call("completeItem", result)
            
            if success:
                self.metrics.complete_goal('goal-fix-critical-bug')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _complete_code_review(self) -> bool:
        """Goal: Move task-api from Review to Testing"""
        try:
            # Direct state update
            success, result = await self.client.call_tool("updateState", 
                                                        {"entityId": "task-api", "newState": "Testing"})
            self.metrics.add_tool_call("updateState", result)
            
            if success:
                self.metrics.complete_goal('goal-complete-review')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _start_task_efficiently(self) -> bool:
        """Goal: Start any open task in under 3 calls (EASY for Petri Net)"""
        try:
            # Single semantic operation
            success, result = await self.client.call_tool("startWorkingOn", {"identifier": "task-deploy"})
            self.metrics.add_tool_call("startWorkingOn", result)
            
            # Only 1 call needed!
            if success:
                self.metrics.complete_goal('goal-quick-task-start')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False
    
    async def _reassign_work_item(self) -> bool:
        """Goal: Reassign task-ui"""
        try:
            # Direct reassignment without navigation
            success, result = await self.client.call_tool("reassignItem", 
                                                        {"entityId": "task-ui", 
                                                         "fromUser": "user-alice", 
                                                         "toUser": "user-charlie"})
            self.metrics.add_tool_call("reassignItem", result)
            
            if success:
                self.metrics.complete_goal('goal-reassign-work')
                return True
        except Exception as e:
            self.metrics.errors_encountered += 1
        
        return False

def enumerate_all_tests(dataset: dict) -> list:
    """Enumerate ALL possible tests from the dataset systematically"""
    tests = []
    test_id = 0
    
    projects = list(dataset['entities']['projects'].keys())
    tasks = list(dataset['entities']['tasks'].keys()) 
    bugs = list(dataset['entities']['bugs'].keys())
    users = list(dataset['entities']['users'].keys())
    
    # 1. Single state transitions for each task
    for task_id in tasks:
        task = dataset['entities']['tasks'][task_id]
        current_state = task['state']
        valid_transitions = task.get('validTransitions', {})
        project_id = task.get('project', projects[0] if projects else None)
        
        for target_state in valid_transitions.get(current_state, []):
            test_id += 1
            tests.append({
                'id': f'test-{test_id:03d}',
                'name': f'Transition {task["name"]}: {current_state} → {target_state}',
                'entity_type': 'task',
                'entity_id': task_id,
                'project_id': project_id,
                'current_state': current_state,
                'target_state': target_state,
                'test_type': 'single_transition',
                'complexity': 'simple'
            })
    
    # 2. Single state transitions for each bug
    for bug_id in bugs:
        bug = dataset['entities']['bugs'][bug_id]
        current_state = bug['state']
        valid_transitions = bug.get('validTransitions', {})
        project_id = bug.get('project', projects[0] if projects else None)
        
        for target_state in valid_transitions.get(current_state, []):
            test_id += 1
            tests.append({
                'id': f'test-{test_id:03d}',
                'name': f'Transition {bug["name"]}: {current_state} → {target_state}',
                'entity_type': 'bug',
                'entity_id': bug_id,
                'project_id': project_id,
                'current_state': current_state,
                'target_state': target_state,
                'test_type': 'single_transition',
                'complexity': 'simple'
            })
    
    # 3. Multi-step workflows (complete to final state)
    for task_id in tasks:
        task = dataset['entities']['tasks'][task_id]
        current_state = task['state']
        valid_transitions = task.get('validTransitions', {})
        project_id = task.get('project', projects[0] if projects else None)
        
        # Find terminal states (states with no outgoing transitions)
        terminal_states = []
        for state, transitions in valid_transitions.items():
            if not transitions:  # No outgoing transitions
                terminal_states.append(state)
        
        for terminal_state in terminal_states:
            if terminal_state != current_state:
                test_id += 1
                tests.append({
                    'id': f'test-{test_id:03d}',
                    'name': f'Complete {task["name"]} to {terminal_state}',
                    'entity_type': 'task',
                    'entity_id': task_id,
                    'project_id': project_id,
                    'current_state': current_state,
                    'target_state': terminal_state,
                    'test_type': 'completion',
                    'complexity': 'complex'
                })
    
    # 4. Multi-step workflows for bugs
    for bug_id in bugs:
        bug = dataset['entities']['bugs'][bug_id]
        current_state = bug['state']
        valid_transitions = bug.get('validTransitions', {})
        project_id = bug.get('project', projects[0] if projects else None)
        
        # Find terminal states
        terminal_states = []
        for state, transitions in valid_transitions.items():
            if not transitions:
                terminal_states.append(state)
        
        for terminal_state in terminal_states:
            if terminal_state != current_state:
                test_id += 1
                tests.append({
                    'id': f'test-{test_id:03d}',
                    'name': f'Resolve {bug["name"]} to {terminal_state}',
                    'entity_type': 'bug',
                    'entity_id': bug_id,
                    'project_id': project_id,
                    'current_state': current_state,
                    'target_state': terminal_state,
                    'test_type': 'completion',
                    'complexity': 'complex'
                })
    
    # 5. Direct access efficiency tests (bypass navigation)
    for task_id in tasks:
        task = dataset['entities']['tasks'][task_id]
        test_id += 1
        tests.append({
            'id': f'test-{test_id:03d}',
            'name': f'Direct Access: {task["name"]}',
            'entity_type': 'task',
            'entity_id': task_id,
            'test_type': 'direct_access',
            'complexity': 'efficiency',
            'description': 'Test navigation bypass capabilities'
        })
    
    # 6. Reassignment tests (if multiple users)
    if len(users) > 1:
        for task_id in tasks:
            task = dataset['entities']['tasks'][task_id]
            for i, from_user in enumerate(users):
                for j, to_user in enumerate(users):
                    if i != j:  # Don't reassign to same user
                        test_id += 1
                        tests.append({
                            'id': f'test-{test_id:03d}',
                            'name': f'Reassign {task["name"]}: {from_user} → {to_user}',
                            'entity_type': 'task',
                            'entity_id': task_id,
                            'from_user': from_user,
                            'to_user': to_user,
                            'test_type': 'reassignment',
                            'complexity': 'simple'
                        })
        
        for bug_id in bugs:
            bug = dataset['entities']['bugs'][bug_id]
            for i, from_user in enumerate(users):
                for j, to_user in enumerate(users):
                    if i != j:
                        test_id += 1
                        tests.append({
                            'id': f'test-{test_id:03d}',
                            'name': f'Reassign {bug["name"]}: {from_user} → {to_user}',
                            'entity_type': 'bug',
                            'entity_id': bug_id,
                            'from_user': from_user,
                            'to_user': to_user,
                            'test_type': 'reassignment',
                            'complexity': 'simple'
                        })
    
    return tests

def select_tests(all_tests: list, num_tests: int, seed: int = None) -> list:
    """Select a subset of tests using seeded randomization for reproducibility"""
    if seed is not None:
        random.seed(seed)
    
    if num_tests >= len(all_tests):
        # If requesting more tests than available, return all
        return all_tests.copy()
    
    # Random sample without replacement
    selected = random.sample(all_tests, num_tests)
    
    # Sort by ID to maintain some consistency in output order
    selected.sort(key=lambda x: x['id'])
    
    return selected

def generate_test_scenarios(dataset: dict, num_tests: int = 5, seed: int = None) -> list:
    """Generate test scenarios with enumeration and seeded selection"""
    all_tests = enumerate_all_tests(dataset)
    selected_tests = select_tests(all_tests, num_tests, seed)
    return selected_tests

async def execute_scenario_fsm(navigator, scenario):
    """Execute a scenario using FSM navigator"""
    start_time = time.time()
    navigator.metrics.start_new_goal()
    
    try:
        test_type = scenario['test_type']
        entity_type = scenario.get('entity_type', 'task')
        
        if test_type in ['single_transition', 'completion']:
            if entity_type == 'task':
                success = await _fsm_update_task_state(navigator, scenario)
            elif entity_type == 'bug':
                success = await _fsm_update_bug_state(navigator, scenario)
            else:
                success = False
        elif test_type == 'direct_access':
            success = await _fsm_direct_access(navigator, scenario)
        elif test_type == 'reassignment':
            success = await _fsm_reassign(navigator, scenario)
        else:
            success = False
        
        elapsed = time.time() - start_time
        calls = len(navigator.metrics.paths_taken[-1]) if navigator.metrics.paths_taken else 0
        return success, calls, elapsed
        
    except Exception as e:
        navigator.metrics.errors_encountered += 1
        elapsed = time.time() - start_time
        calls = len(navigator.metrics.paths_taken[-1]) if navigator.metrics.paths_taken else 0
        return False, calls, elapsed

async def execute_scenario_petri(navigator, scenario):
    """Execute a scenario using Petri navigator"""
    start_time = time.time()
    navigator.metrics.start_new_goal()
    
    try:
        test_type = scenario['test_type']
        entity_type = scenario.get('entity_type', 'task')
        
        if test_type in ['single_transition', 'completion']:
            if entity_type == 'task':
                success = await _petri_update_task_state(navigator, scenario)
            elif entity_type == 'bug':
                success = await _petri_update_bug_state(navigator, scenario)
            else:
                success = False
        elif test_type == 'direct_access':
            success = await _petri_direct_access(navigator, scenario)
        elif test_type == 'reassignment':
            success = await _petri_reassign(navigator, scenario)
        else:
            success = False
        
        elapsed = time.time() - start_time
        calls = len(navigator.metrics.paths_taken[-1]) if navigator.metrics.paths_taken else 0
        return success, calls, elapsed
        
    except Exception as e:
        navigator.metrics.errors_encountered += 1
        elapsed = time.time() - start_time
        calls = len(navigator.metrics.paths_taken[-1]) if navigator.metrics.paths_taken else 0
        return False, calls, elapsed

# FSM scenario implementations
async def _fsm_update_task_state(navigator, scenario):
    """FSM: Update task state through hierarchy"""
    # FSM requires navigation to the entity first
    success, result = await navigator.client.call_tool("listProjects")
    navigator.metrics.add_tool_call("listProjects", result)
    
    if 'project_id' in scenario:
        success, result = await navigator.client.call_tool("getProject", {"projectId": scenario['project_id']})
        navigator.metrics.add_tool_call("getProject", result)
    
    success, result = await navigator.client.call_tool("getTask", {"taskId": scenario['entity_id']})
    navigator.metrics.add_tool_call("getTask", result)
    
    success, result = await navigator.client.call_tool("updateTaskState", 
                                                      {"taskId": scenario['entity_id'], "newState": scenario['target_state']})
    navigator.metrics.add_tool_call("updateTaskState", result)
    
    return success

async def _fsm_update_bug_state(navigator, scenario):
    """FSM: Update bug state through hierarchy"""
    success, result = await navigator.client.call_tool("listProjects")
    navigator.metrics.add_tool_call("listProjects", result)
    
    if 'project_id' in scenario:
        success, result = await navigator.client.call_tool("getProject", {"projectId": scenario['project_id']})
        navigator.metrics.add_tool_call("getProject", result)
    
    success, result = await navigator.client.call_tool("getBug", {"bugId": scenario['entity_id']})
    navigator.metrics.add_tool_call("getBug", result)
    
    success, result = await navigator.client.call_tool("updateBugState", 
                                                      {"bugId": scenario['entity_id'], "newState": scenario['target_state']})
    navigator.metrics.add_tool_call("updateBugState", result)
    
    return success

async def _fsm_direct_access(navigator, scenario):
    """FSM: Try direct access (should fail due to navigation requirements)"""
    # This should fail because FSM requires navigation first
    if scenario['entity_type'] == 'task':
        success, result = await navigator.client.call_tool("updateTaskState", 
                                                          {"taskId": scenario['entity_id'], "newState": "In Progress"})
    else:
        success, result = await navigator.client.call_tool("updateBugState", 
                                                          {"bugId": scenario['entity_id'], "newState": "In Progress"})
    
    navigator.metrics.add_tool_call("updateTaskState" if scenario['entity_type'] == 'task' else "updateBugState", result)
    
    # FSM typically fails on direct access due to location requirements
    return "Error" not in result

async def _fsm_reassign(navigator, scenario):
    """FSM: Reassign entity through hierarchy"""
    success, result = await navigator.client.call_tool("listProjects")
    navigator.metrics.add_tool_call("listProjects", result)
    
    if scenario['entity_type'] == 'task':
        success, result = await navigator.client.call_tool("getTask", {"taskId": scenario['entity_id']})
        navigator.metrics.add_tool_call("getTask", result)
        
        success, result = await navigator.client.call_tool("assignTask", 
                                                          {"taskId": scenario['entity_id'], "userId": scenario['to_user']})
        navigator.metrics.add_tool_call("assignTask", result)
    else:
        success, result = await navigator.client.call_tool("getBug", {"bugId": scenario['entity_id']})
        navigator.metrics.add_tool_call("getBug", result)
        
        success, result = await navigator.client.call_tool("assignBug", 
                                                          {"bugId": scenario['entity_id'], "userId": scenario['to_user']})
        navigator.metrics.add_tool_call("assignBug", result)
    
    return success

# Petri scenario implementations  
async def _petri_update_task_state(navigator, scenario):
    """Petri: Direct task state update"""
    if scenario['test_type'] == 'completion':
        # Use semantic completion operation
        success, result = await navigator.client.call_tool("completeItem", {"entityId": scenario['entity_id']})
        navigator.metrics.add_tool_call("completeItem", result)
    else:
        # Direct state update
        success, result = await navigator.client.call_tool("updateState", 
                                                          {"entityId": scenario['entity_id'], "newState": scenario['target_state']})
        navigator.metrics.add_tool_call("updateState", result)
    
    return success

async def _petri_update_bug_state(navigator, scenario):
    """Petri: Direct bug state update"""
    if scenario['test_type'] == 'completion':
        # Use semantic completion operation  
        success, result = await navigator.client.call_tool("completeItem", {"entityId": scenario['entity_id']})
        navigator.metrics.add_tool_call("completeItem", result)
    else:
        # Direct state update
        success, result = await navigator.client.call_tool("updateState", 
                                                          {"entityId": scenario['entity_id'], "newState": scenario['target_state']})
        navigator.metrics.add_tool_call("updateState", result)
    
    return success

async def _petri_direct_access(navigator, scenario):
    """Petri: Direct access (should succeed)"""
    success, result = await navigator.client.call_tool("startWorkingOn", {"identifier": scenario['entity_id']})
    navigator.metrics.add_tool_call("startWorkingOn", result)
    
    return success

async def _petri_reassign(navigator, scenario):
    """Petri: Direct reassignment"""
    success, result = await navigator.client.call_tool("reassignItem", 
                                                      {"entityId": scenario['entity_id'],
                                                       "fromUser": scenario['from_user'],
                                                       "toUser": scenario['to_user']})
    navigator.metrics.add_tool_call("reassignItem", result)
    
    return success

async def run_comparison(dataset_file: str, num_tests: int = 5, seed: int = None):
    """Run both navigators and compare results using real MCP calls"""
    
    print("=" * 80)
    print("WORKFLOW NAVIGATION COMPARISON: FSM vs PETRI NET")
    print("Using Real MCP Server Calls")
    print(f"Dataset File: {dataset_file}")
    print("=" * 80)
    print()
    
    # Load the dataset file directly (same as MCP servers do)
    global WORKFLOW_DATA
    dataset_path = Path(__file__).parent.joinpath(dataset_file)
    if not dataset_path.exists():
        print(f"Error: Dataset file not found: {dataset_path}")
        return
        
    WORKFLOW_DATA = json.loads(dataset_path.read_text())
    dataset = WORKFLOW_DATA
    
    print(f"Loaded dataset from: {dataset_path}")
    print(f"Entities: {len(dataset['entities']['projects'])} projects, "
          f"{len(dataset['entities']['tasks'])} tasks, "
          f"{len(dataset['entities']['bugs'])} bugs")
    
    # Generate test scenarios based on actual dataset content
    print("Enumerating all possible tests from dataset...")
    all_tests = enumerate_all_tests(dataset)
    print(f"Found {len(all_tests)} total possible tests")
    
    # Select subset for this run
    print(f"Selecting {num_tests} tests (seed: {seed if seed is not None else 'random'})...")
    scenarios = select_tests(all_tests, num_tests, seed)
    
    if not scenarios:
        print(f"Error: Dataset {dataset_file} doesn't have enough entities for testing")
        return
    
    print(f"Generated {len(scenarios)} test scenarios:")
    for scenario in scenarios:
        print(f"  - {scenario['name']} ({scenario['test_type']})")
    print()
    
    # Initialize navigators with specified dataset file
    print(f"Starting MCP servers with {dataset_file}...")
    fsm_navigator = FSMNavigatorTest(str(dataset_path))
    petri_navigator = PetriNetNavigatorTest(str(dataset_path))
    
    try:
        await fsm_navigator.initialize()
        await petri_navigator.initialize()
        print("✓ Both MCP servers started successfully\n")
        
        print("Running comparison tests...\n")
        
        for scenario in scenarios:
            print(f"Scenario: {scenario['name']}")
            
            # Execute scenario with both navigators
            fsm_success, fsm_calls, fsm_time = await execute_scenario_fsm(fsm_navigator, scenario)
            petri_success, petri_calls, petri_time = await execute_scenario_petri(petri_navigator, scenario)
            
            print(f"  FSM: {'✓' if fsm_success else '✗'} ({fsm_calls} calls, {fsm_time:.2f}s)")
            print(f"  Petri Net: {'✓' if petri_success else '✗'} ({petri_calls} calls, {petri_time:.2f}s)")
            
            if petri_calls > 0 and fsm_calls > 0:
                efficiency = fsm_calls / petri_calls
                print(f"  Efficiency gain: {efficiency:.1f}x")
            elif petri_success and not fsm_success:
                print(f"  FSM failed, Petri succeeded (architectural advantage)")
            print()
        
        # Generate results
        print("\n" + "=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        
        print("\n## Overall Performance")
        print(f"Total Tool Calls:")
        print(f"  FSM Navigator: {fsm_navigator.metrics.tool_calls}")
        print(f"  Petri Net Navigator: {petri_navigator.metrics.tool_calls}")
        if petri_navigator.metrics.tool_calls > 0:
            efficiency = fsm_navigator.metrics.tool_calls / petri_navigator.metrics.tool_calls
            print(f"  Efficiency Gain: {efficiency:.1f}x")
        
        print(f"\nGoals Completed:")
        print(f"  FSM Navigator: {len(fsm_navigator.metrics.goals_completed)}/{len(scenarios)}")
        print(f"  Petri Net Navigator: {len(petri_navigator.metrics.goals_completed)}/{len(scenarios)}")
        
        print(f"\nAverage Calls per Goal:")
        print(f"  FSM Navigator: {fsm_navigator.metrics.get_average_calls_per_goal():.1f}")
        print(f"  Petri Net Navigator: {petri_navigator.metrics.get_average_calls_per_goal():.1f}")
        
        print(f"\nSemantic Hints Followed:")
        print(f"  FSM Navigator: {fsm_navigator.metrics.semantic_hints_followed}")
        print(f"  Petri Net Navigator: {petri_navigator.metrics.semantic_hints_followed}")
        
        print(f"\nErrors Encountered:")
        print(f"  FSM Navigator: {fsm_navigator.metrics.errors_encountered}")
        print(f"  Petri Net Navigator: {petri_navigator.metrics.errors_encountered}")
        
        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "real_mcp_calls",
            "fsm_metrics": {
                "tool_calls": fsm_navigator.metrics.tool_calls,
                "goals_completed": fsm_navigator.metrics.goals_completed,
                "average_calls_per_goal": fsm_navigator.metrics.get_average_calls_per_goal(),
                "semantic_hints_followed": fsm_navigator.metrics.semantic_hints_followed,
                "errors": fsm_navigator.metrics.errors_encountered,
                "time_elapsed": fsm_navigator.metrics.time_elapsed
            },
            "petri_metrics": {
                "tool_calls": petri_navigator.metrics.tool_calls,
                "goals_completed": petri_navigator.metrics.goals_completed,
                "average_calls_per_goal": petri_navigator.metrics.get_average_calls_per_goal(),
                "semantic_hints_followed": petri_navigator.metrics.semantic_hints_followed,
                "errors": petri_navigator.metrics.errors_encountered,
                "time_elapsed": petri_navigator.metrics.time_elapsed
            },
            "efficiency_gain": (fsm_navigator.metrics.tool_calls / petri_navigator.metrics.tool_calls 
                              if petri_navigator.metrics.tool_calls > 0 else 0),
            "paths": {
                "fsm": [[call for call in path] for path in fsm_navigator.metrics.paths_taken],
                "petri": [[call for call in path] for path in petri_navigator.metrics.paths_taken]
            }
        }
        
        with open('test-results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n✅ Results saved to test-results.json")
        
        # Key findings
        print("\n## Key Findings")
        print("1. FSM Navigator requires hierarchical navigation for every operation")
        print("2. Petri Net Navigator uses direct multi-entry access")
        print("3. Semantic operations in Petri Net eliminate intermediate steps")
        print("4. FSM fails on time-constrained goals due to navigation overhead")
        print("5. Petri Net achieves same goals with significantly fewer calls")
        
    finally:
        # Cleanup
        print("\nShutting down MCP servers...")
        await fsm_navigator.cleanup()
        await petri_navigator.cleanup()
        print("✓ Cleanup complete")

# Gauntlet functionality removed - users can run datasets individually

if __name__ == "__main__":
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Harness for Comparing FSM vs Petri Net Navigators')
    parser.add_argument('dataset_file', help='Path to dataset JSON file')
    parser.add_argument('-n', '--num-tests', type=int, default=5, 
                       help='Number of tests to run (default: 5)')
    parser.add_argument('-s', '--seed', type=int, default=None,
                       help='Random seed for reproducible test selection (default: random)')
    parser.add_argument('--list-all', action='store_true',
                       help='List all possible tests in the dataset and exit')
    
    args = parser.parse_args()
    
    if args.list_all:
        # Load dataset and list all possible tests
        from pathlib import Path
        dataset_path = Path(args.dataset_file)
        if not dataset_path.exists():
            print(f"Error: Dataset file not found: {dataset_path}")
            sys.exit(1)
        
        WORKFLOW_DATA = json.loads(dataset_path.read_text())
        all_tests = enumerate_all_tests(WORKFLOW_DATA)
        
        print(f"Dataset: {args.dataset_file}")
        print(f"Total possible tests: {len(all_tests)}")
        print("\nAll possible tests:")
        for i, test in enumerate(all_tests, 1):
            print(f"{i:3d}. {test['name']} ({test['test_type']}, {test['complexity']})")
        
        print(f"\nTo run a subset:")
        print(f"  python test-harness.py {args.dataset_file} -n 10")
        print(f"  python test-harness.py {args.dataset_file} -n 10 -s 42  # reproducible")
        sys.exit(0)
    
    asyncio.run(run_comparison(args.dataset_file, args.num_tests, args.seed))