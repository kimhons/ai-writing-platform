/*
 * Permission Manager - 4-Level Agent Control System
 * Manages agent permissions and approval workflows
 */

/**
 * Permission Manager Class
 * Handles the 4-level permission system for agent autonomy control
 */
export class PermissionManager {
    constructor(wordService) {
        this.wordService = wordService;
        this.currentLevel = 1; // Start with Assistant level (highest control)
        this.approvalQueue = new Map();
        this.permissionHistory = [];
        this.agentCapabilities = new Map();
        
        // Permission level definitions
        this.permissionLevels = {
            1: {
                name: 'Assistant',
                description: 'Every action requires explicit approval',
                icon: '👤',
                color: '#0078d4',
                approvalScope: 'action',
                autoApprove: false,
                maxWordCount: 50,
                allowedActions: ['suggest', 'highlight', 'comment'],
                restrictedActions: ['insert', 'replace', 'delete', 'format']
            },
            2: {
                name: 'Collaborative',
                description: 'Paragraph-level approval required',
                icon: '🤝',
                color: '#107c10',
                approvalScope: 'paragraph',
                autoApprove: false,
                maxWordCount: 200,
                allowedActions: ['suggest', 'highlight', 'comment', 'insert', 'format'],
                restrictedActions: ['replace', 'delete']
            },
            3: {
                name: 'Semi-Autonomous',
                description: 'Section/chapter-level approval',
                icon: '⚡',
                color: '#ff8c00',
                approvalScope: 'section',
                autoApprove: true,
                maxWordCount: 1000,
                allowedActions: ['suggest', 'highlight', 'comment', 'insert', 'replace', 'format'],
                restrictedActions: ['delete']
            },
            4: {
                name: 'Fully Autonomous',
                description: 'Project-level approval only',
                icon: '🚀',
                color: '#d13438',
                approvalScope: 'project',
                autoApprove: true,
                maxWordCount: 10000,
                allowedActions: ['suggest', 'highlight', 'comment', 'insert', 'replace', 'delete', 'format'],
                restrictedActions: []
            }
        };
        
        // Event listeners
        this.eventListeners = new Map();
        
        console.log('Permission Manager initialized with level 1 (Assistant)');
    }

    /**
     * Set permission level for agents
     */
    async setPermissionLevel(level) {
        if (!this.permissionLevels[level]) {
            throw new Error(`Invalid permission level: ${level}`);
        }
        
        const previousLevel = this.currentLevel;
        this.currentLevel = level;
        
        // Log permission change
        this.permissionHistory.push({
            timestamp: new Date().toISOString(),
            previousLevel: previousLevel,
            newLevel: level,
            reason: 'User changed permission level'
        });
        
        // Clear approval queue if moving to higher autonomy
        if (level > previousLevel) {
            await this.clearApprovalQueue('Permission level increased');
        }
        
        // Emit permission change event
        this.emit('permission:changed', {
            previousLevel,
            newLevel: level,
            levelConfig: this.permissionLevels[level]
        });
        
        console.log(`Permission Manager: Level changed from ${previousLevel} to ${level}`, this.permissionLevels[level]);
        
        return {
            success: true,
            level: level,
            config: this.permissionLevels[level]
        };
    }

    /**
     * Check if action requires approval based on current permission level
     */
    requiresApproval(action, agentId = null) {
        const levelConfig = this.permissionLevels[this.currentLevel];
        
        // Level 1 (Assistant) - Everything requires approval
        if (this.currentLevel === 1) {
            return true;
        }
        
        // Check if action is restricted at current level
        if (levelConfig.restrictedActions.includes(action.type)) {
            return true;
        }
        
        // Check word count limits
        if (action.wordCount && action.wordCount > levelConfig.maxWordCount) {
            return true;
        }
        
        // Level 2 (Collaborative) - Paragraph-level approval
        if (this.currentLevel === 2) {
            return action.scope === 'paragraph' || action.scope === 'section' || action.scope === 'document';
        }
        
        // Level 3 (Semi-Autonomous) - Section-level approval
        if (this.currentLevel === 3) {
            return action.scope === 'section' || action.scope === 'document';
        }
        
        // Level 4 (Fully Autonomous) - Project-level approval only
        if (this.currentLevel === 4) {
            return action.scope === 'document' || action.scope === 'project';
        }
        
        return false;
    }

