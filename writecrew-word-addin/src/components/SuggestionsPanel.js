/**
 * SuggestionsPanel Component
 * Displays agent suggestions in track changes style with approval workflow
 */

class SuggestionsPanel {
    constructor(wordService, permissionManager, onSuggestionAction) {
        this.wordService = wordService;
        this.permissionManager = permissionManager;
        this.onSuggestionAction = onSuggestionAction;
        this.element = null;
        this.suggestions = [];
        this.filters = {
            status: 'all', // all, pending, approved, rejected
            agent: 'all',
            type: 'all' // all, content, grammar, style, structure
        };
        this.sortBy = 'timestamp'; // timestamp, priority, agent
        
        this.init();
    }
    
    init() {
        this.element = this.createElement();
        this.attachEventListeners();
        this.loadSuggestions();
    }
    
    createElement() {
        const panel = document.createElement('div');
        panel.className = 'suggestions-panel';
        
        panel.innerHTML = `
            <div class="suggestions-header">
                <div class="header-title">
                    <h3>Agent Suggestions</h3>
                    <div class="suggestion-count">
                        <span class="count">0</span> suggestions
                    </div>
                </div>
                
                <div class="header-controls">
                    <div class="filter-controls">
                        <select class="filter-status" aria-label="Filter by status">
                            <option value="all">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
                        </select>
                        
                        <select class="filter-agent" aria-label="Filter by agent">
                            <option value="all">All Agents</option>
                            <option value="content_writer">✍️ Content Writer</option>
                            <option value="research_agent">🔍 Research Agent</option>
                            <option value="style_editor">🎨 Style Editor</option>
                            <option value="grammar_assistant">📝 Grammar Assistant</option>
                            <option value="structure_architect">🏗️ Structure Architect</option>
                            <option value="legal_expert">⚖️ Legal Expert</option>
                            <option value="medical_expert">🏥 Medical Expert</option>
                            <option value="technical_expert">⚙️ Technical Expert</option>
                            <option value="academic_expert">🎓 Academic Expert</option>
                        </select>
                        
                        <select class="filter-type" aria-label="Filter by type">
                            <option value="all">All Types</option>
                            <option value="content">Content</option>
                            <option value="grammar">Grammar</option>
                            <option value="style">Style</option>
                            <option value="structure">Structure</option>
                            <option value="research">Research</option>
                        </select>
                    </div>
                    
                    <div class="action-controls">
                        <button class="bulk-approve" title="Approve all visible suggestions" disabled>
                            ✅ Approve All
                        </button>
                        <button class="bulk-reject" title="Reject all visible suggestions" disabled>
                            ❌ Reject All
                        </button>
                        <button class="refresh-suggestions" title="Refresh suggestions">
                            🔄
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="suggestions-content">
                <div class="suggestions-list" role="list" aria-label="Agent suggestions">
                    <div class="empty-state">
                        <div class="empty-icon">💡</div>
                        <h4>No suggestions yet</h4>
                        <p>Agent suggestions will appear here as you work on your document.</p>
                        <button class="request-suggestions">Request Suggestions</button>
                    </div>
                </div>
            </div>
            
            <div class="suggestions-footer">
                <div class="footer-stats">
                    <span class="stat">
                        <span class="stat-value" data-stat="pending">0</span>
                        <span class="stat-label">Pending</span>
                    </span>
                    <span class="stat">
                        <span class="stat-value" data-stat="approved">0</span>
                        <span class="stat-label">Approved</span>
                    </span>
                    <span class="stat">
                        <span class="stat-value" data-stat="rejected">0</span>
                        <span class="stat-label">Rejected</span>
                    </span>
                </div>
                
                <div class="footer-actions">
                    <button class="clear-approved" title="Clear approved suggestions">
                        🗑️ Clear Approved
                    </button>
                    <button class="export-suggestions" title="Export suggestions">
                        📤 Export
                    </button>
                </div>
            </div>
        `;
        
        return panel;
    }
    
