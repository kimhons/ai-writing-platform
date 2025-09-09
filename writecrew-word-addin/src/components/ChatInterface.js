/**
 * ChatInterface Component
 * Handles natural language communication with AI agents
 */

class ChatInterface {
    constructor(crewAIService, onMessageAction) {
        this.crewAIService = crewAIService;
        this.onMessageAction = onMessageAction;
        this.element = null;
        this.messageHistory = [];
        this.activeAgent = null;
        this.isTyping = false;
        this.messageCounter = 0;
        
        this.init();
    }
    
    init() {
        this.element = this.createElement();
        this.attachEventListeners();
        this.loadMessageHistory();
    }
    
    createElement() {
        const chatContainer = document.createElement('div');
        chatContainer.className = 'chat-interface';
        
        chatContainer.innerHTML = `
            <div class="chat-header">
                <div class="chat-title">
                    <h3>Agent Chat</h3>
                    <div class="agent-selector">
                        <select class="active-agent-select" aria-label="Select active agent">
                            <option value="">Select Agent...</option>
                            <option value="master_router">🎯 Master Router</option>
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
                    </div>
                </div>
                <div class="chat-status">
                    <span class="connection-status connected">
                        <span class="status-indicator"></span>
                        Connected
                    </span>
                </div>
            </div>
            
            <div class="chat-messages" role="log" aria-live="polite" aria-label="Chat messages">
                <div class="welcome-message">
                    <div class="message system-message">
                        <div class="message-content">
                            <p>👋 Welcome to WriteCrew! Select an agent above to start collaborating.</p>
                            <div class="quick-actions">
                                <button class="quick-action" data-action="help">
                                    ❓ Get Help
                                </button>
                                <button class="quick-action" data-action="start-writing">
                                    ✍️ Start Writing
                                </button>
                                <button class="quick-action" data-action="improve-text">
                                    ✨ Improve Text
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="chat-input-container">
                <div class="typing-indicator" style="display: none;">
                    <div class="typing-dots">
                        <span class="agent-name"></span> is typing
                        <span class="dot">.</span>
                        <span class="dot">.</span>
                        <span class="dot">.</span>
                    </div>
                </div>
                
                <div class="chat-input-wrapper">
                    <div class="input-controls">
                        <button class="attachment-btn" aria-label="Attach file" title="Attach file">
                            📎
                        </button>
                        <button class="voice-btn" aria-label="Voice input" title="Voice input">
                            🎤
                        </button>
                    </div>
                    
                    <div class="input-field-container">
                        <textarea 
                            class="chat-input" 
                            placeholder="Type your message to the agent..."
                            rows="1"
                            aria-label="Chat message input"
                        ></textarea>
                        <div class="input-suggestions" style="display: none;">
                            <div class="suggestion-item" data-suggestion="Can you help me write a professional email?">
                                Can you help me write a professional email?
                            </div>
                            <div class="suggestion-item" data-suggestion="Please review this paragraph for grammar errors">
                                Please review this paragraph for grammar errors
                            </div>
                            <div class="suggestion-item" data-suggestion="Suggest improvements to make this more engaging">
                                Suggest improvements to make this more engaging
                            </div>
                        </div>
                    </div>
                    
                    <button class="send-btn" aria-label="Send message" disabled>
                        <span class="send-icon">➤</span>
                    </button>
                </div>
                
                <div class="chat-footer">
                    <div class="message-count">
                        <span class="count">0</span> messages
                    </div>
                    <div class="chat-actions">
                        <button class="clear-chat" title="Clear chat history">
                            🗑️ Clear
                        </button>
                        <button class="export-chat" title="Export chat">
                            📤 Export
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return chatContainer;
    }
    
    attachEventListeners() {
        const agentSelect = this.element.querySelector('.active-agent-select');
        const chatInput = this.element.querySelector('.chat-input');
        const sendBtn = this.element.querySelector('.send-btn');
        const quickActions = this.element.querySelectorAll('.quick-action');
        const attachmentBtn = this.element.querySelector('.attachment-btn');
        const voiceBtn = this.element.querySelector('.voice-btn');
        const clearBtn = this.element.querySelector('.clear-chat');
        const exportBtn = this.element.querySelector('.export-chat');
        const suggestions = this.element.querySelectorAll('.suggestion-item');
        
        // Agent selection
        agentSelect.addEventListener('change', (e) => {
            this.setActiveAgent(e.target.value);
        });
        
        // Chat input handling
        chatInput.addEventListener('input', (e) => {
            this.handleInputChange(e);
        });
        
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        });
        
        // Send button
        sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Quick actions
        quickActions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleQuickAction(e.target.dataset.action);
            });
        });
        
        // Suggestion items
        suggestions.forEach(item => {
            item.addEventListener('click', (e) => {
                chatInput.value = e.target.dataset.suggestion;
                this.handleInputChange({ target: chatInput });
                chatInput.focus();
                this.hideSuggestions();
            });
        });
        
        // Input focus/blur for suggestions
        chatInput.addEventListener('focus', () => {
            if (!chatInput.value.trim()) {
                this.showSuggestions();
            }
        });
        
        chatInput.addEventListener('blur', (e) => {
            // Delay hiding to allow clicking on suggestions
            setTimeout(() => {
                if (!this.element.querySelector('.input-suggestions:hover')) {
                    this.hideSuggestions();
                }
            }, 200);
        });
        
        // Attachment button
        attachmentBtn.addEventListener('click', () => {
            this.handleAttachment();
        });
        
        // Voice button
        voiceBtn.addEventListener('click', () => {
            this.handleVoiceInput();
        });
        
        // Clear chat
        clearBtn.addEventListener('click', () => {
            this.clearChat();
        });
        
        // Export chat
        exportBtn.addEventListener('click', () => {
            this.exportChat();
        });
    }
    
    setActiveAgent(agentId) {
        this.activeAgent = agentId;
        const chatInput = this.element.querySelector('.chat-input');
        
        if (agentId) {
            chatInput.placeholder = `Type your message to ${this.getAgentName(agentId)}...`;
            chatInput.disabled = false;
            
            // Add agent selection message
            this.addSystemMessage(`Connected to ${this.getAgentName(agentId)}. How can I help you today?`);
        } else {
            chatInput.placeholder = 'Select an agent to start chatting...';
            chatInput.disabled = true;
        }
        
        this.updateSendButtonState();
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
    
    handleInputChange(e) {
        const input = e.target.value;
        this.updateSendButtonState();
        
        // Show/hide suggestions
        if (input.trim() === '') {
            this.showSuggestions();
        } else {
            this.hideSuggestions();
        }
    }
    
    updateSendButtonState() {
        const chatInput = this.element.querySelector('.chat-input');
        const sendBtn = this.element.querySelector('.send-btn');
        
        const hasText = chatInput.value.trim().length > 0;
        const hasAgent = this.activeAgent !== null;
        
        sendBtn.disabled = !hasText || !hasAgent || this.isTyping;
    }
    
    async sendMessage() {
        const chatInput = this.element.querySelector('.chat-input');
        const message = chatInput.value.trim();
        
        if (!message || !this.activeAgent || this.isTyping) return;
        
        // Add user message to chat
        this.addMessage({
            id: `msg_${++this.messageCounter}`,
            type: 'user',
            content: message,
            timestamp: new Date(),
            agentId: this.activeAgent
        });
        
        // Clear input
        chatInput.value = '';
        chatInput.style.height = 'auto';
        this.updateSendButtonState();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to agent
            const response = await this.crewAIService.sendMessage({
                agentId: this.activeAgent,
                message: message,
                context: this.getConversationContext()
            });
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add agent response
            this.addMessage({
                id: `msg_${++this.messageCounter}`,
                type: 'agent',
                content: response.content,
                timestamp: new Date(),
                agentId: this.activeAgent,
                confidence: response.confidence,
                suggestions: response.suggestions
            });
            
            // Trigger callback for any actions
            if (this.onMessageAction && response.actions) {
                response.actions.forEach(action => {
                    this.onMessageAction(action.type, action.data);
                });
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            
            this.addMessage({
                id: `msg_${++this.messageCounter}`,
                type: 'error',
                content: 'Sorry, I encountered an error processing your message. Please try again.',
                timestamp: new Date(),
                agentId: this.activeAgent
            });
        }
    }
    
    addMessage(message) {
        const messagesContainer = this.element.querySelector('.chat-messages');
        const messageElement = this.createMessageElement(message);
        
        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Update message history
        this.messageHistory.push(message);
        this.updateMessageCount();
        
        // Save to local storage
        this.saveMessageHistory();
    }
    
    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type}-message`;
        messageDiv.setAttribute('data-message-id', message.id);
        
        const timestamp = this.formatTimestamp(message.timestamp);
        
        let messageHTML = '';
        
        if (message.type === 'user') {
            messageHTML = `
                <div class="message-header">
                    <span class="sender">You</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
                <div class="message-content">
                    <p>${this.escapeHtml(message.content)}</p>
                </div>
            `;
        } else if (message.type === 'agent') {
            messageHTML = `
                <div class="message-header">
                    <span class="sender">
                        ${this.getAgentIcon(message.agentId)} ${this.getAgentName(message.agentId)}
                    </span>
                    <span class="timestamp">${timestamp}</span>
                    ${message.confidence ? `<span class="confidence">Confidence: ${(message.confidence * 100).toFixed(0)}%</span>` : ''}
                </div>
                <div class="message-content">
                    <div class="message-text">${this.formatMessageContent(message.content)}</div>
                    ${message.suggestions ? this.renderSuggestions(message.suggestions) : ''}
                </div>
                <div class="message-actions">
                    <button class="action-btn copy-btn" title="Copy message">📋</button>
                    <button class="action-btn like-btn" title="Helpful">👍</button>
                    <button class="action-btn dislike-btn" title="Not helpful">👎</button>
                </div>
            `;
        } else if (message.type === 'system') {
            messageHTML = `
                <div class="message-content">
                    <p class="system-text">${this.escapeHtml(message.content)}</p>
                </div>
            `;
        } else if (message.type === 'error') {
            messageHTML = `
                <div class="message-content">
                    <p class="error-text">⚠️ ${this.escapeHtml(message.content)}</p>
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageHTML;
        
        // Attach message-specific event listeners
        this.attachMessageEventListeners(messageDiv, message);
        
        return messageDiv;
    }
    
    attachMessageEventListeners(messageElement, message) {
        const copyBtn = messageElement.querySelector('.copy-btn');
        const likeBtn = messageElement.querySelector('.like-btn');
        const dislikeBtn = messageElement.querySelector('.dislike-btn');
        
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(message.content);
                copyBtn.textContent = '✅';
                setTimeout(() => copyBtn.textContent = '📋', 2000);
            });
        }
        
        if (likeBtn) {
            likeBtn.addEventListener('click', () => {
                this.handleMessageFeedback(message.id, 'like');
                likeBtn.classList.add('active');
                dislikeBtn.classList.remove('active');
            });
        }
        
        if (dislikeBtn) {
            dislikeBtn.addEventListener('click', () => {
                this.handleMessageFeedback(message.id, 'dislike');
                dislikeBtn.classList.add('active');
                likeBtn.classList.remove('active');
            });
        }
    }
    
    renderSuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) return '';
        
        return `
            <div class="message-suggestions">
                <h5>Suggestions:</h5>
                <div class="suggestion-list">
                    ${suggestions.map((suggestion, index) => `
                        <button class="suggestion-btn" data-suggestion="${this.escapeHtml(suggestion)}">
                            ${this.escapeHtml(suggestion)}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
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
    
    formatMessageContent(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        const indicator = this.element.querySelector('.typing-indicator');
        const agentName = this.element.querySelector('.typing-indicator .agent-name');
        
        agentName.textContent = this.getAgentName(this.activeAgent);
        indicator.style.display = 'block';
        
        this.updateSendButtonState();
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        const indicator = this.element.querySelector('.typing-indicator');
        indicator.style.display = 'none';
        
        this.updateSendButtonState();
    }
    
    showSuggestions() {
        const suggestions = this.element.querySelector('.input-suggestions');
        suggestions.style.display = 'block';
    }
    
    hideSuggestions() {
        const suggestions = this.element.querySelector('.input-suggestions');
        suggestions.style.display = 'none';
    }
    
    addSystemMessage(content) {
        this.addMessage({
            id: `sys_${++this.messageCounter}`,
            type: 'system',
            content: content,
            timestamp: new Date()
        });
    }
    
    handleQuickAction(action) {
        const actions = {
            'help': 'Can you help me understand how to use WriteCrew effectively?',
            'start-writing': 'I want to start writing a new document. Can you help me get started?',
            'improve-text': 'Please help me improve the selected text in my document.'
        };
        
        const message = actions[action];
        if (message) {
            const chatInput = this.element.querySelector('.chat-input');
            chatInput.value = message;
            this.handleInputChange({ target: chatInput });
            chatInput.focus();
        }
    }
    
    handleAttachment() {
        // Create file input
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.txt,.doc,.docx,.pdf';
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.uploadFile(file);
            }
        });
        
        fileInput.click();
    }
    
    async uploadFile(file) {
        try {
            // Show upload progress
            this.addSystemMessage(`Uploading ${file.name}...`);
            
            // Upload file (implementation depends on backend)
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.addSystemMessage(`File uploaded successfully: ${file.name}`);
                
                // Add file reference to next message
                this.pendingAttachment = {
                    filename: file.name,
                    fileId: result.fileId,
                    type: file.type
                };
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            console.error('File upload error:', error);
            this.addSystemMessage(`Failed to upload ${file.name}. Please try again.`);
        }
    }
    
    handleVoiceInput() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            const voiceBtn = this.element.querySelector('.voice-btn');
            voiceBtn.textContent = '🔴';
            voiceBtn.disabled = true;
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const chatInput = this.element.querySelector('.chat-input');
                chatInput.value = transcript;
                this.handleInputChange({ target: chatInput });
            };
            
            recognition.onend = () => {
                voiceBtn.textContent = '🎤';
                voiceBtn.disabled = false;
            };
            
            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                voiceBtn.textContent = '🎤';
                voiceBtn.disabled = false;
            };
            
            recognition.start();
        } else {
            alert('Speech recognition is not supported in your browser.');
        }
    }
    
    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.messageHistory = [];
            const messagesContainer = this.element.querySelector('.chat-messages');
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="message system-message">
                        <div class="message-content">
                            <p>👋 Welcome to WriteCrew! Select an agent above to start collaborating.</p>
                        </div>
                    </div>
                </div>
            `;
            this.updateMessageCount();
            this.saveMessageHistory();
        }
    }
    
    exportChat() {
        const chatData = {
            timestamp: new Date().toISOString(),
            activeAgent: this.activeAgent,
            messages: this.messageHistory
        };
        
        const blob = new Blob([JSON.stringify(chatData, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `writecrew-chat-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
    
    updateMessageCount() {
        const countElement = this.element.querySelector('.message-count .count');
        countElement.textContent = this.messageHistory.length;
    }
    
    getConversationContext() {
        return {
            recentMessages: this.messageHistory.slice(-5),
            activeAgent: this.activeAgent,
            documentContext: this.onMessageAction ? 
                this.onMessageAction('get_document_context') : null
        };
    }
    
    handleMessageFeedback(messageId, feedback) {
        // Send feedback to backend for model improvement
        if (this.crewAIService.sendFeedback) {
            this.crewAIService.sendFeedback(messageId, feedback);
        }
    }
    
    saveMessageHistory() {
        try {
            localStorage.setItem('writecrew_chat_history', JSON.stringify(this.messageHistory));
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }
    
    loadMessageHistory() {
        try {
            const saved = localStorage.getItem('writecrew_chat_history');
            if (saved) {
                this.messageHistory = JSON.parse(saved);
                this.updateMessageCount();
                
                // Restore messages to UI
                this.messageHistory.forEach(message => {
                    const messageElement = this.createMessageElement(message);
                    const messagesContainer = this.element.querySelector('.chat-messages');
                    messagesContainer.appendChild(messageElement);
                });
                
                // Scroll to bottom
                const messagesContainer = this.element.querySelector('.chat-messages');
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }
    
    updateConnectionStatus(isConnected) {
        const statusElement = this.element.querySelector('.connection-status');
        if (isConnected) {
            statusElement.className = 'connection-status connected';
            statusElement.innerHTML = '<span class="status-indicator"></span>Connected';
        } else {
            statusElement.className = 'connection-status disconnected';
            statusElement.innerHTML = '<span class="status-indicator"></span>Disconnected';
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
    module.exports = ChatInterface;
} else {
    window.ChatInterface = ChatInterface;
}

