/*
 * WriteCrew Task Pane - Main JavaScript
 * Microsoft Office.js integration with CrewAI backend
 */

// Import CSS
import './taskpane.css';

// Import services
import { CrewAIService } from '../services/crewai-service.js';
import { WordIntegrationService } from '../services/word-integration.js';
import { PermissionManager } from '../services/permission-manager.js';

/**
 * WriteCrew Task Pane Main Class
 * Handles Office.js initialization and UI management
 */
class WriteCrewTaskPane {
    constructor() {
        this.crewAIService = null;
        this.wordService = null;
        this.permissionManager = null;
        this.currentAgent = 'content_writer';
        this.permissionLevel = 1; // Start with Assistant level
        this.isInitialized = false;
        this.sessionStartTime = Date.now();
        this.wordsGenerated = 0;
        this.costEstimate = 0.00;
        
        // UI Elements
        this.elements = {};
        
        // Bind methods
        this.handleSendMessage = this.handleSendMessage.bind(this);
        this.handleAgentChange = this.handleAgentChange.bind(this);
        this.handlePermissionChange = this.handlePermissionChange.bind(this);
        this.updateSessionStats = this.updateSessionStats.bind(this);
    }

    /**
     * Initialize WriteCrew when Office.js is ready
     */
    async initialize() {
        try {
            console.log('WriteCrew: Starting initialization...');
            this.showLoadingOverlay('Initializing WriteCrew...');
            
            // Wait for Office.js to be ready
            await this.initializeOfficeJS();
            
            // Initialize services
            await this.initializeServices();
            
            // Setup UI
            this.initializeUI();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Start session timer
            this.startSessionTimer();
            
            this.isInitialized = true;
            this.hideLoadingOverlay();
            this.updateConnectionStatus('connected', 'Connected');
            
            console.log('WriteCrew: Initialization complete');
            
        } catch (error) {
            console.error('WriteCrew: Initialization failed:', error);
            this.showError('Failed to initialize WriteCrew. Please refresh and try again.');
            this.hideLoadingOverlay();
        }
    }

    /**
     * Initialize Office.js and verify Word integration
     */
    async initializeOfficeJS() {
        return new Promise((resolve, reject) => {
            Office.onReady((info) => {
                console.log('Office.js ready:', info);
                
                if (info.host === Office.HostType.Word) {
                    console.log('WriteCrew: Word host detected');
                    resolve();
                } else {
                    reject(new Error('WriteCrew requires Microsoft Word'));
                }
            });
        });
    }

    /**
     * Initialize all services
     */
    async initializeServices() {
        try {
            // Initialize CrewAI service
            this.crewAIService = new CrewAIService({
                apiUrl: process.env.CREWAI_API_URL || 'http://localhost:8000',
                apiKey: process.env.CREWAI_API_KEY || 'dev-key'
            });
            
            // Initialize Word integration service
            this.wordService = new WordIntegrationService();
            
            // Initialize permission manager
            this.permissionManager = new PermissionManager(this.wordService);
            
            // Test connections
            await this.crewAIService.testConnection();
            await this.wordService.testWordConnection();
            
            console.log('WriteCrew: All services initialized successfully');
            
        } catch (error) {
            console.error('WriteCrew: Service initialization failed:', error);
            throw error;
        }
    }