    attachEventListeners() {
        // Filter controls
        const statusFilter = this.element.querySelector('.filter-status');
        const agentFilter = this.element.querySelector('.filter-agent');
        const typeFilter = this.element.querySelector('.filter-type');
        
        statusFilter.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.applyFilters();
        });
        
        agentFilter.addEventListener('change', (e) => {
            this.filters.agent = e.target.value;
            this.applyFilters();
        });
        
        typeFilter.addEventListener('change', (e) => {
            this.filters.type = e.target.value;
            this.applyFilters();
        });
        
        // Action controls
        const bulkApprove = this.element.querySelector('.bulk-approve');
        const bulkReject = this.element.querySelector('.bulk-reject');
        const refreshBtn = this.element.querySelector('.refresh-suggestions');
        const requestBtn = this.element.querySelector('.request-suggestions');
        const clearApproved = this.element.querySelector('.clear-approved');
        const exportBtn = this.element.querySelector('.export-suggestions');
        
        bulkApprove.addEventListener('click', () => {
            this.bulkApproveVisible();
        });
        
        bulkReject.addEventListener('click', () => {
            this.bulkRejectVisible();
        });
        
        refreshBtn.addEventListener('click', () => {
            this.refreshSuggestions();
        });
        
        requestBtn.addEventListener('click', () => {
            this.requestSuggestions();
        });
        
        clearApproved.addEventListener('click', () => {
            this.clearApproved();
        });
        
        exportBtn.addEventListener('click', () => {
            this.exportSuggestions();
        });
    }
    
    addSuggestion(suggestion) {
        // Ensure suggestion has required properties
        const fullSuggestion = {
            id: suggestion.id || `sug_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            agentId: suggestion.agentId,
            type: suggestion.type || 'content',
            status: suggestion.status || 'pending',
            priority: suggestion.priority || 'medium',
            timestamp: suggestion.timestamp || new Date(),
            title: suggestion.title || 'Suggestion',
            description: suggestion.description || '',
            originalText: suggestion.originalText || '',
            suggestedText: suggestion.suggestedText || '',
            reasoning: suggestion.reasoning || '',
            confidence: suggestion.confidence || 0.8,
            location: suggestion.location || { paragraph: 0, sentence: 0 },
            cost: suggestion.cost || 0,
            ...suggestion
        };
        
        this.suggestions.unshift(fullSuggestion);
        this.renderSuggestions();
        this.updateStats();
        this.updateBulkActionButtons();
        
        // Highlight in document if location provided
        if (fullSuggestion.location && this.wordService) {
            this.highlightSuggestionInDocument(fullSuggestion);
        }
    }
    
    renderSuggestions() {
        const listContainer = this.element.querySelector('.suggestions-list');
        const filteredSuggestions = this.getFilteredSuggestions();
        
        if (filteredSuggestions.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">💡</div>
                    <h4>No suggestions match your filters</h4>
                    <p>Try adjusting your filters or request new suggestions.</p>
                    <button class="request-suggestions">Request Suggestions</button>
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = '';
        
        filteredSuggestions.forEach(suggestion => {
            const suggestionElement = this.createSuggestionElement(suggestion);
            listContainer.appendChild(suggestionElement);
        });
        
        this.updateSuggestionCount(filteredSuggestions.length);
    }
    
    createSuggestionElement(suggestion) {
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = `suggestion-item ${suggestion.status} priority-${suggestion.priority}`;
        suggestionDiv.setAttribute('data-suggestion-id', suggestion.id);
        suggestionDiv.setAttribute('role', 'listitem');
        
        const agentName = this.getAgentName(suggestion.agentId);
        const agentIcon = this.getAgentIcon(suggestion.agentId);
        const timestamp = this.formatTimestamp(suggestion.timestamp);
        
        suggestionDiv.innerHTML = `
            <div class="suggestion-header">
                <div class="suggestion-meta">
                    <span class="agent-info">
                        <span class="agent-icon">${agentIcon}</span>
                        <span class="agent-name">${agentName}</span>
                    </span>
                    <span class="suggestion-type ${suggestion.type}">${this.capitalizeFirst(suggestion.type)}</span>
                    <span class="suggestion-priority priority-${suggestion.priority}">
                        ${this.getPriorityIcon(suggestion.priority)}
                    </span>
                </div>
                <div class="suggestion-actions">
                    <span class="suggestion-time" title="${new Date(suggestion.timestamp).toLocaleString()}">
                        ${timestamp}
                    </span>
                    <div class="action-buttons">
                        ${suggestion.status === 'pending' ? `
                            <button class="action-btn approve-btn" title="Approve suggestion" data-action="approve">
                                ✅
                            </button>
                            <button class="action-btn reject-btn" title="Reject suggestion" data-action="reject">
                                ❌
                            </button>
                        ` : ''}
                        <button class="action-btn more-btn" title="More options" data-action="more">
                            ⋯
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="suggestion-content">
                <div class="suggestion-title">
                    <h4>${this.escapeHtml(suggestion.title)}</h4>
                    ${suggestion.confidence ? `
                        <span class="confidence-badge" title="Confidence: ${(suggestion.confidence * 100).toFixed(0)}%">
                            ${(suggestion.confidence * 100).toFixed(0)}%
                        </span>
                    ` : ''}
                </div>
                
                ${suggestion.description ? `
                    <div class="suggestion-description">
                        <p>${this.escapeHtml(suggestion.description)}</p>
                    </div>
                ` : ''}
                
                ${suggestion.originalText || suggestion.suggestedText ? `
                    <div class="text-comparison">
                        ${suggestion.originalText ? `
                            <div class="original-text">
                                <label>Original:</label>
                                <div class="text-content">${this.escapeHtml(suggestion.originalText)}</div>
                            </div>
                        ` : ''}
                        ${suggestion.suggestedText ? `
                            <div class="suggested-text">
                                <label>Suggested:</label>
                                <div class="text-content">${this.escapeHtml(suggestion.suggestedText)}</div>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                
                ${suggestion.reasoning ? `
                    <div class="suggestion-reasoning">
                        <details>
                            <summary>Reasoning</summary>
                            <p>${this.escapeHtml(suggestion.reasoning)}</p>
                        </details>
                    </div>
                ` : ''}
            </div>
            
            <div class="suggestion-footer">
                <div class="suggestion-stats">
                    ${suggestion.location ? `
                        <span class="location-info" title="Document location">
                            📍 Paragraph ${suggestion.location.paragraph + 1}
                        </span>
                    ` : ''}
                    ${suggestion.cost ? `
                        <span class="cost-info" title="Processing cost">
                            💰 $${suggestion.cost.toFixed(4)}
                        </span>
                    ` : ''}
                </div>
                
                ${suggestion.status !== 'pending' ? `
                    <div class="status-info">
                        <span class="status-badge ${suggestion.status}">
                            ${suggestion.status === 'approved' ? '✅ Approved' : '❌ Rejected'}
                        </span>
                        ${suggestion.statusTimestamp ? `
                            <span class="status-time">
                                ${this.formatTimestamp(suggestion.statusTimestamp)}
                            </span>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
        
        this.attachSuggestionEventListeners(suggestionDiv, suggestion);
        
        return suggestionDiv;
    }
    
    attachSuggestionEventListeners(element, suggestion) {
        const actionButtons = element.querySelectorAll('.action-btn');
        
        actionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                this.handleSuggestionAction(suggestion.id, action, btn);
            });
        });
        
        // Click to navigate to suggestion location
        element.addEventListener('click', () => {
            if (suggestion.location && this.wordService) {
                this.navigateToSuggestion(suggestion);
            }
        });
    }
    
    async handleSuggestionAction(suggestionId, action, buttonElement) {
        const suggestion = this.suggestions.find(s => s.id === suggestionId);
        if (!suggestion) return;
        
        try {
            switch (action) {
                case 'approve':
                    await this.approveSuggestion(suggestion);
                    break;
                case 'reject':
                    await this.rejectSuggestion(suggestion);
                    break;
                case 'more':
                    this.showSuggestionMenu(suggestion, buttonElement);
                    break;
            }
        } catch (error) {
            console.error(`Error handling suggestion action ${action}:`, error);
        }
    }
    
    async approveSuggestion(suggestion) {
        // Check permissions
        const canApprove = await this.permissionManager.canApproveAction(
            'suggestion_approval',
            suggestion.agentId
        );
        
        if (!canApprove) {
            alert('You do not have permission to approve this suggestion.');
            return;
        }
        
        // Apply suggestion to document
        if (suggestion.suggestedText && this.wordService) {
            await this.wordService.applySuggestion(suggestion);
        }
        
        // Update suggestion status
        suggestion.status = 'approved';
        suggestion.statusTimestamp = new Date();
        
        // Re-render
        this.renderSuggestions();
        this.updateStats();
        this.updateBulkActionButtons();
        
        // Trigger callback
        if (this.onSuggestionAction) {
            this.onSuggestionAction('approved', suggestion);
        }
        
        // Remove highlight from document
        this.removeHighlightFromDocument(suggestion);
    }
    
    async rejectSuggestion(suggestion) {
        // Update suggestion status
        suggestion.status = 'rejected';
        suggestion.statusTimestamp = new Date();
        
        // Re-render
        this.renderSuggestions();
        this.updateStats();
        this.updateBulkActionButtons();
        
        // Trigger callback
        if (this.onSuggestionAction) {
            this.onSuggestionAction('rejected', suggestion);
        }
        
        // Remove highlight from document
        this.removeHighlightFromDocument(suggestion);
    }
    
    showSuggestionMenu(suggestion, buttonElement) {
        // Create context menu
        const menu = document.createElement('div');
        menu.className = 'suggestion-context-menu';
        menu.innerHTML = `
            <div class="menu-item" data-action="copy">📋 Copy Text</div>
            <div class="menu-item" data-action="edit">✏️ Edit Suggestion</div>
            <div class="menu-item" data-action="feedback">💬 Provide Feedback</div>
            <div class="menu-separator"></div>
            <div class="menu-item" data-action="navigate">📍 Go to Location</div>
            <div class="menu-item" data-action="details">ℹ️ View Details</div>
            ${suggestion.status === 'pending' ? '' : `
                <div class="menu-separator"></div>
                <div class="menu-item" data-action="revert">↩️ Revert Status</div>
            `}
        `;
        
        // Position menu
        const rect = buttonElement.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.top = `${rect.bottom + 5}px`;
        menu.style.left = `${rect.left}px`;
        menu.style.zIndex = '1000';
        
        document.body.appendChild(menu);
        
        // Handle menu clicks
        menu.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action) {
                this.handleMenuAction(suggestion, action);
            }
            document.body.removeChild(menu);
        });
        
        // Close menu on outside click
        const closeMenu = (e) => {
            if (!menu.contains(e.target)) {
                document.body.removeChild(menu);
                document.removeEventListener('click', closeMenu);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 100);
    }
    
    handleMenuAction(suggestion, action) {
        switch (action) {
            case 'copy':
                navigator.clipboard.writeText(suggestion.suggestedText || suggestion.description);
                break;
            case 'edit':
                this.editSuggestion(suggestion);
                break;
            case 'feedback':
                this.provideFeedback(suggestion);
                break;
            case 'navigate':
                this.navigateToSuggestion(suggestion);
                break;
            case 'details':
                this.showSuggestionDetails(suggestion);
                break;
            case 'revert':
                this.revertSuggestionStatus(suggestion);
                break;
        }
    }
    
    getFilteredSuggestions() {
        return this.suggestions.filter(suggestion => {
            if (this.filters.status !== 'all' && suggestion.status !== this.filters.status) {
                return false;
            }
            if (this.filters.agent !== 'all' && suggestion.agentId !== this.filters.agent) {
                return false;
            }
            if (this.filters.type !== 'all' && suggestion.type !== this.filters.type) {
                return false;
            }
            return true;
        }).sort((a, b) => {
            if (this.sortBy === 'timestamp') {
                return new Date(b.timestamp) - new Date(a.timestamp);
            } else if (this.sortBy === 'priority') {
                const priorityOrder = { high: 3, medium: 2, low: 1 };
                return priorityOrder[b.priority] - priorityOrder[a.priority];
            }
            return 0;
        });
    }
    
    applyFilters() {
        this.renderSuggestions();
        this.updateBulkActionButtons();
    }
    
    updateStats() {
        const stats = {
            pending: this.suggestions.filter(s => s.status === 'pending').length,
            approved: this.suggestions.filter(s => s.status === 'approved').length,
            rejected: this.suggestions.filter(s => s.status === 'rejected').length
        };
        
        Object.entries(stats).forEach(([key, value]) => {
            const element = this.element.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    updateSuggestionCount(count) {
        const countElement = this.element.querySelector('.suggestion-count .count');
        countElement.textContent = count;
    }
    
    updateBulkActionButtons() {
        const filteredSuggestions = this.getFilteredSuggestions();
        const pendingSuggestions = filteredSuggestions.filter(s => s.status === 'pending');
        
        const bulkApprove = this.element.querySelector('.bulk-approve');
        const bulkReject = this.element.querySelector('.bulk-reject');
        
        bulkApprove.disabled = pendingSuggestions.length === 0;
        bulkReject.disabled = pendingSuggestions.length === 0;
    }
    
    async bulkApproveVisible() {
        const filteredSuggestions = this.getFilteredSuggestions();
        const pendingSuggestions = filteredSuggestions.filter(s => s.status === 'pending');
        
        if (pendingSuggestions.length === 0) return;
        
        const confirmed = confirm(`Are you sure you want to approve ${pendingSuggestions.length} suggestions?`);
        if (!confirmed) return;
        
        for (const suggestion of pendingSuggestions) {
            await this.approveSuggestion(suggestion);
        }
    }
    
    async bulkRejectVisible() {
        const filteredSuggestions = this.getFilteredSuggestions();
        const pendingSuggestions = filteredSuggestions.filter(s => s.status === 'pending');
        
        if (pendingSuggestions.length === 0) return;
        
        const confirmed = confirm(`Are you sure you want to reject ${pendingSuggestions.length} suggestions?`);
        if (!confirmed) return;
        
        for (const suggestion of pendingSuggestions) {
            await this.rejectSuggestion(suggestion);
        }
    }
    
    async refreshSuggestions() {
        // Request fresh suggestions from backend
        if (this.onSuggestionAction) {
            this.onSuggestionAction('refresh_requested');
        }
    }
    
    async requestSuggestions() {
        // Request new suggestions for current document
        if (this.onSuggestionAction) {
            this.onSuggestionAction('suggestions_requested');
        }
    }
    
    clearApproved() {
        const approvedCount = this.suggestions.filter(s => s.status === 'approved').length;
        
        if (approvedCount === 0) {
            alert('No approved suggestions to clear.');
            return;
        }
        
        const confirmed = confirm(`Are you sure you want to clear ${approvedCount} approved suggestions?`);
        if (!confirmed) return;
        
        this.suggestions = this.suggestions.filter(s => s.status !== 'approved');
        this.renderSuggestions();
        this.updateStats();
        this.updateBulkActionButtons();
    }
    
    exportSuggestions() {
        const data = {
            timestamp: new Date().toISOString(),
            totalSuggestions: this.suggestions.length,
            suggestions: this.suggestions
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `writecrew-suggestions-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
    
    // Utility methods
    getAgentName(agentId) {
        const names = {
            'master_router': 'Master Router',
            'content_writer': 'Content Writer',
            'research_agent': 'Research Agent',
            'style_editor': 'Style Editor',
            'grammar_assistant': 'Grammar Assistant',
            'structure_architect': 'Structure Architect',
            'legal_expert': 'Legal Expert',
            'medical_expert': 'Medical Expert',
            'technical_expert': 'Technical Expert',
            'academic_expert': 'Academic Expert'
        };
        return names[agentId] || 'Agent';
    }
    
    getAgentIcon(agentId) {
        const icons = {
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
        return icons[agentId] || '🤖';
    }
    
    getPriorityIcon(priority) {
        const icons = {
            high: '🔴',
            medium: '🟡',
            low: '🟢'
        };
        return icons[priority] || '🟡';
    }
    
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    formatTimestamp(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return time.toLocaleDateString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async highlightSuggestionInDocument(suggestion) {
        if (this.wordService && suggestion.location) {
            await this.wordService.highlightText(suggestion.location, {
                color: this.getSuggestionHighlightColor(suggestion.type),
                id: suggestion.id
            });
        }
    }
    
    async removeHighlightFromDocument(suggestion) {
        if (this.wordService && suggestion.id) {
            await this.wordService.removeHighlight(suggestion.id);
        }
    }
    
    async navigateToSuggestion(suggestion) {
        if (this.wordService && suggestion.location) {
            await this.wordService.navigateToLocation(suggestion.location);
        }
    }
    
    getSuggestionHighlightColor(type) {
        const colors = {
            content: '#E3F2FD',
            grammar: '#FFF3E0',
            style: '#F3E5F5',
            structure: '#E8F5E8',
            research: '#FFF8E1'
        };
        return colors[type] || '#F5F5F5';
    }
    
    loadSuggestions() {
        // Load suggestions from local storage or backend
        try {
            const saved = localStorage.getItem('writecrew_suggestions');
            if (saved) {
                this.suggestions = JSON.parse(saved);
                this.renderSuggestions();
                this.updateStats();
                this.updateBulkActionButtons();
            }
        } catch (error) {
            console.error('Failed to load suggestions:', error);
        }
    }
    
    saveSuggestions() {
        try {
            localStorage.setItem('writecrew_suggestions', JSON.stringify(this.suggestions));
        } catch (error) {
            console.error('Failed to save suggestions:', error);
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
    module.exports = SuggestionsPanel;
} else {
    window.SuggestionsPanel = SuggestionsPanel;
}

