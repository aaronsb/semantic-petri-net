# Concrete Mathematical Example: Bug Tracking Workflow

## Classical Petri Net vs. Semantic Petri Net

### Traditional FSM Bug Workflow

**Places (P)**: {New, Assigned, InProgress, Testing, Done}
**Transitions (T)**: {assign, start, complete, test, close}
**Initial Marking**: M₀ = [1,0,0,0,0] (one token in "New")

```
New → assign → Assigned → start → InProgress → complete → Testing → test → Done
```

**Problem**: All bugs must start at "New" regardless of context.

### Semantic Petri Net Bug Workflow

**Enhanced Places**:
```javascript
const places = {
  new: { id: 'new', isInitial: true, roleConstraints: ['reporter'] },
  investigating: { id: 'investigating', isInitial: true, roleConstraints: ['developer'] },
  assigned: { id: 'assigned', isInitial: false, roleConstraints: [] },
  inProgress: { id: 'inProgress', isInitial: true, roleConstraints: ['developer'] },
  testing: { id: 'testing', isInitial: false, roleConstraints: ['tester'] },
  done: { id: 'done', isInitial: false, isFinal: true, roleConstraints: [] }
};
```

**Semantic Transitions**:
```javascript
const transitions = {
  report: {
    from: ['new'],
    to: ['assigned'],
    roles: ['reporter'],
    guidance: (context) => ['Provide reproduction steps', 'Set priority level']
  },
  investigate: {
    from: ['investigating'],
    to: ['inProgress'],
    roles: ['developer'],
    guidance: (context) => ['Document findings', 'Estimate effort']
  },
  escalate: {
    from: ['new', 'assigned'],
    to: ['investigating'],
    roles: ['developer', 'manager'],
    guidance: (context) => ['Assess impact', 'Notify stakeholders']
  }
};
```

**Multiple Valid Initial Markings**:
- Reporter workflow: M₁ = [1,0,0,0,0,0] (starts at "new")
- Emergency bug: M₂ = [0,1,0,0,0,0] (starts at "investigating")
- Ongoing work: M₃ = [0,0,0,1,0,0] (starts at "inProgress")

### Mathematical Properties

#### 1. Reachability Analysis
**Question**: Can state "done" be reached from any initial marking?

**Classical Analysis**: 
- From M₁: New → Assigned → InProgress → Testing → Done ✓
- From M₂: Not reachable (no path from Investigating to standard flow) ✗

**Semantic Analysis**:
- From M₁: New → Assigned → InProgress → Testing → Done ✓
- From M₂: Investigating → InProgress → Testing → Done ✓
- From M₃: InProgress → Testing → Done ✓

**Result**: Semantic extension increases reachable state space while maintaining governance.

#### 2. Liveness Analysis
**Question**: Which transitions can fire infinitely often?

**Classical Liveness**:
- assign: L1 (can fire from New)
- start: L1 (can fire from Assigned)
- complete: L1 (can fire from InProgress)

**Semantic Liveness with Role Context**:
```javascript
function analyzeLiveness(transition, userRole) {
  if (!transition.roles.includes(userRole)) {
    return 'RoleDead'; // Never available to this role
  }
  
  const reachableStates = computeReachability(transition.from, userRole);
  if (reachableStates.length === 0) {
    return 'ContextuallyDead'; // Available to role but unreachable
  }
  
  return 'ContextuallyLive'; // Available when context permits
}

// Developer perspective
analyzeLiveness(transitions.investigate, 'developer') → 'ContextuallyLive'
analyzeLiveness(transitions.report, 'developer') → 'RoleDead'

// Reporter perspective  
analyzeLiveness(transitions.report, 'reporter') → 'ContextuallyLive'
analyzeLiveness(transitions.investigate, 'reporter') → 'RoleDead'
```

#### 3. Boundedness with Business Constraints
**Question**: What's the maximum number of bugs in each state?

**Classical Boundedness**: Structural only
```javascript
// No inherent bounds - could have infinite bugs in any state
const classicalBounds = {
  new: Infinity,
  assigned: Infinity,
  inProgress: Infinity,
  testing: Infinity,
  done: Infinity
};
```

