/**
 * Semantic Petri Net Workflow Patterns
 * 
 * Abstract implementation patterns for enterprise workflow systems
 * that embrace non-deterministic flow while maintaining governance.
 * 
 * These patterns demonstrate the key concepts from the research paper
 * without reference to any specific enterprise system.
 */

// ==========================================
// Core Interfaces and Types
// ==========================================

interface WorkItem {
  id: string;
  type: 'task' | 'bug' | 'feature' | 'epic';
  state: WorkflowState;
  assignee?: User;
  priority: Priority;
  metadata: Record<string, any>;
}

interface WorkflowState {
  id: string;
  name: string;
  isInitial: boolean;
  isFinal: boolean;
  numericPriority: number;
  validTransitions: string[];
}

interface User {
  id: string;
  role: 'developer' | 'product-manager' | 'project-manager' | 'tester';
  teams: string[];
  permissions: string[];
}

interface ExecutionContext {
  user: User;
  workspace: {
    currentProject?: string;
    recentActions: string[];
  };
  personality: PersonalityConfig;
  businessContext: Record<string, any>;
}

interface PersonalityConfig {
  id: string;
  name: string;
  availableOperations: string[];
  restrictions: Record<string, any>;
  workflowHints: Record<string, string[]>;
}

interface SemanticOperation<TParams = any> {
  id: string;
  name: string;
  description: string;
  requiredRoles: string[];
  
  execute(context: ExecutionContext, params: TParams): Promise<SemanticResponse>;
  canExecute(context: ExecutionContext): boolean;
}

interface SemanticResponse {
  content: any[];
  suggestions: string[];
  nextSteps: string[];
  contextualHints: ContextualHint[];
  affectedEntities?: EntityReference[];
}

interface ContextualHint {
  operation: string;
  reason: string;
  applicableRoles: string[];
  businessContext: string;
  priority: 'high' | 'medium' | 'low';
}

interface EntityReference {
  id: string;
  type: string;
  action: 'created' | 'updated' | 'deleted';
}

// ==========================================
// Pattern 1: Multi-Entry Workflow Discovery
// ==========================================

class WorkflowStateManager {
  /**
   * Discovers valid entry points for a work item type based on context
   * Replaces hardcoded initial states with dynamic discovery
   */
  async discoverEntryPoints(
    itemType: string,
    context: ExecutionContext
  ): Promise<WorkflowState[]> {
    // Discover all potential initial states
    const allStates = await this.getStatesForType(itemType);
    const initialStates = allStates.filter(state => state.isInitial);
    
    // Filter by user role and business context
    return initialStates.filter(state => 
      this.isValidEntryPoint(state, context)
    );
  }

  /**
   * Selects the most appropriate entry point based on context
   */
  selectOptimalEntryPoint(
    availableStates: WorkflowState[],
    context: ExecutionContext,
    businessPriority: 'urgent' | 'normal' | 'low'
  ): WorkflowState {
    // Role-based selection
    if (context.user.role === 'developer' && businessPriority === 'urgent') {
      // Developers can bypass triage for urgent items
      return availableStates.find(s => s.name === 'InProgress') || availableStates[0];
    }
    
    if (context.user.role === 'product-manager') {
      // Product managers typically start with planning states
      return availableStates.find(s => s.name === 'Planned') || availableStates[0];
    }
    
    // Default to lowest numeric priority (highest business priority)
    return availableStates.sort((a, b) => a.numericPriority - b.numericPriority)[0];
  }

  private async getStatesForType(itemType: string): Promise<WorkflowState[]> {
    // Abstract state discovery - in practice would query metadata
    return [
      { id: '1', name: 'Open', isInitial: true, isFinal: false, numericPriority: 1, validTransitions: ['InProgress', 'Investigating'] },
      { id: '2', name: 'Planned', isInitial: true, isFinal: false, numericPriority: 2, validTransitions: ['InProgress'] },
      { id: '3', name: 'InProgress', isInitial: true, isFinal: false, numericPriority: 3, validTransitions: ['Done', 'Blocked'] },
      { id: '4', name: 'Done', isInitial: false, isFinal: true, numericPriority: 10, validTransitions: [] }
    ];
  }

  private isValidEntryPoint(state: WorkflowState, context: ExecutionContext): boolean {
    // Business rule validation
    if (state.name === 'InProgress' && !context.user.permissions.includes('bypass-triage')) {
      return false;
    }
    
    // Role-based validation
    if (state.name === 'Planned' && context.user.role !== 'product-manager') {
      return false;
    }
    
    return true;
  }
}