    /**
     * Initialize UI elements and cache references
     */
    initializeUI() {
        // Cache DOM elements
        this.elements = {
            // Chat elements
            chatMessages: document.getElementById('chat-messages'),
            chatInput: document.getElementById('chat-input'),
            sendButton: document.getElementById('send-message'),
            agentSelector: document.getElementById('active-agent'),
            
            // Permission elements
            permissionLevels: document.querySelectorAll('.permission-level'),
            
            // Status elements
            connectionStatus: document.getElementById('connection-status'),
            statusText: document.getElementById('status-text'),
            wordsGenerated: document.getElementById('words-generated'),
            costEstimate: document.getElementById('cost-estimate'),
            sessionTime: document.getElementById('session-time'),
            
            // Pane elements
            chatPane: document.getElementById('chat-pane'),
            suggestionsPane: document.getElementById('suggestions-pane'),
            
            // Agent cards
            agentCards: document.getElementById('agent-cards'),
            suggestionsFeed: document.getElementById('suggestions-feed'),
            approvalQueue: document.getElementById('approval-items'),
            
            // Modals
            loadingOverlay: document.getElementById('loading-overlay'),
            errorModal: document.getElementById('error-modal'),
            errorMessage: document.getElementById('error-message'),
            errorClose: document.getElementById('error-close')
        };

        // Initialize agent cards
        this.updateAgentCards();
        
        // Set initial permission level
        this.updatePermissionLevel(1);
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Chat functionality
        this.elements.sendButton.addEventListener('click', this.handleSendMessage);
        this.elements.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // Agent selection
        this.elements.agentSelector.addEventListener('change', this.handleAgentChange);
        
        // Permission level changes
        this.elements.permissionLevels.forEach(button => {
            button.addEventListener('click', (e) => {
                const level = parseInt(e.currentTarget.dataset.level);
                this.handlePermissionChange(level);
            });
        });
        
        // Error modal
        this.elements.errorClose.addEventListener('click', () => {
            this.hideError();
        });
        
        // Resize functionality (basic implementation)
        this.setupResizeHandles();
    }

