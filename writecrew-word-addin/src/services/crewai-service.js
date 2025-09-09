/*
 * CrewAI Service - Backend Integration
 * Handles communication with CrewAI backend and agent orchestration
 */

/**
 * CrewAI Service Class
 * Manages all communication with the CrewAI backend system
 */
export class CrewAIService {
    constructor(config = {}) {
        this.apiUrl = config.apiUrl || 'http://localhost:8000';
        this.apiKey = config.apiKey || 'dev-key';
        this.timeout = config.timeout || 30000; // 30 seconds
        this.retryAttempts = config.retryAttempts || 3;
        this.retryDelay = config.retryDelay || 1000; // 1 second
        
        // WebSocket connection for real-time updates
        this.websocket = null;
        this.websocketUrl = config.websocketUrl || 'ws://localhost:8000/ws';
        
        // Agent state management
        this.activeAgents = new Map();
        this.pendingSuggestions = new Map();
        
        // Event listeners
        this.eventListeners = new Map();
        
        console.log('CrewAI Service initialized with config:', {
            apiUrl: this.apiUrl,
            websocketUrl: this.websocketUrl
        });
    }

    /**
     * Test connection to CrewAI backend
     */
    async testConnection() {
        try {
            const response = await this.makeRequest('GET', '/health');
            console.log('CrewAI Service: Connection test successful', response);
            return response;
        } catch (error) {
            console.error('CrewAI Service: Connection test failed', error);
            throw new Error(`Failed to connect to CrewAI backend: ${error.message}`);
        }
    }