// ==========================================
// Pattern 2: Semantic Guidance Generation
// ==========================================

class SemanticGuidanceEngine {
  /**
   * Generates contextual workflow guidance based on current state and user context
   * Creates emergent workflow patterns without hardcoded sequences
   */
  generateGuidance(
    operationResult: any,
    context: ExecutionContext,
    currentWorkItems: WorkItem[]
  ): ContextualHint[] {
    const hints: ContextualHint[] = [];
    
    // State-based guidance
    hints.push(...this.generateStateBasedHints(currentWorkItems, context));
    
    // Role-based guidance
    hints.push(...this.generateRoleBasedHints(context));
    
    // Business context guidance
    hints.push(...this.generateBusinessContextHints(operationResult, context));
    
    // Workflow continuity guidance
    hints.push(...this.generateContinuityHints(context.workspace.recentActions, context));
    
    return this.prioritizeHints(hints, context);
  }

  private generateStateBasedHints(workItems: WorkItem[], context: ExecutionContext): ContextualHint[] {
    const hints: ContextualHint[] = [];
    
    const blockedItems = workItems.filter(item => item.state.name === 'Blocked');
    if (blockedItems.length > 0) {
      hints.push({
        operation: 'resolve-impediment',
        reason: `${blockedItems.length} work items are blocked and need attention`,
        applicableRoles: ['developer', 'project-manager'],
        businessContext: 'impediment-resolution',
        priority: 'high'
      });
    }
    
    const inProgressItems = workItems.filter(item => item.state.name === 'InProgress');
    if (inProgressItems.length > 3) {
      hints.push({
        operation: 'update-progress',
        reason: 'Multiple items in progress may need status updates',
        applicableRoles: ['developer'],
        businessContext: 'progress-tracking',
        priority: 'medium'
      });
    }
    
    return hints;
  }

  private generateRoleBasedHints(context: ExecutionContext): ContextualHint[] {
    const hints: ContextualHint[] = [];
    
    switch (context.user.role) {
      case 'developer':
        hints.push({
          operation: 'review-assigned-work',
          reason: 'Check for new assignments and priority changes',
          applicableRoles: ['developer'],
          businessContext: 'daily-workflow',
          priority: 'medium'
        });
        break;
        
      case 'product-manager':
        hints.push({
          operation: 'review-backlog-health',
          reason: 'Ensure sufficient planned work for team capacity',
          applicableRoles: ['product-manager'],
          businessContext: 'planning',
          priority: 'medium'
        });
        break;
        
      case 'project-manager':
        hints.push({
          operation: 'assess-delivery-risks',
          reason: 'Monitor project health and identify potential delays',
          applicableRoles: ['project-manager'],
          businessContext: 'risk-management',
          priority: 'high'
        });
        break;
    }
    
    return hints;
  }

  private generateBusinessContextHints(operationResult: any, context: ExecutionContext): ContextualHint[] {
    const hints: ContextualHint[] = [];
    
    // Emergency context
    if (context.businessContext.emergency) {
      hints.push({
        operation: 'escalate-critical-path',
        reason: 'Emergency situation requires immediate escalation',
        applicableRoles: ['developer', 'project-manager'],
        businessContext: 'emergency-response',
        priority: 'high'
      });
    }
    
    // Release context
    if (context.businessContext.nearingRelease) {
      hints.push({
        operation: 'focus-on-release-items',
        reason: 'Release deadline approaching - prioritize committed items',
        applicableRoles: ['developer', 'tester'],
        businessContext: 'release-management',
        priority: 'high'
      });
    }
    
    return hints;
  }

  private generateContinuityHints(recentActions: string[], context: ExecutionContext): ContextualHint[] {
    const hints: ContextualHint[] = [];
    
    const lastAction = recentActions[recentActions.length - 1];
    
    // Workflow continuity patterns
    if (lastAction === 'start-work-item') {
      hints.push({
        operation: 'update-progress',
        reason: 'Recently started work item may need progress logging',
        applicableRoles: ['developer'],
        businessContext: 'work-continuity',
        priority: 'low'
      });
    }
    
    if (lastAction === 'resolve-impediment') {
      hints.push({
        operation: 'resume-blocked-work',
        reason: 'Impediment resolved - blocked work can now continue',
        applicableRoles: ['developer'],
        businessContext: 'impediment-recovery',
        priority: 'medium'
      });
    }
    
    return hints;
  }