    /**
     * Setup resize handles for panes
     */
    setupResizeHandles() {
        const leftHandle = document.getElementById('resize-handle-left');
        let isResizing = false;
        
        leftHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.addEventListener('mousemove', handleResize);
            document.addEventListener('mouseup', stopResize);
        });
        
        const handleResize = (e) => {
            if (!isResizing) return;
            
            const container = document.getElementById('writecrew-main');
            const rect = container.getBoundingClientRect();
            const newWidth = e.clientX - rect.left;
            
            if (newWidth >= 250 && newWidth <= 500) {
                this.elements.chatPane.style.width = `${newWidth}px`;
            }
        };
        
        const stopResize = () => {
            isResizing = false;
            document.removeEventListener('mousemove', handleResize);
            document.removeEventListener('mouseup', stopResize);
        };
    }

    /**
     * Handle sending chat messages
     */
    async handleSendMessage() {
        const message = this.elements.chatInput.value.trim();
        if (!message) return;
        
        try {
            // Clear input
            this.elements.chatInput.value = '';
            
            // Add user message to chat
            this.addChatMessage('user', message);
            
            // Show typing indicator
            const typingId = this.showTypingIndicator();
            
            // Send to CrewAI
            const response = await this.crewAIService.sendMessage({
                agent: this.currentAgent,
                message: message,
                permissionLevel: this.permissionLevel,
                wordContext: await this.wordService.getDocumentContext()
            });
            
            // Remove typing indicator
            this.hideTypingIndicator(typingId);
            
            // Add agent response
            this.addChatMessage('agent', response.message, this.currentAgent);
            
            // Handle any suggestions
            if (response.suggestions && response.suggestions.length > 0) {
                this.handleAgentSuggestions(response.suggestions);
            }
            
            // Update stats
            this.updateWordCount(response.wordsGenerated || 0);
            this.updateCostEstimate(response.cost || 0);
            
        } catch (error) {
            console.error('WriteCrew: Failed to send message:', error);
            this.hideTypingIndicator();
            this.showError('Failed to send message. Please try again.');
        }
    }

    /**
     * Handle agent selection changes
     */
    handleAgentChange(event) {
        const newAgent = event.target.value;
        console.log(`WriteCrew: Switching to agent: ${newAgent}`);
        
        this.currentAgent = newAgent;
        this.updateAgentCards();
        
        // Add system message
        this.addChatMessage('system', `Switched to ${this.getAgentDisplayName(newAgent)}`);
    }

    /**
     * Handle permission level changes
     */
    async handlePermissionChange(level) {
        try {
            console.log(`WriteCrew: Changing permission level to: ${level}`);
            
            // Update permission manager
            await this.permissionManager.setPermissionLevel(level);
            
            // Update UI
            this.updatePermissionLevel(level);
            
            // Store current level
            this.permissionLevel = level;
            
            // Add system message
            const levelNames = {
                1: 'Assistant (High Control)',
                2: 'Collaborative (Medium Control)',
                3: 'Semi-Autonomous (Low Control)',
                4: 'Fully Autonomous (Minimal Control)'
            };
            
            this.addChatMessage('system', `Permission level changed to: ${levelNames[level]}`);
            
        } catch (error) {
            console.error('WriteCrew: Failed to change permission level:', error);
            this.showError('Failed to change permission level. Please try again.');
        }
    }

    /**
     * Add message to chat display
     */
    addChatMessage(type, message, agent = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        
        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${type}`;
        
        if (type === 'agent' && agent) {
            const agentName = document.createElement('div');
            agentName.className = 'agent-name';
            agentName.textContent = this.getAgentDisplayName(agent);
            bubble.appendChild(agentName);
        }
        
        const content = document.createElement('div');
        content.textContent = message;
        bubble.appendChild(content);
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(bubble);
        messageDiv.appendChild(timestamp);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message agent typing-indicator';
        typingDiv.id = `typing-${Date.now()}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble agent';
        bubble.innerHTML = '<div class="typing-dots">●●●</div>';
        
        typingDiv.appendChild(bubble);
        this.elements.chatMessages.appendChild(typingDiv);
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        
        return typingDiv.id;
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator(typingId = null) {
        if (typingId) {
            const typingElement = document.getElementById(typingId);
            if (typingElement) {
                typingElement.remove();
            }
        } else {
            // Remove all typing indicators
            const typingElements = this.elements.chatMessages.querySelectorAll('.typing-indicator');
            typingElements.forEach(el => el.remove());
        }
    }

    /**
     * Handle agent suggestions
     */
    handleAgentSuggestions(suggestions) {
        suggestions.forEach(suggestion => {
            this.addSuggestionToFeed(suggestion);
            
            // If permission level requires approval, add to approval queue
            if (this.permissionManager.requiresApproval(suggestion, this.permissionLevel)) {
                this.addToApprovalQueue(suggestion);
            }
        });
    }

    /**
     * Add suggestion to suggestions feed
     */
    addSuggestionToFeed(suggestion) {
        // Remove "no suggestions" message if it exists
        const noSuggestions = this.elements.suggestionsFeed.querySelector('.no-suggestions');
        if (noSuggestions) {
            noSuggestions.remove();
        }
        
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = 'suggestion-item';
        suggestionDiv.innerHTML = `
            <div class="suggestion-header">
                <span class="suggestion-agent">${this.getAgentDisplayName(suggestion.agent)}</span>
                <span class="suggestion-type">${suggestion.type}</span>
            </div>
            <div class="suggestion-content">${suggestion.content}</div>
            <div class="suggestion-actions">
                <button class="approve" onclick="writeCrew.approveSuggestion('${suggestion.id}')">Approve</button>
                <button class="reject" onclick="writeCrew.rejectSuggestion('${suggestion.id}')">Reject</button>
                <button class="modify" onclick="writeCrew.modifySuggestion('${suggestion.id}')">Modify</button>
            </div>
        `;
        
        this.elements.suggestionsFeed.appendChild(suggestionDiv);
    }

    /**
     * Add suggestion to approval queue
     */
    addToApprovalQueue(suggestion) {
        const approvalDiv = document.createElement('div');
        approvalDiv.className = 'approval-item';
        approvalDiv.innerHTML = `
            <div class="approval-text">${suggestion.content.substring(0, 50)}...</div>
            <div class="approval-actions">
                <button onclick="writeCrew.approveFromQueue('${suggestion.id}')">✓</button>
                <button onclick="writeCrew.rejectFromQueue('${suggestion.id}')">✗</button>
            </div>
        `;
        
        this.elements.approvalQueue.appendChild(approvalDiv);
    }

    /**
     * Update agent cards display
     */
    updateAgentCards() {
        const agents = [
            { id: 'content_writer', name: 'Content Writer', status: 'ready' },
            { id: 'research_assistant', name: 'Research Assistant', status: 'ready' },
            { id: 'editor', name: 'Editor', status: 'ready' },
            { id: 'quality_checker', name: 'Quality Checker', status: 'ready' }
        ];
        
        this.elements.agentCards.innerHTML = '';
        
        agents.forEach(agent => {
            const cardDiv = document.createElement('div');
            cardDiv.className = `agent-card ${agent.id === this.currentAgent ? 'active' : ''}`;
            cardDiv.innerHTML = `
                <span class="agent-name">${agent.name}</span>
                <span class="agent-status">${agent.status}</span>
            `;
            
            this.elements.agentCards.appendChild(cardDiv);
        });
    }

    /**
     * Update permission level UI
     */
    updatePermissionLevel(level) {
        this.elements.permissionLevels.forEach(button => {
            const buttonLevel = parseInt(button.dataset.level);
            button.classList.toggle('active', buttonLevel === level);
        });
    }

    /**
     * Update connection status
     */
    updateConnectionStatus(status, text) {
        this.elements.connectionStatus.className = `status-indicator ${status}`;
        this.elements.statusText.textContent = text;
    }

    /**
     * Update word count
     */
    updateWordCount(words) {
        this.wordsGenerated += words;
        this.elements.wordsGenerated.textContent = `Words: ${this.wordsGenerated}`;
    }

    /**
     * Update cost estimate
     */
    updateCostEstimate(cost) {
        this.costEstimate += cost;
        this.elements.costEstimate.textContent = `Cost: $${this.costEstimate.toFixed(2)}`;
    }

    /**
     * Start session timer
     */
    startSessionTimer() {
        setInterval(() => {
            const elapsed = Date.now() - this.sessionStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            this.elements.sessionTime.textContent = `Time: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    /**
     * Get display name for agent
     */
    getAgentDisplayName(agentId) {
        const names = {
            'content_writer': 'Content Writer',
            'research_assistant': 'Research Assistant',
            'editor': 'Editor',
            'quality_checker': 'Quality Checker'
        };
        return names[agentId] || agentId;
    }

    /**
     * Show loading overlay
     */
    showLoadingOverlay(message = 'Loading...') {
        this.elements.loadingOverlay.querySelector('p').textContent = message;
        this.elements.loadingOverlay.style.display = 'flex';
    }

    /**
     * Hide loading overlay
     */
    hideLoadingOverlay() {
        this.elements.loadingOverlay.style.display = 'none';
    }

    /**
     * Show error modal
     */
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorModal.style.display = 'flex';
    }

    /**
     * Hide error modal
     */
    hideError() {
        this.elements.errorModal.style.display = 'none';
    }

    // Public methods for suggestion handling (called from HTML onclick)
    async approveSuggestion(suggestionId) {
        try {
            await this.crewAIService.approveSuggestion(suggestionId);
            // Remove from UI
            const suggestionElement = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
            if (suggestionElement) {
                suggestionElement.remove();
            }
        } catch (error) {
            console.error('Failed to approve suggestion:', error);
            this.showError('Failed to approve suggestion');
        }
    }

    async rejectSuggestion(suggestionId) {
        try {
            await this.crewAIService.rejectSuggestion(suggestionId);
            // Remove from UI
            const suggestionElement = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
            if (suggestionElement) {
                suggestionElement.remove();
            }
        } catch (error) {
            console.error('Failed to reject suggestion:', error);
            this.showError('Failed to reject suggestion');
        }
    }

    async modifySuggestion(suggestionId) {
        // This would open a modal for modification
        console.log('Modify suggestion:', suggestionId);
        // TODO: Implement modification UI
    }

    async approveFromQueue(suggestionId) {
        await this.approveSuggestion(suggestionId);
        // Also remove from approval queue
        const queueElement = document.querySelector(`[data-approval-id="${suggestionId}"]`);
        if (queueElement) {
            queueElement.remove();
        }
    }

    async rejectFromQueue(suggestionId) {
        await this.rejectSuggestion(suggestionId);
        // Also remove from approval queue
        const queueElement = document.querySelector(`[data-approval-id="${suggestionId}"]`);
        if (queueElement) {
            queueElement.remove();
        }
    }
}

// Initialize WriteCrew when DOM is loaded
let writeCrew;

document.addEventListener('DOMContentLoaded', () => {
    writeCrew = new WriteCrewTaskPane();
    writeCrew.initialize();
});

// Make writeCrew available globally for HTML onclick handlers
window.writeCrew = writeCrew;

// Export for module usage
export default WriteCrewTaskPane;

