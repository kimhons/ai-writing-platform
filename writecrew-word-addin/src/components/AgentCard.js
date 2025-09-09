/**
 * AgentCard Component
 * Displays individual agent status, capabilities, and controls
 */

class AgentCard {
    constructor(agent, permissionManager, onAgentAction) {
        this.agent = agent;
        this.permissionManager = permissionManager;
        this.onAgentAction = onAgentAction;
        this.isExpanded = false;
        this.element = null;
        
        this.init();
    }
    
    init() {
        this.element = this.createElement();
        this.attachEventListeners();
    }
    
    createElement() {
        const card = document.createElement('div');
        card.className = `agent-card ${this.agent.status}`;
        card.setAttribute('data-agent-id', this.agent.id);
        
        card.innerHTML = `
            <div class="agent-card-header" role="button" tabindex="0" aria-expanded="false">
                <div class="agent-info">
                    <div class="agent-avatar">
                        <span class="agent-icon">${this.getAgentIcon()}</span>
                        <div class="agent-status-indicator ${this.agent.status}"></div>
                    </div>
                    <div class="agent-details">
                        <h3 class="agent-name">${this.agent.name}</h3>
                        <p class="agent-specialty">${this.agent.specialty}</p>
                        <div class="agent-metrics">
                            <span class="metric">
                                <span class="metric-value">${this.agent.tasksCompleted || 0}</span>
                                <span class="metric-label">Tasks</span>
                            </span>
                            <span class="metric">
                                <span class="metric-value">${this.agent.wordsGenerated || 0}</span>
                                <span class="metric-label">Words</span>
                            </span>
                            <span class="metric">
                                <span class="metric-value">$${(this.agent.costIncurred || 0).toFixed(2)}</span>
                                <span class="metric-label">Cost</span>
                            </span>
                        </div>
                    </div>
                </div>
                <div class="agent-controls">
                    <div class="permission-level">
                        <span class="permission-indicator level-${this.agent.permissionLevel}">
                            ${this.getPermissionIcon()}
                        </span>
                    </div>
                    <button class="expand-toggle" aria-label="Expand agent details">
                        <span class="expand-icon">▼</span>
                    </button>
                </div>
            </div>
            
            <div class="agent-card-body" style="display: none;">
                <div class="agent-capabilities">
                    <h4>Capabilities</h4>
                    <div class="capability-tags">
                        ${this.agent.capabilities.map(cap => 
                            `<span class="capability-tag">${cap}</span>`
                        ).join('')}
                    </div>
                </div>
                
                <div class="agent-permissions">
                    <h4>Permission Level</h4>
                    <div class="permission-selector">
                        <select class="permission-dropdown" aria-label="Agent permission level">
                            <option value="1" ${this.agent.permissionLevel === 1 ? 'selected' : ''}>
                                👤 Assistant (High Control)
                            </option>
                            <option value="2" ${this.agent.permissionLevel === 2 ? 'selected' : ''}>
                                🤝 Collaborative (Medium Control)
                            </option>
                            <option value="3" ${this.agent.permissionLevel === 3 ? 'selected' : ''}>
                                ⚡ Semi-Autonomous (Low Control)
                            </option>
                            <option value="4" ${this.agent.permissionLevel === 4 ? 'selected' : ''}>
                                🚀 Fully Autonomous (Minimal Control)
                            </option>
                        </select>
                    </div>
                    <p class="permission-description">
                        ${this.getPermissionDescription()}
                    </p>
                </div>
                
                <div class="agent-activity">
                    <h4>Recent Activity</h4>
                    <div class="activity-feed">
                        ${this.renderActivityFeed()}
                    </div>
                </div>
                
                <div class="agent-actions">
                    <button class="btn btn-primary start-agent" ${this.agent.status === 'active' ? 'disabled' : ''}>
                        ${this.agent.status === 'active' ? 'Active' : 'Activate Agent'}
                    </button>
                    <button class="btn btn-secondary pause-agent" ${this.agent.status !== 'active' ? 'disabled' : ''}>
                        Pause
                    </button>
                    <button class="btn btn-outline settings-agent">
                        Settings
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    attachEventListeners() {
        const header = this.element.querySelector('.agent-card-header');
        const expandToggle = this.element.querySelector('.expand-toggle');
        const permissionDropdown = this.element.querySelector('.permission-dropdown');
        const startButton = this.element.querySelector('.start-agent');
        const pauseButton = this.element.querySelector('.pause-agent');
        const settingsButton = this.element.querySelector('.settings-agent');
        
        // Toggle expansion
        const toggleExpansion = () => {
            this.isExpanded = !this.isExpanded;
            const body = this.element.querySelector('.agent-card-body');
            const icon = this.element.querySelector('.expand-icon');
            
            if (this.isExpanded) {
                body.style.display = 'block';
                icon.textContent = '▲';
                header.setAttribute('aria-expanded', 'true');
            } else {
                body.style.display = 'none';
                icon.textContent = '▼';
                header.setAttribute('aria-expanded', 'false');
            }
        };
        
        header.addEventListener('click', toggleExpansion);
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleExpansion();
            }
        });
        
        // Permission level change
        permissionDropdown.addEventListener('change', async (e) => {
            const newLevel = parseInt(e.target.value);
            try {
                await this.permissionManager.updateAgentPermission(this.agent.id, newLevel);
                this.agent.permissionLevel = newLevel;
                this.updatePermissionIndicator();
                this.updatePermissionDescription();
                
                // Trigger callback
                if (this.onAgentAction) {
                    this.onAgentAction('permission_changed', {
                        agentId: this.agent.id,
                        newLevel: newLevel
                    });
                }
            } catch (error) {
                console.error('Failed to update permission level:', error);
                // Revert dropdown
                e.target.value = this.agent.permissionLevel;
            }
        });
        
        // Agent control buttons
        startButton.addEventListener('click', () => {
            this.onAgentAction('start', { agentId: this.agent.id });
        });
        
        pauseButton.addEventListener('click', () => {
            this.onAgentAction('pause', { agentId: this.agent.id });
        });
        
        settingsButton.addEventListener('click', () => {
            this.onAgentAction('settings', { agentId: this.agent.id });
        });
    }
    
    getAgentIcon() {
        const iconMap = {
            'master_router': '🎯',
            'content_writer': '✍️',
            'research_agent': '🔍',
            'style_editor': '🎨',
            'grammar_assistant': '📝',
            'structure_architect': '🏗️',
            'legal_expert': '⚖️',
            'medical_expert': '🏥',
            'technical_expert': '⚙️',
            'academic_expert': '🎓'
        };
        return iconMap[this.agent.id] || '🤖';
    }
    
    getPermissionIcon() {
        const iconMap = {
            1: '👤',
            2: '🤝',
            3: '⚡',
            4: '🚀'
        };
        return iconMap[this.agent.permissionLevel] || '👤';
    }
    
    getPermissionDescription() {
        const descriptions = {
            1: 'Agent suggests changes but requires approval for every action. Maximum safety and control.',
            2: 'Agent can make direct edits but requires approval per paragraph. Balanced collaboration.',
            3: 'Agent works independently but requires approval per section. High productivity mode.',
            4: 'Agent works with minimal oversight, requiring approval only at major milestones. Use with trusted agents.'
        };
        return descriptions[this.agent.permissionLevel] || descriptions[1];
    }
    
    renderActivityFeed() {
        if (!this.agent.recentActivity || this.agent.recentActivity.length === 0) {
            return '<p class="no-activity">No recent activity</p>';
        }
        
        return this.agent.recentActivity.slice(0, 3).map(activity => `
            <div class="activity-item">
                <span class="activity-time">${this.formatTime(activity.timestamp)}</span>
                <span class="activity-description">${activity.description}</span>
            </div>
        `).join('');
    }
    
    formatTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return time.toLocaleDateString();
    }
    
    updateStatus(newStatus) {
        this.agent.status = newStatus;
        this.element.className = `agent-card ${newStatus}`;
        
        const statusIndicator = this.element.querySelector('.agent-status-indicator');
        statusIndicator.className = `agent-status-indicator ${newStatus}`;
        
        const startButton = this.element.querySelector('.start-agent');
        const pauseButton = this.element.querySelector('.pause-agent');
        
        if (newStatus === 'active') {
            startButton.disabled = true;
            startButton.textContent = 'Active';
            pauseButton.disabled = false;
        } else {
            startButton.disabled = false;
            startButton.textContent = 'Activate Agent';
            pauseButton.disabled = true;
        }
    }
    
    updateMetrics(metrics) {
        const metricsElement = this.element.querySelector('.agent-metrics');
        metricsElement.innerHTML = `
            <span class="metric">
                <span class="metric-value">${metrics.tasksCompleted || 0}</span>
                <span class="metric-label">Tasks</span>
            </span>
            <span class="metric">
                <span class="metric-value">${metrics.wordsGenerated || 0}</span>
                <span class="metric-label">Words</span>
            </span>
            <span class="metric">
                <span class="metric-value">$${(metrics.costIncurred || 0).toFixed(2)}</span>
                <span class="metric-label">Cost</span>
            </span>
        `;
        
        // Update agent object
        Object.assign(this.agent, metrics);
    }
    
    updatePermissionIndicator() {
        const indicator = this.element.querySelector('.permission-indicator');
        indicator.className = `permission-indicator level-${this.agent.permissionLevel}`;
        indicator.textContent = this.getPermissionIcon();
    }
    
    updatePermissionDescription() {
        const description = this.element.querySelector('.permission-description');
        description.textContent = this.getPermissionDescription();
    }
    
    addActivity(activity) {
        if (!this.agent.recentActivity) {
            this.agent.recentActivity = [];
        }
        
        this.agent.recentActivity.unshift(activity);
        
        // Keep only last 10 activities
        if (this.agent.recentActivity.length > 10) {
            this.agent.recentActivity = this.agent.recentActivity.slice(0, 10);
        }
        
        // Update activity feed if expanded
        if (this.isExpanded) {
            const activityFeed = this.element.querySelector('.activity-feed');
            activityFeed.innerHTML = this.renderActivityFeed();
        }
    }
    
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AgentCard;
} else {
    window.AgentCard = AgentCard;
}