  private prioritizeHints(hints: ContextualHint[], context: ExecutionContext): ContextualHint[] {
    // Sort by priority and relevance to current context
    return hints
      .filter(hint => hint.applicableRoles.includes(context.user.role))
      .sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      })
      .slice(0, 5); // Limit to top 5 suggestions to avoid overwhelming users
  }
}

// ==========================================
// Pattern 3: Personality-Based Operation Filtering
// ==========================================

class PersonalityEngine {
  private personalities: Map<string, PersonalityConfig> = new Map();

  constructor() {
    this.initializePersonalities();
  }

  /**
   * Gets available operations for a specific role/personality
   * Enables composable workflows through tool filtering
   */
  getAvailableOperations(personalityId: string): string[] {
    const personality = this.personalities.get(personalityId);
    return personality?.availableOperations || [];
  }

  /**
   * Filters operation results based on personality restrictions
   */
  filterOperationResponse(
    response: SemanticResponse,
    context: ExecutionContext
  ): SemanticResponse {
    const personality = this.personalities.get(context.personality.id);
    if (!personality) return response;

    // Filter suggestions to only include available operations
    const filteredSuggestions = response.suggestions.filter(suggestion => {
      const operationId = suggestion.split(' ')[0];
      return personality.availableOperations.includes(operationId);
    });

    // Filter contextual hints by applicable roles
    const filteredHints = response.contextualHints.filter(hint =>
      hint.applicableRoles.includes(context.user.role)
    );

    return {
      ...response,
      suggestions: filteredSuggestions,
      contextualHints: filteredHints
    };
  }

  private initializePersonalities(): void {
    // Developer personality - focused on implementation
    this.personalities.set('developer', {
      id: 'developer',
      name: 'Developer',
      availableOperations: [
        'show-assigned-work',
        'start-work-item',
        'update-progress',
        'complete-work',
        'resolve-impediment',
        'log-time',
        'request-review'
      ],
      restrictions: {
        editScope: 'assigned',
        allowDelete: false
      },
      workflowHints: {
        dailyStart: ['show-assigned-work'],
        workComplete: ['log-time', 'request-review'],
        blockedWork: ['resolve-impediment', 'escalate-blocker']
      }
    });

    // Product Manager personality - focused on planning
    this.personalities.set('product-manager', {
      id: 'product-manager',
      name: 'Product Manager',
      availableOperations: [
        'manage-backlog',
        'prioritize-items',
        'plan-iteration',
        'define-requirements',
        'review-feedback',
        'forecast-delivery'
      ],
      restrictions: {
        editScope: 'product',
        allowDelete: true
      },
      workflowHints: {
        iterationPlanning: ['review-backlog', 'prioritize-items'],
        feedbackReceived: ['analyze-feedback', 'update-priorities']
      }
    });

    // Project Manager personality - focused on coordination
    this.personalities.set('project-manager', {
      id: 'project-manager',
      name: 'Project Manager',
      availableOperations: [
        'monitor-team-progress',
        'identify-risks',
        'manage-dependencies',
        'generate-reports',
        'coordinate-teams',
        'escalate-issues'
      ],
      restrictions: {
        editScope: 'project',
        allowDelete: false
      },
      workflowHints: {
        dailyStandup: ['monitor-team-progress', 'identify-blockers'],
        riskDetected: ['escalate-issues', 'mitigate-risks']
      }
    });
  }
}

// ==========================================
// Pattern 4: Emergent Workflow Orchestration
// ==========================================

class WorkflowOrchestrator {
  constructor(
    private stateManager: WorkflowStateManager,
    private guidanceEngine: SemanticGuidanceEngine,
    private personalityEngine: PersonalityEngine
  ) {}

  /**
   * Orchestrates complex workflows that emerge from individual operation guidance
   * rather than being hardcoded in the system
   */
  async executeWorkflow(
    initialOperation: string,
    context: ExecutionContext,
    params: any
  ): Promise<SemanticResponse> {
    // Execute the requested operation
    const operation = this.getOperation(initialOperation);
    const result = await operation.execute(context, params);

    // Generate semantic guidance for next steps
    const workItems = await this.getCurrentWorkItems(context);
    const guidance = this.guidanceEngine.generateGuidance(result, context, workItems);

    // Filter based on personality
    const filteredResponse = this.personalityEngine.filterOperationResponse(
      {
        ...result,
        contextualHints: guidance
      },
      context
    );

    // Update context for future operations
    this.updateContext(context, initialOperation, result);

    return filteredResponse;
  }

