/**
 * MainController
 * Central orchestration controller for WriteCrew Word Add-in
 * Manages all UI components, backend communication, and application lifecycle
 */

class MainController {
    constructor() {
        // Core services
        this.crewAIService = null;
        this.wordService = null;
        this.permissionManager = null;
        
        // UI components
        this.chatInterface = null;
        this.suggestionsPanel = null;
        this.agentCards = new Map();
        
        // Application state
        this.isInitialized = false;
        this.isConnected = false;
        this.activeAgents = new Map();
        this.currentDocument = null;
        this.userSession = null;
        this.settings = {
            autoSave: true,
            realTimeSync: true,
            notificationsEnabled: true,
            theme: 'office-default'
        };
        
        // Event handlers
        this.eventHandlers = new Map();
        this.webSocket = null;
        this.heartbeatInterval = null;
        
        // Performance monitoring
        this.performanceMetrics = {
            startTime: Date.now(),
            agentResponseTimes: [],
            errorCount: 0,
            successfulOperations: 0
        };
        
        this.init();
    }
    
    async init() {
        try {
            console.log('🚀 Initializing WriteCrew Main Controller...');
            
            // Wait for Office to be ready
            await this.waitForOfficeReady();
            
            // Initialize core services
            await this.initializeServices();
            
            // Setup UI components
            await this.initializeUI();
            
            // Establish backend connection
            await this.connectToBackend();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load user session and preferences
            await this.loadUserSession();
            
            // Initialize agents
            await this.initializeAgents();
            
            // Setup real-time communication
            this.setupWebSocket();
            
            // Start monitoring
            this.startPerformanceMonitoring();
            
            this.isInitialized = true;
            console.log('✅ WriteCrew Main Controller initialized successfully');
            
            // Show welcome message
            this.showWelcomeMessage();
            
        } catch (error) {
            console.error('❌ Failed to initialize WriteCrew:', error);
            this.handleInitializationError(error);
        }
    }
    