    /**
     * Initialize WebSocket connection for real-time updates
     */
    async initializeWebSocket() {
        try {
            this.websocket = new WebSocket(this.websocketUrl);
            
            this.websocket.onopen = () => {
                console.log('CrewAI Service: WebSocket connected');
                this.emit('websocket:connected');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('CrewAI Service: Failed to parse WebSocket message', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('CrewAI Service: WebSocket disconnected');
                this.emit('websocket:disconnected');
                // Attempt to reconnect after delay
                setTimeout(() => this.initializeWebSocket(), 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('CrewAI Service: WebSocket error', error);
                this.emit('websocket:error', error);
            };
            
        } catch (error) {
            console.error('CrewAI Service: Failed to initialize WebSocket', error);
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleWebSocketMessage(data) {
        console.log('CrewAI Service: WebSocket message received', data);
        
        switch (data.type) {
            case 'agent_response':
                this.emit('agent:response', data.payload);
                break;
            case 'suggestion_created':
                this.handleSuggestionCreated(data.payload);
                break;
            case 'agent_status_update':
                this.handleAgentStatusUpdate(data.payload);
                break;
            case 'workflow_progress':
                this.emit('workflow:progress', data.payload);
                break;
            default:
                console.log('CrewAI Service: Unknown WebSocket message type', data.type);
        }
    }

    /**
     * Send message to specific agent
     */
    async sendMessage(messageData) {
        try {
            const payload = {
                agent: messageData.agent,
                message: messageData.message,
                permission_level: messageData.permissionLevel,
                word_context: messageData.wordContext,
                session_id: this.getSessionId(),
                timestamp: new Date().toISOString()
            };
            
            console.log('CrewAI Service: Sending message to agent', payload);
            
            const response = await this.makeRequest('POST', '/agents/message', payload);
            
            // Update agent state
            this.updateAgentState(messageData.agent, {
                lastMessage: messageData.message,
                lastResponse: response.message,
                status: 'active'
            });
            
            return {
                message: response.message,
                suggestions: response.suggestions || [],
                wordsGenerated: response.words_generated || 0,
                cost: response.cost || 0,
                confidence: response.confidence || 0.8,
                agent: messageData.agent
            };
            
        } catch (error) {
            console.error('CrewAI Service: Failed to send message', error);
            throw error;
        }
    }

    /**
     * Get available agents from backend
     */
    async getAvailableAgents() {
        try {
            const response = await this.makeRequest('GET', '/agents');
            console.log('CrewAI Service: Available agents retrieved', response);
            return response.agents || [];
        } catch (error) {
            console.error('CrewAI Service: Failed to get available agents', error);
            throw error;
        }
    }

    /**
     * Initialize specific agent
     */
    async initializeAgent(agentType, config = {}) {
        try {
            const payload = {
                agent_type: agentType,
                config: config,
                session_id: this.getSessionId()
            };
            
            const response = await this.makeRequest('POST', '/agents/initialize', payload);
            
            // Store agent state
            this.activeAgents.set(agentType, {
                id: response.agent_id,
                type: agentType,
                status: 'initialized',
                config: config,
                capabilities: response.capabilities || [],
                initialized_at: new Date().toISOString()
            });
            
            console.log(`CrewAI Service: Agent ${agentType} initialized`, response);
            return response;
            
        } catch (error) {
            console.error(`CrewAI Service: Failed to initialize agent ${agentType}`, error);
            throw error;
        }
    }

    /**
     * Execute multi-agent workflow
     */
    async executeWorkflow(workflowData) {
        try {
            const payload = {
                workflow_type: workflowData.type,
                agents: workflowData.agents,
                tasks: workflowData.tasks,
                permission_level: workflowData.permissionLevel,
                word_context: workflowData.wordContext,
                session_id: this.getSessionId()
            };
            
            console.log('CrewAI Service: Executing workflow', payload);
            
            const response = await this.makeRequest('POST', '/workflows/execute', payload);
            
            return {
                workflow_id: response.workflow_id,
                status: response.status,
                estimated_duration: response.estimated_duration,
                tasks: response.tasks || []
            };
            
        } catch (error) {
            console.error('CrewAI Service: Failed to execute workflow', error);
            throw error;
        }
    }

    /**
     * Get workflow status
     */
    async getWorkflowStatus(workflowId) {
        try {
            const response = await this.makeRequest('GET', `/workflows/${workflowId}/status`);
            return response;
        } catch (error) {
            console.error('CrewAI Service: Failed to get workflow status', error);
            throw error;
        }
    }

    /**
     * Approve suggestion
     */
    async approveSuggestion(suggestionId) {
        try {
            const payload = {
                suggestion_id: suggestionId,
                action: 'approve',
                session_id: this.getSessionId()
            };
            
            const response = await this.makeRequest('POST', '/suggestions/approve', payload);
            
            // Remove from pending suggestions
            this.pendingSuggestions.delete(suggestionId);
            
            console.log('CrewAI Service: Suggestion approved', response);
            return response;
            
        } catch (error) {
            console.error('CrewAI Service: Failed to approve suggestion', error);
            throw error;
        }
    }

    /**
     * Reject suggestion
     */
    async rejectSuggestion(suggestionId, reason = '') {
        try {
            const payload = {
                suggestion_id: suggestionId,
                action: 'reject',
                reason: reason,
                session_id: this.getSessionId()
            };
            
            const response = await this.makeRequest('POST', '/suggestions/reject', payload);
            
            // Remove from pending suggestions
            this.pendingSuggestions.delete(suggestionId);
            
            console.log('CrewAI Service: Suggestion rejected', response);
            return response;
            
        } catch (error) {
            console.error('CrewAI Service: Failed to reject suggestion', error);
            throw error;
        }
    }

    /**
     * Modify suggestion
     */
    async modifySuggestion(suggestionId, modifications) {
        try {
            const payload = {
                suggestion_id: suggestionId,
                modifications: modifications,
                session_id: this.getSessionId()
            };
            
            const response = await this.makeRequest('POST', '/suggestions/modify', payload);
            
            console.log('CrewAI Service: Suggestion modified', response);
            return response;
            
        } catch (error) {
            console.error('CrewAI Service: Failed to modify suggestion', error);
            throw error;
        }
    }

    /**
     * Get agent performance metrics
     */
    async getAgentMetrics(agentType, timeframe = '24h') {
        try {
            const response = await this.makeRequest('GET', `/agents/${agentType}/metrics?timeframe=${timeframe}`);
            return response;
        } catch (error) {
            console.error('CrewAI Service: Failed to get agent metrics', error);
            throw error;
        }
    }

    /**
     * Update agent configuration
     */
    async updateAgentConfig(agentType, config) {
        try {
            const payload = {
                agent_type: agentType,
                config: config,
                session_id: this.getSessionId()
            };
            
            const response = await this.makeRequest('PUT', `/agents/${agentType}/config`, payload);
            
            // Update local agent state
            if (this.activeAgents.has(agentType)) {
                const agent = this.activeAgents.get(agentType);
                agent.config = { ...agent.config, ...config };
                this.activeAgents.set(agentType, agent);
            }
            
            console.log(`CrewAI Service: Agent ${agentType} config updated`, response);
            return response;
            
        } catch (error) {
            console.error('CrewAI Service: Failed to update agent config', error);
            throw error;
        }
    }

    /**
     * Handle suggestion created event
     */
    handleSuggestionCreated(suggestion) {
        this.pendingSuggestions.set(suggestion.id, suggestion);
        this.emit('suggestion:created', suggestion);
    }

    /**
     * Handle agent status update
     */
    handleAgentStatusUpdate(update) {
        if (this.activeAgents.has(update.agent_type)) {
            const agent = this.activeAgents.get(update.agent_type);
            agent.status = update.status;
            agent.last_updated = new Date().toISOString();
            this.activeAgents.set(update.agent_type, agent);
        }
        
        this.emit('agent:status_update', update);
    }

    /**
     * Update agent state
     */
    updateAgentState(agentType, updates) {
        if (this.activeAgents.has(agentType)) {
            const agent = this.activeAgents.get(agentType);
            Object.assign(agent, updates);
            agent.last_updated = new Date().toISOString();
            this.activeAgents.set(agentType, agent);
        }
    }

    /**
     * Make HTTP request to CrewAI backend
     */
    async makeRequest(method, endpoint, data = null, attempt = 1) {
        const url = `${this.apiUrl}${endpoint}`;
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`,
                'X-Session-ID': this.getSessionId()
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            console.log(`CrewAI Service: Making ${method} request to ${url}`, data);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            options.signal = controller.signal;
            
            const response = await fetch(url, options);
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`HTTP ${response.status}: ${errorData.message || response.statusText}`);
            }
            
            const responseData = await response.json();
            console.log(`CrewAI Service: ${method} ${url} successful`, responseData);
            
            return responseData;
            
        } catch (error) {
            console.error(`CrewAI Service: ${method} ${url} failed (attempt ${attempt})`, error);
            
            // Retry logic
            if (attempt < this.retryAttempts && !error.name === 'AbortError') {
                console.log(`CrewAI Service: Retrying request in ${this.retryDelay}ms...`);
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                return this.makeRequest(method, endpoint, data, attempt + 1);
            }
            
            throw error;
        }
    }

    /**
     * Get or generate session ID
     */
    getSessionId() {
        if (!this.sessionId) {
            this.sessionId = `writecrew_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }
        return this.sessionId;
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
                    console.error(`CrewAI Service: Error in event listener for ${event}`, error);
                }
            });
        }
    }

    /**
     * Get current agent states
     */
    getActiveAgents() {
        return Array.from(this.activeAgents.values());
    }

    /**
     * Get pending suggestions
     */
    getPendingSuggestions() {
        return Array.from(this.pendingSuggestions.values());
    }

    /**
     * Close WebSocket connection
     */
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }

    /**
     * Cleanup resources
     */
    destroy() {
        this.disconnect();
        this.activeAgents.clear();
        this.pendingSuggestions.clear();
        this.eventListeners.clear();
    }
}

