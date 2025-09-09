/**
 * RealtimeCommunicationService
 * Manages WebSocket connections, message routing, and real-time communication
 * between WriteCrew Word Add-in and backend services
 */

class RealtimeCommunicationService {
    constructor(options = {}) {
        // Configuration
        this.config = {
            baseUrl: options.baseUrl || 'ws://localhost:8000',
            reconnectAttempts: options.reconnectAttempts || 5,
            reconnectDelay: options.reconnectDelay || 1000,
            heartbeatInterval: options.heartbeatInterval || 30000,
            messageTimeout: options.messageTimeout || 10000,
            maxMessageQueue: options.maxMessageQueue || 100,
            ...options
        };
        
        // Connection state
        this.websocket = null;
        this.connectionState = 'disconnected'; // disconnected, connecting, connected, reconnecting
        this.reconnectAttempt = 0;
        this.lastConnectTime = null;
        this.sessionId = null;
        
        // Message handling
        this.messageHandlers = new Map();
        this.pendingMessages = new Map();
        this.messageQueue = [];
        this.messageId = 0;
        
        // Heartbeat
        this.heartbeatInterval = null;
        this.lastHeartbeat = null;
        this.heartbeatTimeout = null;
        
        // Event emitter functionality
        this.eventListeners = new Map();
        
        // Performance metrics
        this.metrics = {
            messagessent: 0,
            messagesReceived: 0,
            reconnections: 0,
            errors: 0,
            averageLatency: 0,
            connectionUptime: 0,
            lastLatencies: []
        };
        
        // Connection quality monitoring
        this.connectionQuality = {
            status: 'unknown', // excellent, good, fair, poor, critical
            latency: 0,
            packetLoss: 0,
            stability: 1.0
        };
        
        this.init();
    }
    
    init() {
        console.log('🔌 Initializing Real-time Communication Service...');
        
        // Generate session ID
        this.sessionId = this.generateSessionId();
        
        // Setup default message handlers
        this.setupDefaultHandlers();
        
        // Start connection quality monitoring
        this.startQualityMonitoring();
        
        console.log('✅ Real-time Communication Service initialized');
    }
    
    // Connection Management
    async connect(userToken = null) {
        if (this.connectionState === 'connected' || this.connectionState === 'connecting') {
            console.log('Already connected or connecting');
            return Promise.resolve();
        }
        
        return new Promise((resolve, reject) => {
            try {
                this.connectionState = 'connecting';
                this.emit('connectionStateChanged', { state: 'connecting' });
                
                // Construct WebSocket URL with authentication
                const wsUrl = this.buildWebSocketUrl(userToken);
                
                console.log(`🔗 Connecting to WebSocket: ${wsUrl}`);
                
                // Create WebSocket connection
                this.websocket = new WebSocket(wsUrl);
                
                // Connection timeout
                const connectionTimeout = setTimeout(() => {
                    if (this.connectionState === 'connecting') {
                        this.websocket.close();
                        reject(new Error('Connection timeout'));
                    }
                }, 10000);
                
                // WebSocket event handlers
                this.websocket.onopen = (event) => {
                    clearTimeout(connectionTimeout);
                    this.handleConnectionOpen(event);
                    resolve();
                };
                
                this.websocket.onmessage = (event) => {
                    this.handleMessage(event);
                };
                
                this.websocket.onclose = (event) => {
                    clearTimeout(connectionTimeout);
                    this.handleConnectionClose(event);
                    
                    if (this.connectionState === 'connecting') {
                        reject(new Error(`Connection failed: ${event.reason}`));
                    }
                };
                
                this.websocket.onerror = (error) => {
                    clearTimeout(connectionTimeout);
                    this.handleConnectionError(error);
                    
                    if (this.connectionState === 'connecting') {
                        reject(error);
                    }
                };
                
            } catch (error) {
                this.connectionState = 'disconnected';
                this.emit('connectionStateChanged', { state: 'disconnected', error });
                reject(error);
            }
        });
    }
    
    disconnect() {
        console.log('🔌 Disconnecting WebSocket...');
        
        // Stop heartbeat
        this.stopHeartbeat();
        
        // Clear reconnection attempts
        this.reconnectAttempt = 0;
        
        // Close WebSocket
        if (this.websocket) {
            this.websocket.close(1000, 'User initiated disconnect');
        }
        
        // Update state
        this.connectionState = 'disconnected';
        this.emit('connectionStateChanged', { state: 'disconnected' });
    }
    