**Semantic Boundedness**: Business + Role constraints
```javascript
function computeSemanticBounds(place, businessRules) {
  // Team capacity constraints
  const teamCapacity = businessRules.maxWorkInProgress || 10;
  
  // Role-based constraints
  const availableUsers = getUsersWithRole(place.roleConstraints);
  const roleCapacity = availableUsers.length * businessRules.itemsPerUser;
  
  // Business priority constraints
  const priorityCapacity = businessRules.maxHighPriorityItems || 5;
  
  return Math.min(teamCapacity, roleCapacity, priorityCapacity);
}

const semanticBounds = {
  new: computeSemanticBounds(places.new, businessRules), // e.g., 20
  investigating: computeSemanticBounds(places.investigating, businessRules), // e.g., 3
  inProgress: computeSemanticBounds(places.inProgress, businessRules), // e.g., 8
  testing: computeSemanticBounds(places.testing, businessRules), // e.g., 5
  done: Infinity // No limit on completed work
};
```

### Guidance Generation Mathematics

Each transition firing generates contextual guidance based on current state and context:

```javascript
function generateGuidance(transition, fromState, toState, context) {
  const baseGuidance = transition.guidance(context);
  
  // Add state-specific guidance
  const stateGuidance = generateStateGuidance(toState, context);
  
  // Add role-specific guidance  
  const roleGuidance = generateRoleGuidance(context.user.role, toState);
  
  // Add business context guidance
  const businessGuidance = generateBusinessGuidance(context.businessRules, toState);
  
  return {
    suggestions: [...baseGuidance, ...stateGuidance],
    nextSteps: [...roleGuidance],
    contextualHints: [...businessGuidance]
  };
}

// Example: Developer investigating emergency bug
const context = {
  user: { role: 'developer', name: 'Alice' },
  businessRules: { priority: 'critical', impact: 'high' },
  currentTime: '2024-01-15T02:30:00Z'
};

const guidance = generateGuidance(
  transitions.investigate,
  places.investigating,
  places.inProgress,
  context
);

// Result:
{
  suggestions: [
    'Document initial findings immediately',
    'Estimate time to resolution',
    'Identify root cause'
  ],
  nextSteps: [
    'Update stakeholders with progress every 30 minutes',
    'Consider pairing with senior developer if needed'
  ],
  contextualHints: [
    {
      reason: 'Critical priority detected',
      action: 'escalate-if-blocked',
      trigger: 'if no progress in 1 hour'
    }
  ]
}
```

### Emergent Pattern Detection

After many executions, certain firing sequences become common patterns:

```javascript
// Emergency Bug Pattern (learned from execution history)
const emergentPatterns = {
  emergencyBug: {
    sequence: ['escalate', 'investigate', 'start', 'complete', 'test'],
    frequency: 0.85, // 85% of critical bugs follow this pattern
    averageTime: '4 hours',
    successRate: 0.92,
    contextualTriggers: [
      { priority: 'critical' },
      { timeOfDay: 'after-hours' },
      { userRole: 'developer' }
    ]
  },
  
  standardBug: {
    sequence: ['report', 'assign', 'start', 'complete', 'test'],
    frequency: 0.65,
    averageTime: '2 days',
    successRate: 0.88,
    contextualTriggers: [
      { priority: 'normal' },
      { timeOfDay: 'business-hours' },
      { userRole: 'reporter' }
    ]
  }
};
```

### Mathematical Conclusion

This concrete example demonstrates that semantic Petri nets:

1. **Preserve Mathematical Rigor**: All classical properties (reachability, liveness, boundedness) remain well-defined
2. **Add Contextual Dimensions**: Role and business constraints create multi-dimensional property spaces
3. **Enable Optimization**: Guidance generation creates preference orderings over valid execution paths
4. **Support Learning**: Pattern detection identifies optimal workflows through statistical analysis

The mathematics validate that semantic workflows are legitimate extensions of Petri net theory that add practical value without sacrificing formal foundation.