    /**
     * Request approval for agent action
     */
    async requestApproval(action, agentId) {
        const approvalId = `approval-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const levelConfig = this.permissionLevels[this.currentLevel];
        
        const approvalRequest = {
            id: approvalId,
            agentId: agentId,
            action: action,
            permissionLevel: this.currentLevel,
            requestedAt: new Date().toISOString(),
            status: 'pending',
            priority: this.calculatePriority(action),
            estimatedImpact: this.estimateImpact(action),
            timeout: this.calculateTimeout(action)
        };
        
        // Add to approval queue
        this.approvalQueue.set(approvalId, approvalRequest);
        
        // Emit approval request event
        this.emit('approval:requested', approvalRequest);
        
        console.log(`Permission Manager: Approval requested for ${action.type} by ${agentId}`, approvalRequest);
        
        // Auto-approve if level allows and conditions are met
        if (levelConfig.autoApprove && this.shouldAutoApprove(action, agentId)) {
            return await this.autoApprove(approvalId, 'Auto-approved based on permission level');
        }
        
        return {
            approvalId: approvalId,
            status: 'pending',
            requiresUserApproval: true
        };
    }

    /**
     * Approve pending action
     */
    async approveAction(approvalId, reason = '') {
        const approval = this.approvalQueue.get(approvalId);
        if (!approval) {
            throw new Error(`Approval request ${approvalId} not found`);
        }
        
        if (approval.status !== 'pending') {
            throw new Error(`Approval request ${approvalId} is not pending`);
        }
        
        // Update approval status
        approval.status = 'approved';
        approval.approvedAt = new Date().toISOString();
        approval.approvalReason = reason;
        
        // Execute the approved action
        try {
            const result = await this.executeApprovedAction(approval);
            
            approval.executionResult = result;
            approval.executedAt = new Date().toISOString();
            
            // Remove from queue
            this.approvalQueue.delete(approvalId);
            
            // Emit approval event
            this.emit('approval:approved', approval);
            
            console.log(`Permission Manager: Action approved and executed`, approvalId, result);
            
            return {
                success: true,
                approvalId: approvalId,
                executionResult: result
            };
            
        } catch (error) {
            approval.status = 'execution_failed';
            approval.executionError = error.message;
            
            console.error(`Permission Manager: Failed to execute approved action`, approvalId, error);
            throw error;
        }
    }

    /**
     * Reject pending action
     */
    async rejectAction(approvalId, reason = '') {
        const approval = this.approvalQueue.get(approvalId);
        if (!approval) {
            throw new Error(`Approval request ${approvalId} not found`);
        }
        
        if (approval.status !== 'pending') {
            throw new Error(`Approval request ${approvalId} is not pending`);
        }
        
        // Update approval status
        approval.status = 'rejected';
        approval.rejectedAt = new Date().toISOString();
        approval.rejectionReason = reason;
        
        // Remove from queue
        this.approvalQueue.delete(approvalId);
        
        // Emit rejection event
        this.emit('approval:rejected', approval);
        
        console.log(`Permission Manager: Action rejected`, approvalId, reason);
        
        return {
            success: true,
            approvalId: approvalId,
            status: 'rejected',
            reason: reason
        };
    }

    /**
     * Auto-approve action based on permission level
     */
    async autoApprove(approvalId, reason) {
        const approval = this.approvalQueue.get(approvalId);
        if (!approval) {
            throw new Error(`Approval request ${approvalId} not found`);
        }
        
        approval.status = 'auto_approved';
        approval.autoApprovedAt = new Date().toISOString();
        approval.autoApprovalReason = reason;
        
        try {
            const result = await this.executeApprovedAction(approval);
            
            approval.executionResult = result;
            approval.executedAt = new Date().toISOString();
            
            // Remove from queue
            this.approvalQueue.delete(approvalId);
            
            // Emit auto-approval event
            this.emit('approval:auto_approved', approval);
            
            console.log(`Permission Manager: Action auto-approved and executed`, approvalId, result);
            
            return {
                success: true,
                approvalId: approvalId,
                status: 'auto_approved',
                executionResult: result
            };
            
        } catch (error) {
            approval.status = 'execution_failed';
            approval.executionError = error.message;
            
            console.error(`Permission Manager: Failed to execute auto-approved action`, approvalId, error);
            throw error;
        }
    }

    /**
     * Execute approved action through Word service
     */
    async executeApprovedAction(approval) {
        const { action, agentId } = approval;
        
        switch (action.type) {
            case 'insert':
                return await this.wordService.insertContent(action.content, {
                    location: action.location,
                    formatting: action.formatting,
                    agentId: agentId
                });
                
            case 'replace':
                return await this.wordService.replaceContent(
                    action.oldContent,
                    action.newContent,
                    { agentId: agentId }
                );
                
            case 'comment':
                return await this.wordService.addComment(
                    action.text,
                    action.suggestion,
                    { agentId: agentId, suggestionType: action.suggestionType }
                );
                
            case 'highlight':
                return await this.wordService.highlightText(action.text, {
                    color: action.color,
                    agentId: agentId,
                    reason: action.reason
                });
                
            case 'format':
                return await this.wordService.applyFormatting(action.range, action.formatting);
                
            default:
                throw new Error(`Unknown action type: ${action.type}`);
        }
    }

    /**
     * Check if action should be auto-approved
     */
    shouldAutoApprove(action, agentId) {
        const levelConfig = this.permissionLevels[this.currentLevel];
        
        // Never auto-approve if level doesn't allow it
        if (!levelConfig.autoApprove) {
            return false;
        }
        
        // Check agent trust level
        const agentCapability = this.agentCapabilities.get(agentId);
        if (agentCapability && agentCapability.trustLevel < 0.8) {
            return false;
        }
        
        // Check action safety
        if (action.type === 'delete' || action.type === 'replace') {
            return false; // Always require explicit approval for destructive actions
        }
        
        // Check word count limits
        if (action.wordCount && action.wordCount > levelConfig.maxWordCount * 0.5) {
            return false; // Require approval for large changes
        }
        
        return true;
    }

    /**
     * Calculate priority for approval request
     */
    calculatePriority(action) {
        let priority = 'medium';
        
        // High priority for destructive actions
        if (action.type === 'delete' || action.type === 'replace') {
            priority = 'high';
        }
        
        // Low priority for suggestions and comments
        if (action.type === 'suggest' || action.type === 'comment') {
            priority = 'low';
        }
        
        // Increase priority for large word counts
        if (action.wordCount && action.wordCount > 500) {
            priority = priority === 'low' ? 'medium' : 'high';
        }
        
        return priority;
    }

    /**
     * Estimate impact of action
     */
    estimateImpact(action) {
        const impact = {
            wordCount: action.wordCount || 0,
            scope: action.scope || 'word',
            reversible: true,
            riskLevel: 'low'
        };
        
        // Assess reversibility
        if (action.type === 'delete') {
            impact.reversible = false;
            impact.riskLevel = 'high';
        }
        
        // Assess scope impact
        if (action.scope === 'document' || action.scope === 'section') {
            impact.riskLevel = impact.riskLevel === 'low' ? 'medium' : 'high';
        }
        
        return impact;
    }

    /**
     * Calculate timeout for approval request
     */
    calculateTimeout(action) {
        const baseTimeout = 300000; // 5 minutes
        
        // Longer timeout for high-impact actions
        if (action.scope === 'document' || action.wordCount > 1000) {
            return baseTimeout * 2; // 10 minutes
        }
        
        // Shorter timeout for simple actions
        if (action.type === 'suggest' || action.type === 'comment') {
            return baseTimeout / 2; // 2.5 minutes
        }
        
        return baseTimeout;
    }

    /**
     * Clear approval queue
     */
    async clearApprovalQueue(reason = 'Queue cleared') {
        const clearedCount = this.approvalQueue.size;
        
        // Reject all pending approvals
        for (const [approvalId, approval] of this.approvalQueue) {
            approval.status = 'cancelled';
            approval.cancelledAt = new Date().toISOString();
            approval.cancellationReason = reason;
            
            this.emit('approval:cancelled', approval);
        }
        
        this.approvalQueue.clear();
        
        console.log(`Permission Manager: Cleared ${clearedCount} pending approvals`, reason);
        
        return {
            success: true,
            clearedCount: clearedCount,
            reason: reason
        };
    }

    /**
     * Get pending approvals
     */
    getPendingApprovals() {
        return Array.from(this.approvalQueue.values())
            .filter(approval => approval.status === 'pending')
            .sort((a, b) => {
                // Sort by priority and timestamp
                const priorityOrder = { high: 3, medium: 2, low: 1 };
                const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
                
                if (priorityDiff !== 0) return priorityDiff;
                
                return new Date(a.requestedAt) - new Date(b.requestedAt);
            });
    }

    /**
     * Get approval history
     */
    getApprovalHistory(limit = 50) {
        return this.permissionHistory
            .slice(-limit)
            .reverse();
    }

    /**
     * Set agent capabilities and trust level
     */
    setAgentCapabilities(agentId, capabilities) {
        this.agentCapabilities.set(agentId, {
            ...capabilities,
            updatedAt: new Date().toISOString()
        });
        
        console.log(`Permission Manager: Agent capabilities updated for ${agentId}`, capabilities);
    }

    /**
     * Get current permission level configuration
     */
    getCurrentLevelConfig() {
        return {
            level: this.currentLevel,
            config: this.permissionLevels[this.currentLevel]
        };
    }

    /**
     * Get all permission levels
     */
    getAllLevels() {
        return this.permissionLevels;
    }

    /**
     * Check if agent can perform action
     */
    canAgentPerformAction(agentId, actionType) {
        const levelConfig = this.permissionLevels[this.currentLevel];
        
        // Check if action is allowed at current level
        if (!levelConfig.allowedActions.includes(actionType)) {
            return {
                allowed: false,
                reason: `Action ${actionType} not allowed at permission level ${this.currentLevel}`
            };
        }
        
        // Check if action is restricted
        if (levelConfig.restrictedActions.includes(actionType)) {
            return {
                allowed: false,
                reason: `Action ${actionType} is restricted at permission level ${this.currentLevel}`
            };
        }
        
        return {
            allowed: true,
            requiresApproval: this.requiresApproval({ type: actionType }, agentId)
        };
    }

    /**
     * Event system methods
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Permission Manager: Error in event listener for ${event}`, error);
                }
            });
        }
    }

    /**
     * Get permission statistics
     */
    getPermissionStats() {
        const pendingCount = this.getPendingApprovals().length;
        const totalRequests = this.permissionHistory.length;
        
        return {
            currentLevel: this.currentLevel,
            pendingApprovals: pendingCount,
            totalRequests: totalRequests,
            queueSize: this.approvalQueue.size,
            activeAgents: this.agentCapabilities.size
        };
    }

    /**
     * Cleanup resources
     */
    destroy() {
        this.approvalQueue.clear();
        this.permissionHistory = [];
        this.agentCapabilities.clear();
        this.eventListeners.clear();
    }
}