    async reconnect() {
        if (this.connectionState === 'connected' || this.connectionState === 'connecting') {
            return;
        }
        
        if (this.reconnectAttempt >= this.config.reconnectAttempts) {
            console.error('❌ Maximum reconnection attempts reached');
            this.emit('reconnectionFailed', { attempts: this.reconnectAttempt });
            return;
        }
        
        this.reconnectAttempt++;
        this.connectionState = 'reconnecting';
        this.emit('connectionStateChanged', { 
            state: 'reconnecting', 
            attempt: this.reconnectAttempt 
        });
        
        console.log(`🔄 Reconnection attempt ${this.reconnectAttempt}/${this.config.reconnectAttempts}`);
        
        // Exponential backoff
        const delay = this.config.reconnectDelay * Math.pow(2, this.reconnectAttempt - 1);
        
        setTimeout(async () => {
            try {
                await this.connect();
                this.reconnectAttempt = 0;
                this.metrics.reconnections++;
                
                // Resend queued messages
                await this.resendQueuedMessages();
                
            } catch (error) {
                console.error(`Reconnection attempt ${this.reconnectAttempt} failed:`, error);
                this.reconnect(); // Try again
            }
        }, delay);
    }
    
    // Message Handling
    async sendMessage(type, data = {}, options = {}) {
        const message = {
            id: this.generateMessageId(),
            type,
            data,
            timestamp: Date.now(),
            sessionId: this.sessionId
        };
        
        // Add to pending messages if expecting response
        if (options.expectResponse) {
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    this.pendingMessages.delete(message.id);
                    reject(new Error(`Message timeout: ${type}`));
                }, options.timeout || this.config.messageTimeout);
                
                this.pendingMessages.set(message.id, {
                    resolve,
                    reject,
                    timeout,
                    message
                });
                