    async waitForOfficeReady() {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Office.js initialization timeout'));
            }, 30000);
            
            Office.onReady((info) => {
                clearTimeout(timeout);
                
                if (info.host === Office.HostType.Word) {
                    console.log('📝 Microsoft Word detected and ready');
                    resolve(info);
                } else {
                    reject(new Error('WriteCrew requires Microsoft Word'));
                }
            });
        });
    }
    
    async initializeServices() {
        console.log('🔧 Initializing core services...');
        
        // Initialize CrewAI service
        this.crewAIService = new CrewAIService({
            baseUrl: this.getBackendUrl(),
            apiKey: await this.getApiKey(),
            timeout: 30000,
            retryAttempts: 3
        });
        
        // Initialize Word integration service
        this.wordService = new WordIntegrationService();
        await this.wordService.initialize();
        
        // Initialize permission manager
        this.permissionManager = new PermissionManager(this.wordService);
        await this.permissionManager.initialize();
        
        console.log('✅ Core services initialized');
    }
    
    async initializeUI() {
        console.log('🎨 Initializing UI components...');
        
        // Get main container
        const container = document.getElementById('writecrew-container');
        if (!container) {
            throw new Error('WriteCrew container not found');
        }
        
        // Create main layout
        this.createMainLayout(container);
        
        // Initialize chat interface
        this.chatInterface = new ChatInterface(
            this.crewAIService,
            this.handleChatAction.bind(this)
        );
        
        // Initialize suggestions panel
        this.suggestionsPanel = new SuggestionsPanel(
            this.wordService,
            this.permissionManager,
            this.handleSuggestionAction.bind(this)
        );
        
        // Mount components
        this.mountComponents();
        
        // Setup pane resizing
        this.setupPaneResizing();
        
        console.log('✅ UI components initialized');
    }
    
    createMainLayout(container) {
        container.innerHTML = `
            <div class="writecrew-main-layout">
                <!-- Header -->
                <div class="writecrew-header">
                    <div class="header-brand">
                        <img src="assets/writecrew-logo.png" alt="WriteCrew" class="brand-logo">
                        <h1 class="brand-title">WriteCrew</h1>
                    </div>
                    <div class="header-controls">
                        <div class="connection-status" id="connection-status">
                            <span class="status-indicator"></span>
                            <span class="status-text">Connecting...</span>
                        </div>
                        <button class="settings-btn" id="settings-btn" title="Settings">
                            ⚙️
                        </button>
                        <button class="help-btn" id="help-btn" title="Help">
                            ❓
                        </button>
                    </div>
                </div>
                
                <!-- Main Content Area -->
                <div class="writecrew-content">
                    <!-- Left Pane: Chat Interface -->
                    <div class="left-pane" id="left-pane">
                        <div class="pane-header">
                            <h3>Agent Chat</h3>
                            <button class="pane-toggle" data-pane="left" title="Toggle chat pane">
                                ◀
                            </button>
                        </div>
                        <div class="pane-content" id="chat-container">
                            <!-- Chat interface will be mounted here -->
                        </div>
                    </div>
                    
                    <!-- Resize Handle -->
                    <div class="resize-handle left-resize" id="left-resize-handle">
                        <div class="resize-grip"></div>
                    </div>
                    
                    <!-- Center Pane: Document Area (Word handles this) -->
                    <div class="center-pane" id="center-pane">
                        <div class="document-overlay" id="document-overlay">
                            <!-- Document interaction overlays -->
                        </div>
                    </div>
                    
                    <!-- Resize Handle -->
                    <div class="resize-handle right-resize" id="right-resize-handle">
                        <div class="resize-grip"></div>
                    </div>
                    
                    <!-- Right Pane: Suggestions Panel -->
                    <div class="right-pane" id="right-pane">
                        <div class="pane-header">
                            <h3>Agent Suggestions</h3>
                            <button class="pane-toggle" data-pane="right" title="Toggle suggestions pane">
                                ▶
                            </button>
                        </div>
                        <div class="pane-content" id="suggestions-container">
                            <!-- Suggestions panel will be mounted here -->
                        </div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="writecrew-footer">
                    <div class="footer-stats">
                        <span class="stat" id="words-generated">
                            <span class="stat-value">0</span>
                            <span class="stat-label">Words Generated</span>
                        </span>
                        <span class="stat" id="suggestions-count">
                            <span class="stat-value">0</span>
                            <span class="stat-label">Suggestions</span>
                        </span>
                        <span class="stat" id="cost-tracker">
                            <span class="stat-value">$0.00</span>
                            <span class="stat-label">Session Cost</span>
                        </span>
                    </div>
                    <div class="footer-actions">
                        <button class="footer-btn" id="export-session" title="Export session">
                            📤 Export
                        </button>
                        <button class="footer-btn" id="clear-session" title="Clear session">
                            🗑️ Clear
                        </button>
                    </div>
                </div>
                
                <!-- Agent Cards Container -->
                <div class="agent-cards-container" id="agent-cards-container">
                    <!-- Agent cards will be dynamically added here -->
                </div>
                
                <!-- Modals and Overlays -->
                <div class="modal-overlay" id="modal-overlay" style="display: none;">
                    <div class="modal-content" id="modal-content">
                        <!-- Dynamic modal content -->
                    </div>
                </div>
                
                <!-- Notification Container -->
                <div class="notification-container" id="notification-container">
                    <!-- Notifications will appear here -->
                </div>
                
                <!-- Loading Overlay -->
                <div class="loading-overlay" id="loading-overlay" style="display: none;">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <p class="loading-text">Initializing WriteCrew...</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    mountComponents() {
        // Mount chat interface
        const chatContainer = document.getElementById('chat-container');
        if (this.chatInterface && chatContainer) {
            chatContainer.appendChild(this.chatInterface.element);
        }
        
        // Mount suggestions panel
        const suggestionsContainer = document.getElementById('suggestions-container');
        if (this.suggestionsPanel && suggestionsContainer) {
            suggestionsContainer.appendChild(this.suggestionsPanel.element);
        }
    }
    
    setupPaneResizing() {
        const leftHandle = document.getElementById('left-resize-handle');
        const rightHandle = document.getElementById('right-resize-handle');
        const leftPane = document.getElementById('left-pane');
        const rightPane = document.getElementById('right-pane');
        const centerPane = document.getElementById('center-pane');
        
        let isResizing = false;
        let currentHandle = null;
        
        const startResize = (handle, e) => {
            isResizing = true;
            currentHandle = handle;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            
            e.preventDefault();
        };
        
        const doResize = (e) => {
            if (!isResizing || !currentHandle) return;
            
            const containerRect = document.querySelector('.writecrew-content').getBoundingClientRect();
            const mouseX = e.clientX - containerRect.left;
            const containerWidth = containerRect.width;
            
            if (currentHandle === leftHandle) {
                // Resize left pane
                const newWidth = Math.max(200, Math.min(mouseX, containerWidth * 0.4));
                const percentage = (newWidth / containerWidth) * 100;
                
                leftPane.style.width = `${percentage}%`;
                this.updateCenterPaneWidth();
                
            } else if (currentHandle === rightHandle) {
                // Resize right pane
                const rightWidth = containerWidth - mouseX;
                const newWidth = Math.max(200, Math.min(rightWidth, containerWidth * 0.4));
                const percentage = (newWidth / containerWidth) * 100;
                
                rightPane.style.width = `${percentage}%`;
                this.updateCenterPaneWidth();
            }
        };
        
        const stopResize = () => {
            isResizing = false;
            currentHandle = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // Save pane sizes to preferences
            this.savePaneSizes();
        };
        
        // Event listeners
        leftHandle.addEventListener('mousedown', (e) => startResize(leftHandle, e));
        rightHandle.addEventListener('mousedown', (e) => startResize(rightHandle, e));
        document.addEventListener('mousemove', doResize);
        document.addEventListener('mouseup', stopResize);
        
        // Pane toggle buttons
        document.querySelectorAll('.pane-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const pane = e.target.dataset.pane;
                this.togglePane(pane);
            });
        });
    }
    
    updateCenterPaneWidth() {
        const leftPane = document.getElementById('left-pane');
        const rightPane = document.getElementById('right-pane');
        const centerPane = document.getElementById('center-pane');
        
        const leftWidth = parseFloat(leftPane.style.width) || 25;
        const rightWidth = parseFloat(rightPane.style.width) || 25;
        const centerWidth = 100 - leftWidth - rightWidth;
        
        centerPane.style.width = `${Math.max(30, centerWidth)}%`;
    }
    
    togglePane(pane) {
        const paneElement = document.getElementById(`${pane}-pane`);
        const toggleBtn = document.querySelector(`[data-pane="${pane}"]`);
        
        if (paneElement.classList.contains('collapsed')) {
            paneElement.classList.remove('collapsed');
            toggleBtn.textContent = pane === 'left' ? '◀' : '▶';
        } else {
            paneElement.classList.add('collapsed');
            toggleBtn.textContent = pane === 'left' ? '▶' : '◀';
        }
        
        this.updateCenterPaneWidth();
        this.savePaneSizes();
    }
    
    async connectToBackend() {
        console.log('🔗 Connecting to WriteCrew backend...');
        
        try {
            // Test connection
            const response = await this.crewAIService.testConnection();
            
            if (response.success) {
                this.isConnected = true;
                this.updateConnectionStatus('connected', 'Connected to WriteCrew');
                console.log('✅ Backend connection established');
            } else {
                throw new Error('Backend connection test failed');
            }
            
        } catch (error) {
            console.error('❌ Backend connection failed:', error);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected', 'Connection failed');
            
            // Show retry option
            this.showConnectionError(error);
        }
    }
    
    setupEventListeners() {
        // Header controls
        document.getElementById('settings-btn')?.addEventListener('click', () => {
            this.showSettingsModal();
        });
        
        document.getElementById('help-btn')?.addEventListener('click', () => {
            this.showHelpModal();
        });
        
        // Footer actions
        document.getElementById('export-session')?.addEventListener('click', () => {
            this.exportSession();
        });
        
        document.getElementById('clear-session')?.addEventListener('click', () => {
            this.clearSession();
        });
        
        // Word document events
        this.setupWordEventListeners();
        
        // Window events
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }
    
    setupWordEventListeners() {
        // Listen for document changes
        Office.context.document.addHandlerAsync(
            Office.EventType.DocumentSelectionChanged,
            this.handleSelectionChange.bind(this)
        );
        
        // Listen for document content changes
        if (Office.context.document.addHandlerAsync) {
            Office.context.document.addHandlerAsync(
                Office.EventType.DocumentChanged,
                this.handleDocumentChange.bind(this)
            );
        }
    }
    
    async loadUserSession() {
        console.log('👤 Loading user session...');
        
        try {
            // Load from local storage first
            const savedSession = localStorage.getItem('writecrew_session');
            if (savedSession) {
                this.userSession = JSON.parse(savedSession);
            }
            
            // Validate with backend
            if (this.userSession && this.isConnected) {
                const validation = await this.crewAIService.validateSession(this.userSession.token);
                
                if (!validation.valid) {
                    // Session expired, clear it
                    this.userSession = null;
                    localStorage.removeItem('writecrew_session');
                    this.showLoginModal();
                }
            } else if (!this.userSession) {
                // No session, show login
                this.showLoginModal();
            }
            
            // Load user preferences
            await this.loadUserPreferences();
            
        } catch (error) {
            console.error('Failed to load user session:', error);
            this.showLoginModal();
        }
    }
    
    async initializeAgents() {
        console.log('🤖 Initializing AI agents...');
        
        try {
            // Get available agents from backend
            const agentsResponse = await this.crewAIService.getAvailableAgents();
            
            if (agentsResponse.success) {
                const agentCardsContainer = document.getElementById('agent-cards-container');
                
                agentsResponse.agents.forEach(agentData => {
                    // Create agent card
                    const agentCard = new AgentCard(
                        agentData,
                        this.permissionManager,
                        this.handleAgentAction.bind(this)
                    );
                    
                    // Store reference
                    this.agentCards.set(agentData.id, agentCard);
                    
                    // Add to container
                    agentCardsContainer.appendChild(agentCard.element);
                });
                
                console.log(`✅ Initialized ${agentsResponse.agents.length} agents`);
            }
            
        } catch (error) {
            console.error('Failed to initialize agents:', error);
            this.showNotification('Failed to load AI agents', 'error');
        }
    }
    
    setupWebSocket() {
        if (!this.isConnected) return;
        
        console.log('🔌 Setting up WebSocket connection...');
        
        try {
            const wsUrl = this.getWebSocketUrl();
            this.webSocket = new WebSocket(wsUrl);
            
            this.webSocket.onopen = () => {
                console.log('✅ WebSocket connected');
                this.startHeartbeat();
            };
            
            this.webSocket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
            this.webSocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.stopHeartbeat();
                
                // Attempt reconnection
                setTimeout(() => {
                    if (this.isConnected) {
                        this.setupWebSocket();
                    }
                }, 5000);
            };
            
            this.webSocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.webSocket && this.webSocket.readyState === WebSocket.OPEN) {
                this.webSocket.send(JSON.stringify({ type: 'heartbeat' }));
            }
        }, 30000); // 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    handleWebSocketMessage(event) {
        try {
            const message = JSON.parse(event.data);
            
            switch (message.type) {
                case 'agent_update':
                    this.handleAgentUpdate(message.data);
                    break;
                case 'suggestion':
                    this.handleNewSuggestion(message.data);
                    break;
                case 'task_complete':
                    this.handleTaskComplete(message.data);
                    break;
                case 'error':
                    this.handleBackendError(message.data);
                    break;
                case 'notification':
                    this.showNotification(message.data.message, message.data.type);
                    break;
                default:
                    console.log('Unknown WebSocket message type:', message.type);
            }
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }
    
    // Event handlers
    handleChatAction(action, data) {
        switch (action) {
            case 'message_sent':
                this.updateStats('messagesSent', 1);
                break;
            case 'agent_selected':
                this.setActiveAgent(data.agentId);
                break;
            case 'get_document_context':
                return this.getDocumentContext();
            default:
                console.log('Unknown chat action:', action);
        }
    }
    
    handleSuggestionAction(action, data) {
        switch (action) {
            case 'approved':
                this.updateStats('suggestionsApproved', 1);
                this.updateStats('cost', data.cost || 0);
                break;
            case 'rejected':
                this.updateStats('suggestionsRejected', 1);
                break;
            case 'refresh_requested':
                this.refreshSuggestions();
                break;
            case 'suggestions_requested':
                this.requestSuggestions();
                break;
            default:
                console.log('Unknown suggestion action:', action);
        }
    }
    
    handleAgentAction(action, data) {
        switch (action) {
            case 'start':
                this.startAgent(data.agentId);
                break;
            case 'pause':
                this.pauseAgent(data.agentId);
                break;
            case 'settings':
                this.showAgentSettings(data.agentId);
                break;
            case 'permission_changed':
                this.updateAgentPermission(data.agentId, data.newLevel);
                break;
            default:
                console.log('Unknown agent action:', action);
        }
    }
    
    handleSelectionChange(eventArgs) {
        // Update current selection context
        this.currentSelection = eventArgs;
        
        // Notify components of selection change
        if (this.chatInterface) {
            this.chatInterface.updateDocumentContext(this.getDocumentContext());
        }
    }
    
    handleDocumentChange(eventArgs) {
        // Update document context
        this.currentDocument = eventArgs;
        
        // Auto-save if enabled
        if (this.settings.autoSave) {
            this.autoSave();
        }
        
        // Request suggestions if real-time sync is enabled
        if (this.settings.realTimeSync) {
            this.debounceRequestSuggestions();
        }
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Shift + W: Toggle WriteCrew
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'W') {
            e.preventDefault();
            this.toggleWriteCrew();
        }
        
        // Ctrl/Cmd + Shift + C: Focus chat
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            this.focusChat();
        }
        
        // Ctrl/Cmd + Shift + S: Focus suggestions
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            this.focusSuggestions();
        }
    }
    
    // Agent management
    async startAgent(agentId) {
        try {
            const response = await this.crewAIService.startAgent(agentId);
            
            if (response.success) {
                this.activeAgents.set(agentId, { status: 'active', startTime: Date.now() });
                
                const agentCard = this.agentCards.get(agentId);
                if (agentCard) {
                    agentCard.updateStatus('active');
                }
                
                this.showNotification(`${this.getAgentName(agentId)} activated`, 'success');
            }
            
        } catch (error) {
            console.error(`Failed to start agent ${agentId}:`, error);
            this.showNotification(`Failed to activate ${this.getAgentName(agentId)}`, 'error');
        }
    }
    
    async pauseAgent(agentId) {
        try {
            const response = await this.crewAIService.pauseAgent(agentId);
            
            if (response.success) {
                this.activeAgents.delete(agentId);
                
                const agentCard = this.agentCards.get(agentId);
                if (agentCard) {
                    agentCard.updateStatus('paused');
                }
                
                this.showNotification(`${this.getAgentName(agentId)} paused`, 'info');
            }
            
        } catch (error) {
            console.error(`Failed to pause agent ${agentId}:`, error);
            this.showNotification(`Failed to pause ${this.getAgentName(agentId)}`, 'error');
        }
    }
    
    // Utility methods
    getBackendUrl() {
        return process.env.WRITECREW_BACKEND_URL || 'http://localhost:8000';
    }
    
    getWebSocketUrl() {
        const backendUrl = this.getBackendUrl();
        return backendUrl.replace('http', 'ws') + '/ws';
    }
    
    async getApiKey() {
        // In production, this would be handled securely
        return localStorage.getItem('writecrew_api_key') || '';
    }
    
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
    
    updateConnectionStatus(status, message) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            statusElement.querySelector('.status-text').textContent = message;
        }
    }
    
    updateStats(statName, value) {
        const statElement = document.querySelector(`#${statName.replace(/([A-Z])/g, '-$1').toLowerCase()} .stat-value`);
        if (statElement) {
            const currentValue = parseFloat(statElement.textContent) || 0;
            statElement.textContent = statName === 'cost' ? 
                `$${(currentValue + value).toFixed(2)}` : 
                (currentValue + value).toString();
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">×</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
    
    showWelcomeMessage() {
        if (this.chatInterface) {
            this.chatInterface.addSystemMessage(
                '🎉 Welcome to WriteCrew! Your AI writing assistants are ready to help. Select an agent to get started.'
            );
        }
    }
    
    startPerformanceMonitoring() {
        // Monitor performance metrics
        setInterval(() => {
            this.collectPerformanceMetrics();
        }, 60000); // Every minute
    }
    
    collectPerformanceMetrics() {
        this.performanceMetrics.uptime = Date.now() - this.performanceMetrics.startTime;
        this.performanceMetrics.activeAgents = this.activeAgents.size;
        this.performanceMetrics.memoryUsage = performance.memory ? performance.memory.usedJSHeapSize : 0;
        
        // Send to backend for analysis
        if (this.isConnected) {
            this.crewAIService.sendMetrics(this.performanceMetrics);
        }
    }
    
    getDocumentContext() {
        return {
            selection: this.currentSelection,
            document: this.currentDocument,
            activeAgents: Array.from(this.activeAgents.keys()),
            timestamp: Date.now()
        };
    }
    
    savePaneSizes() {
        const leftPane = document.getElementById('left-pane');
        const rightPane = document.getElementById('right-pane');
        
        const sizes = {
            left: parseFloat(leftPane.style.width) || 25,
            right: parseFloat(rightPane.style.width) || 25
        };
        
        localStorage.setItem('writecrew_pane_sizes', JSON.stringify(sizes));
    }
    
    loadPaneSizes() {
        try {
            const saved = localStorage.getItem('writecrew_pane_sizes');
            if (saved) {
                const sizes = JSON.parse(saved);
                
                const leftPane = document.getElementById('left-pane');
                const rightPane = document.getElementById('right-pane');
                
                leftPane.style.width = `${sizes.left}%`;
                rightPane.style.width = `${sizes.right}%`;
                
                this.updateCenterPaneWidth();
            }
        } catch (error) {
            console.error('Failed to load pane sizes:', error);
        }
    }
    
    cleanup() {
        console.log('🧹 Cleaning up WriteCrew...');
        
        // Close WebSocket
        if (this.webSocket) {
            this.webSocket.close();
        }
        
        // Stop heartbeat
        this.stopHeartbeat();
        
        // Save session data
        this.saveSession();
        
        // Cleanup components
        if (this.chatInterface) {
            this.chatInterface.destroy();
        }
        
        if (this.suggestionsPanel) {
            this.suggestionsPanel.destroy();
        }
        
        this.agentCards.forEach(card => card.destroy());
    }
    
    saveSession() {
        if (this.userSession) {
            localStorage.setItem('writecrew_session', JSON.stringify(this.userSession));
        }
    }
    
    // Error handling
    handleInitializationError(error) {
        const container = document.getElementById('writecrew-container');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <h3>WriteCrew Initialization Failed</h3>
                    <p>${error.message}</p>
                    <button class="retry-btn" onclick="location.reload()">
                        🔄 Retry
                    </button>
                </div>
            `;
        }
    }
    
    handleBackendError(error) {
        console.error('Backend error:', error);
        this.showNotification(`Backend error: ${error.message}`, 'error');
        
        if (error.code === 'CONNECTION_LOST') {
            this.isConnected = false;
            this.updateConnectionStatus('disconnected', 'Connection lost');
            
            // Attempt reconnection
            setTimeout(() => {
                this.connectToBackend();
            }, 5000);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.writeCrew = new MainController();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MainController;
} else {
    window.MainController = MainController;
}