  /**
   * Demonstrates how workflows emerge naturally from operation chaining
   */
  async demonstrateEmergentWorkflow(context: ExecutionContext): Promise<string[]> {
    const workflowSteps: string[] = [];

    // Step 1: User wants to know their work status
    let response = await this.executeWorkflow('show-assigned-work', context, {});
    workflowSteps.push('User requested work status');
    
    // Step 2: System suggests starting available work
    const suggestedWork = response.suggestions.find(s => s.startsWith('start-work-item'));
    if (suggestedWork) {
      const workItemId = suggestedWork.split(' ')[1];
      response = await this.executeWorkflow('start-work-item', context, { id: workItemId });
      workflowSteps.push('System suggested starting work item, user accepted');
    }

    // Step 3: System suggests progress tracking
    const progressSuggestion = response.suggestions.find(s => s.startsWith('update-progress'));
    if (progressSuggestion) {
      workflowSteps.push('System suggested progress tracking for active work');
    }

    // Step 4: If impediments detected, suggest resolution
    const impedimentHint = response.contextualHints.find(h => h.operation === 'resolve-impediment');
    if (impedimentHint) {
      workflowSteps.push('System detected impediment and suggested resolution workflow');
    }

    return workflowSteps;
  }

  private getOperation(operationId: string): SemanticOperation {
    // Abstract operation lookup - would be implemented by operation registry
    return {
      id: operationId,
      name: operationId,
      description: `Semantic operation: ${operationId}`,
      requiredRoles: [],
      execute: async (context, params) => ({
        content: [{ type: 'text', data: `Executed ${operationId}` }],
        suggestions: [`next-logical-step-after-${operationId}`],
        nextSteps: ['Continue workflow based on context'],
        contextualHints: []
      }),
      canExecute: () => true
    };
  }

  private async getCurrentWorkItems(context: ExecutionContext): Promise<WorkItem[]> {
    // Abstract work item retrieval
    return [];
  }

  private updateContext(context: ExecutionContext, operation: string, result: SemanticResponse): void {
    context.workspace.recentActions.push(operation);
    // Update any affected entities in context
    if (result.affectedEntities) {
      // Track entity changes for future contextual guidance
    }
  }
}

// ==========================================
// Usage Example
// ==========================================

export class SemanticWorkflowSystem {
  private stateManager = new WorkflowStateManager();
  private guidanceEngine = new SemanticGuidanceEngine();
  private personalityEngine = new PersonalityEngine();
  private orchestrator = new WorkflowOrchestrator(
    this.stateManager,
    this.guidanceEngine,
    this.personalityEngine
  );

  /**
   * Example usage demonstrating the key patterns working together
   */
  async demonstratePatterns(): Promise<void> {
    // Create example context
    const context: ExecutionContext = {
      user: {
        id: 'dev-123',
        role: 'developer',
        teams: ['team-alpha'],
        permissions: ['read', 'update']
      },
      workspace: {
        currentProject: 'project-x',
        recentActions: []
      },
      personality: {
        id: 'developer',
        name: 'Developer',
        availableOperations: ['show-assigned-work', 'start-work-item'],
        restrictions: {},
        workflowHints: {}
      },
      businessContext: {
        nearingRelease: true
      }
    };

    // Pattern 1: Multi-entry workflow
    const entryPoints = await this.stateManager.discoverEntryPoints('task', context);
    console.log('Available entry points:', entryPoints.map(ep => ep.name));

    // Pattern 2: Semantic guidance
    const workItems: WorkItem[] = []; // Would be populated from actual data
    const guidance = this.guidanceEngine.generateGuidance({}, context, workItems);
    console.log('Contextual guidance:', guidance);

    // Pattern 3: Personality filtering
    const availableOps = this.personalityEngine.getAvailableOperations('developer');
    console.log('Available operations for developer:', availableOps);

    // Pattern 4: Emergent workflow
    const workflowSteps = await this.orchestrator.demonstrateEmergentWorkflow(context);
    console.log('Emergent workflow steps:', workflowSteps);
  }
}