                this.doSendMessage(message);
            });
        } else {
            this.doSendMessage(message);
            return Promise.resolve();
        }
    }
    
    doSendMessage(message) {
        if (this.connectionState !== 'connected') {
            // Queue message for later
            if (this.messageQueue.length < this.config.maxMessageQueue) {
                this.messageQueue.push(message);
                console.log(`📤 Message queued: ${message.type}`);
            } else {
                console.warn('⚠️ Message queue full, dropping message');
            }
            return;
        }
        
        try {
            const messageString = JSON.stringify(message);
            this.websocket.send(messageString);
            
            this.metrics.messagesSent++;
            console.log(`📤 Message sent: ${message.type}`, message);
            
            this.emit('messageSent', { message });
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.metrics.errors++;
            this.emit('messageError', { message, error });
        }
    }
    
    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            
            this.metrics.messagesReceived++;
            console.log(`📥 Message received: ${message.type}`, message);
            
            // Calculate latency if this is a response
            if (message.responseToId && this.pendingMessages.has(message.responseToId)) {
                const pendingMessage = this.pendingMessages.get(message.responseToId);
                const latency = Date.now() - pendingMessage.message.timestamp;
                this.updateLatencyMetrics(latency);
            }
            
            // Handle response messages
            if (message.responseToId && this.pendingMessages.has(message.responseToId)) {
                const pending = this.pendingMessages.get(message.responseToId);
                clearTimeout(pending.timeout);
                this.pendingMessages.delete(message.responseToId);
                
                if (message.error) {
                    pending.reject(new Error(message.error));
                } else {
                    pending.resolve(message.data);
                }
                return;
            }
            
            // Handle heartbeat responses
            if (message.type === 'heartbeat_response') {
                this.handleHeartbeatResponse(message);
                return;
            }
            
            // Route to registered handlers
            const handlers = this.messageHandlers.get(message.type) || [];
            handlers.forEach(handler => {
                try {
                    handler(message.data, message);
                } catch (error) {
                    console.error(`Error in message handler for ${message.type}:`, error);
                }
            });
            
            // Emit generic message event
            this.emit('messageReceived', { message });
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
            this.metrics.errors++;
        }
    }
    
    // Event Handlers
    handleConnectionOpen(event) {
        console.log('✅ WebSocket connection established');
        
        this.connectionState = 'connected';
        this.lastConnectTime = Date.now();
        this.reconnectAttempt = 0;
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Send authentication if needed
        this.sendAuthenticationMessage();
        
        // Process queued messages
        this.processMessageQueue();
        
        this.emit('connectionStateChanged', { state: 'connected' });
        this.emit('connected', { event });
    }
    
    handleConnectionClose(event) {
        console.log('🔌 WebSocket connection closed', event);
        
        this.stopHeartbeat();
        
        const wasConnected = this.connectionState === 'connected';
        this.connectionState = 'disconnected';
        
        this.emit('connectionStateChanged', { 
            state: 'disconnected', 
            code: event.code, 
            reason: event.reason 
        });
        
        // Auto-reconnect if connection was established and not closed intentionally
        if (wasConnected && event.code !== 1000) {
            console.log('🔄 Connection lost, attempting to reconnect...');
            setTimeout(() => {
                this.reconnect();
            }, 1000);
        }
    }
    
    handleConnectionError(error) {
        console.error('❌ WebSocket error:', error);
        
        this.metrics.errors++;
        this.emit('connectionError', { error });
    }
    
    // Heartbeat Management
    startHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        this.heartbeatInterval = setInterval(() => {
            this.sendHeartbeat();
        }, this.config.heartbeatInterval);
        
        console.log('💓 Heartbeat started');
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
        
        console.log('💓 Heartbeat stopped');
    }
    
    sendHeartbeat() {
        if (this.connectionState !== 'connected') {
            return;
        }
        
        const heartbeatMessage = {
            id: this.generateMessageId(),
            type: 'heartbeat',
            timestamp: Date.now(),
            sessionId: this.sessionId
        };
        
        this.doSendMessage(heartbeatMessage);
        this.lastHeartbeat = Date.now();
        
        // Set timeout for heartbeat response
        this.heartbeatTimeout = setTimeout(() => {
            console.warn('⚠️ Heartbeat timeout - connection may be lost');
            this.connectionQuality.status = 'poor';
            this.emit('connectionQualityChanged', this.connectionQuality);
        }, 5000);
    }
    
    handleHeartbeatResponse(message) {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
        
        const latency = Date.now() - this.lastHeartbeat;
        this.updateLatencyMetrics(latency);
        this.updateConnectionQuality(latency);
        
        console.log(`💓 Heartbeat response received (${latency}ms)`);
    }
    
    // Message Queue Management
    processMessageQueue() {
        console.log(`📤 Processing ${this.messageQueue.length} queued messages`);
        
        const messages = [...this.messageQueue];
        this.messageQueue = [];
        
        messages.forEach(message => {
            this.doSendMessage(message);
        });
    }
    
    async resendQueuedMessages() {
        if (this.messageQueue.length === 0) {
            return;
        }
        
        console.log(`🔄 Resending ${this.messageQueue.length} queued messages`);
        
        // Add delay between messages to avoid overwhelming
        for (const message of this.messageQueue) {
            this.doSendMessage(message);
            await this.delay(100);
        }
        
        this.messageQueue = [];
    }
    
    // Connection Quality Monitoring
    startQualityMonitoring() {
        setInterval(() => {
            this.assessConnectionQuality();
        }, 10000); // Every 10 seconds
    }
    
    updateLatencyMetrics(latency) {
        this.metrics.lastLatencies.push(latency);
        
        // Keep only last 10 latencies
        if (this.metrics.lastLatencies.length > 10) {
            this.metrics.lastLatencies.shift();
        }
        
        // Calculate average latency
        this.metrics.averageLatency = this.metrics.lastLatencies.reduce((a, b) => a + b, 0) / 
                                     this.metrics.lastLatencies.length;
        
        this.connectionQuality.latency = latency;
    }
    
    updateConnectionQuality(latency) {
        // Assess connection quality based on latency
        if (latency < 100) {
            this.connectionQuality.status = 'excellent';
        } else if (latency < 300) {
            this.connectionQuality.status = 'good';
        } else if (latency < 1000) {
            this.connectionQuality.status = 'fair';
        } else if (latency < 3000) {
            this.connectionQuality.status = 'poor';
        } else {
            this.connectionQuality.status = 'critical';
        }
        
        this.emit('connectionQualityChanged', this.connectionQuality);
    }
    
    assessConnectionQuality() {
        if (this.connectionState !== 'connected') {
            this.connectionQuality.status = 'disconnected';
            return;
        }
        
        // Calculate uptime
        if (this.lastConnectTime) {
            this.metrics.connectionUptime = Date.now() - this.lastConnectTime;
        }
        
        // Calculate stability (successful messages / total attempts)
        const totalMessages = this.metrics.messagesSent + this.metrics.errors;
        if (totalMessages > 0) {
            this.connectionQuality.stability = this.metrics.messagesSent / totalMessages;
        }
        
        // Emit quality update
        this.emit('connectionQualityChanged', this.connectionQuality);
    }
    
    // Message Handler Registration
    onMessage(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        
        this.messageHandlers.get(type).push(handler);
        
        // Return unsubscribe function
        return () => {
            const handlers = this.messageHandlers.get(type);
            if (handlers) {
                const index = handlers.indexOf(handler);
                if (index > -1) {
                    handlers.splice(index, 1);
                }
            }
        };
    }
    
    offMessage(type, handler) {
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    // Event Emitter Methods
    on(event, listener) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        
        this.eventListeners.get(event).push(listener);
        
        // Return unsubscribe function
        return () => {
            this.off(event, listener);
        };
    }
    
    off(event, listener) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(listener);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        const listeners = this.eventListeners.get(event) || [];
        listeners.forEach(listener => {
            try {
                listener(data);
            } catch (error) {
                console.error(`Error in event listener for ${event}:`, error);
            }
        });
    }
    
    // High-level API Methods
    async requestAgentAction(agentId, action, data = {}) {
        return this.sendMessage('agent_action', {
            agentId,
            action,
            data
        }, { expectResponse: true });
    }
    
    async sendChatMessage(agentId, message, context = {}) {
        return this.sendMessage('chat_message', {
            agentId,
            message,
            context
        }, { expectResponse: true });
    }
    
    async requestSuggestions(documentContext) {
        return this.sendMessage('request_suggestions', {
            context: documentContext
        }, { expectResponse: true });
    }
    
    async updateDocumentContent(content, changes = []) {
        return this.sendMessage('document_update', {
            content,
            changes,
            timestamp: Date.now()
        });
    }
    
    async reportUserAction(action, data = {}) {
        return this.sendMessage('user_action', {
            action,
            data,
            timestamp: Date.now()
        });
    }
    
    // Setup Methods
    setupDefaultHandlers() {
        // Agent status updates
        this.onMessage('agent_status', (data) => {
            this.emit('agentStatusChanged', data);
        });
        
        // New suggestions
        this.onMessage('suggestion', (data) => {
            this.emit('suggestionReceived', data);
        });
        
        // Task completion
        this.onMessage('task_complete', (data) => {
            this.emit('taskCompleted', data);
        });
        
        // Error messages
        this.onMessage('error', (data) => {
            this.emit('errorReceived', data);
        });
        
        // System notifications
        this.onMessage('notification', (data) => {
            this.emit('notificationReceived', data);
        });
        
        // Agent responses
        this.onMessage('agent_response', (data) => {
            this.emit('agentResponse', data);
        });
    }
    
    sendAuthenticationMessage() {
        // Send authentication token if available
        const token = localStorage.getItem('writecrew_auth_token');
        if (token) {
            this.sendMessage('authenticate', { token });
        }
    }
    
    // Utility Methods
    buildWebSocketUrl(userToken) {
        let url = this.config.baseUrl.replace('http', 'ws');
        
        if (!url.endsWith('/')) {
            url += '/';
        }
        
        url += 'ws';
        
        // Add session ID and token as query parameters
        const params = new URLSearchParams();
        params.append('sessionId', this.sessionId);
        
        if (userToken) {
            params.append('token', userToken);
        }
        
        return `${url}?${params.toString()}`;
    }
    
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    generateMessageId() {
        return ++this.messageId;
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Status and Metrics
    getConnectionStatus() {
        return {
            state: this.connectionState,
            quality: this.connectionQuality,
            metrics: this.metrics,
            sessionId: this.sessionId,
            uptime: this.lastConnectTime ? Date.now() - this.lastConnectTime : 0
        };
    }
    
    getMetrics() {
        return {
            ...this.metrics,
            connectionQuality: this.connectionQuality,
            queuedMessages: this.messageQueue.length,
            pendingMessages: this.pendingMessages.size
        };
    }
    
    // Cleanup
    destroy() {
        console.log('🧹 Destroying Real-time Communication Service...');
        
        // Disconnect WebSocket
        this.disconnect();
        
        // Clear all intervals and timeouts
        this.stopHeartbeat();
        
        // Clear pending messages
        this.pendingMessages.forEach(pending => {
            clearTimeout(pending.timeout);
            pending.reject(new Error('Service destroyed'));
        });
        this.pendingMessages.clear();
        
        // Clear message queue
        this.messageQueue = [];
        
        // Clear event listeners
        this.eventListeners.clear();
        this.messageHandlers.clear();
        
        console.log('✅ Real-time Communication Service destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealtimeCommunicationService;
} else {
    window.RealtimeCommunicationService = RealtimeCommunicationService;
}

