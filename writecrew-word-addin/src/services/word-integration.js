/*
 * Word Integration Service - Office.js API Integration
 * Handles all Microsoft Word document manipulation and integration
 */

/**
 * Word Integration Service Class
 * Manages all interactions with Microsoft Word through Office.js APIs
 */
export class WordIntegrationService {
    constructor() {
        this.isInitialized = false;
        this.documentContext = null;
        this.changeTracking = new Map();
        this.contentControls = new Map();
        this.comments = new Map();
        
        // Event listeners for Word events
        this.eventListeners = new Map();
        
        console.log('Word Integration Service initialized');
    }

    /**
     * Initialize Word integration and test connection
     */
    async testWordConnection() {
        try {
            await this.ensureWordContext();
            console.log('Word Integration Service: Connection test successful');
            return true;
        } catch (error) {
            console.error('Word Integration Service: Connection test failed', error);
            throw new Error(`Failed to connect to Microsoft Word: ${error.message}`);
        }
    }

    /**
     * Ensure Word context is available
     */
    async ensureWordContext() {
        return new Promise((resolve, reject) => {
            if (typeof Office === 'undefined') {
                reject(new Error('Office.js not available'));
                return;
            }

            if (Office.context && Office.context.host === Office.HostType.Word) {
                this.isInitialized = true;
                resolve();
            } else {
                reject(new Error('Word context not available'));
            }
        });
    }

    /**
     * Get current document context and metadata
     */
    async getDocumentContext() {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                // Get document properties
                const document = context.document;
                const properties = document.properties;
                const body = document.body;
                
                // Load properties
                properties.load(['title', 'author', 'creationDate', 'lastModifiedDate']);
                body.load(['text']);
                
                await context.sync();
                
                // Get selection information
                const selection = context.document.getSelection();
                selection.load(['text', 'isEmpty']);
                await context.sync();
                
                // Get paragraph count and word count
                const paragraphs = body.paragraphs;
                paragraphs.load(['items']);
                await context.sync();
                
                const documentContext = {
                    title: properties.title || 'Untitled Document',
                    author: properties.author || 'Unknown',
                    creationDate: properties.creationDate,
                    lastModifiedDate: properties.lastModifiedDate,
                    wordCount: this.estimateWordCount(body.text),
                    paragraphCount: paragraphs.items.length,
                    selectedText: selection.text,
                    hasSelection: !selection.isEmpty,
                    documentText: body.text.substring(0, 1000), // First 1000 chars for context
                    timestamp: new Date().toISOString()
                };
                
                this.documentContext = documentContext;
                console.log('Word Integration Service: Document context retrieved', documentContext);
                
                return documentContext;
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to get document context', error);
            throw error;
        }
    }

    /**
     * Insert content at specified location with formatting
     */
    async insertContent(content, options = {}) {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                const {
                    location = Word.InsertLocation.end,
                    formatting = {},
                    trackChanges = true,
                    agentId = 'unknown'
                } = options;
                
                // Get insertion point
                let insertionPoint;
                if (options.range) {
                    insertionPoint = options.range;
                } else if (options.useSelection) {
                    insertionPoint = context.document.getSelection();
                } else {
                    insertionPoint = context.document.body;
                }
                
                // Insert content
                const paragraph = insertionPoint.insertParagraph(content, location);
                
                // Apply formatting
                if (formatting.fontName) {
                    paragraph.font.name = formatting.fontName;
                }
                if (formatting.fontSize) {
                    paragraph.font.size = formatting.fontSize;
                }
                if (formatting.fontColor) {
                    paragraph.font.color = formatting.fontColor;
                }
                if (formatting.bold) {
                    paragraph.font.bold = formatting.bold;
                }
                if (formatting.italic) {
                    paragraph.font.italic = formatting.italic;
                }
                
                // Add WriteCrew metadata
                const contentControl = paragraph.insertContentControl();
                contentControl.tag = `writecrew-${agentId}-${Date.now()}`;
                contentControl.title = `WriteCrew: ${agentId}`;
                
                // Track changes if enabled
                if (trackChanges) {
                    await this.trackContentChange({
                        type: 'insert',
                        content: content,
                        agentId: agentId,
                        location: location,
                        timestamp: new Date().toISOString(),
                        contentControlTag: contentControl.tag
                    });
                }
                
                await context.sync();
                
                console.log('Word Integration Service: Content inserted successfully', {
                    content: content.substring(0, 100),
                    agentId,
                    location
                });
                
                return {
                    success: true,
                    contentControlTag: contentControl.tag,
                    insertedText: content
                };
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to insert content', error);
            throw error;
        }
    }

    /**
     * Replace content in specified range
     */
    async replaceContent(oldContent, newContent, options = {}) {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                const {
                    agentId = 'unknown',
                    trackChanges = true
                } = options;
                
                // Search for the old content
                const searchResults = context.document.body.search(oldContent, {
                    matchCase: false,
                    matchWholeWord: false
                });
                
                searchResults.load(['items']);
                await context.sync();
                
                if (searchResults.items.length === 0) {
                    throw new Error('Content to replace not found');
                }
                
                // Replace first occurrence
                const range = searchResults.items[0];
                range.insertText(newContent, Word.InsertLocation.replace);
                
                // Add content control for tracking
                const contentControl = range.insertContentControl();
                contentControl.tag = `writecrew-replace-${agentId}-${Date.now()}`;
                contentControl.title = `WriteCrew Replace: ${agentId}`;
                
                // Track changes if enabled
                if (trackChanges) {
                    await this.trackContentChange({
                        type: 'replace',
                        oldContent: oldContent,
                        newContent: newContent,
                        agentId: agentId,
                        timestamp: new Date().toISOString(),
                        contentControlTag: contentControl.tag
                    });
                }
                
                await context.sync();
                
                console.log('Word Integration Service: Content replaced successfully', {
                    oldContent: oldContent.substring(0, 50),
                    newContent: newContent.substring(0, 50),
                    agentId
                });
                
                return {
                    success: true,
                    replacedCount: 1,
                    contentControlTag: contentControl.tag
                };
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to replace content', error);
            throw error;
        }
    }

    /**
     * Add comment/suggestion to document
     */
    async addComment(text, suggestion, options = {}) {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                const {
                    agentId = 'unknown',
                    suggestionType = 'general',
                    range = null
                } = options;
                
                // Get target range
                let targetRange;
                if (range) {
                    targetRange = range;
                } else {
                    targetRange = context.document.getSelection();
                    if (targetRange.isEmpty) {
                        // If no selection, use current paragraph
                        targetRange = context.document.body.paragraphs.getFirst();
                    }
                }
                
                // Create comment
                const comment = targetRange.insertComment(`WriteCrew ${agentId}: ${suggestion}`);
                comment.content = `${suggestionType.toUpperCase()}: ${suggestion}`;
                
                // Add reply with reasoning if provided
                if (options.reasoning) {
                    comment.replies.add(`Reasoning: ${options.reasoning}`);
                }
                
                // Store comment reference
                const commentId = `comment-${agentId}-${Date.now()}`;
                this.comments.set(commentId, {
                    id: commentId,
                    agentId: agentId,
                    text: text,
                    suggestion: suggestion,
                    type: suggestionType,
                    timestamp: new Date().toISOString(),
                    comment: comment
                });
                
                await context.sync();
                
                console.log('Word Integration Service: Comment added successfully', {
                    agentId,
                    suggestion: suggestion.substring(0, 100),
                    commentId
                });
                
                return {
                    success: true,
                    commentId: commentId,
                    comment: comment
                };
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to add comment', error);
            throw error;
        }
    }

    /**
     * Highlight text with specific color and agent identification
     */
    async highlightText(text, options = {}) {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                const {
                    color = '#FFFF00', // Yellow default
                    agentId = 'unknown',
                    reason = 'Agent suggestion'
                } = options;
                
                // Search for text to highlight
                const searchResults = context.document.body.search(text, {
                    matchCase: false,
                    matchWholeWord: false
                });
                
                searchResults.load(['items']);
                await context.sync();
                
                if (searchResults.items.length === 0) {
                    throw new Error('Text to highlight not found');
                }
                
                // Highlight all occurrences
                let highlightedCount = 0;
                for (const range of searchResults.items) {
                    range.font.highlightColor = color;
                    
                    // Add content control for tracking
                    const contentControl = range.insertContentControl();
                    contentControl.tag = `writecrew-highlight-${agentId}-${Date.now()}-${highlightedCount}`;
                    contentControl.title = `WriteCrew Highlight: ${reason}`;
                    
                    highlightedCount++;
                }
                
                await context.sync();
                
                console.log('Word Integration Service: Text highlighted successfully', {
                    text: text.substring(0, 50),
                    color,
                    agentId,
                    count: highlightedCount
                });
                
                return {
                    success: true,
                    highlightedCount: highlightedCount
                };
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to highlight text', error);
            throw error;
        }
    }

    /**
     * Get selected text and context
     */
    async getSelection() {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                const selection = context.document.getSelection();
                selection.load(['text', 'isEmpty']);
                
                // Get surrounding context
                const expandedRange = selection.expandTo(selection.paragraphs.getFirst());
                expandedRange.load(['text']);
                
                await context.sync();
                
                const selectionInfo = {
                    selectedText: selection.text,
                    hasSelection: !selection.isEmpty,
                    contextText: expandedRange.text,
                    wordCount: this.estimateWordCount(selection.text),
                    timestamp: new Date().toISOString()
                };
                
                console.log('Word Integration Service: Selection retrieved', selectionInfo);
                return selectionInfo;
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to get selection', error);
            throw error;
        }
    }

    /**
     * Apply formatting to specified range
     */
    async applyFormatting(range, formatting) {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                // Apply formatting options
                if (formatting.fontName) {
                    range.font.name = formatting.fontName;
                }
                if (formatting.fontSize) {
                    range.font.size = formatting.fontSize;
                }
                if (formatting.fontColor) {
                    range.font.color = formatting.fontColor;
                }
                if (formatting.bold !== undefined) {
                    range.font.bold = formatting.bold;
                }
                if (formatting.italic !== undefined) {
                    range.font.italic = formatting.italic;
                }
                if (formatting.underline !== undefined) {
                    range.font.underline = formatting.underline;
                }
                if (formatting.highlightColor) {
                    range.font.highlightColor = formatting.highlightColor;
                }
                
                await context.sync();
                
                console.log('Word Integration Service: Formatting applied successfully', formatting);
                return { success: true };
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to apply formatting', error);
            throw error;
        }
    }

    /**
     * Track content changes for audit and undo functionality
     */
    async trackContentChange(changeData) {
        const changeId = `change-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        this.changeTracking.set(changeId, {
            id: changeId,
            ...changeData,
            tracked_at: new Date().toISOString()
        });
        
        // Emit change event
        this.emit('content:changed', {
            changeId,
            ...changeData
        });
        
        console.log('Word Integration Service: Content change tracked', changeId, changeData);
        return changeId;
    }

    /**
     * Get all tracked changes
     */
    getTrackedChanges() {
        return Array.from(this.changeTracking.values());
    }

    /**
     * Get content controls created by WriteCrew
     */
    async getWriteCrewContentControls() {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                const contentControls = context.document.contentControls;
                contentControls.load(['items']);
                await context.sync();
                
                const writeCrewControls = [];
                
                for (const control of contentControls.items) {
                    control.load(['tag', 'title', 'text']);
                    await context.sync();
                    
                    if (control.tag && control.tag.startsWith('writecrew-')) {
                        writeCrewControls.push({
                            tag: control.tag,
                            title: control.title,
                            text: control.text,
                            control: control
                        });
                    }
                }
                
                console.log('Word Integration Service: WriteCrew content controls retrieved', writeCrewControls.length);
                return writeCrewControls;
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to get content controls', error);
            throw error;
        }
    }

    /**
     * Remove WriteCrew content control
     */
    async removeContentControl(tag) {
        try {
            await this.ensureWordContext();
            
            return await Word.run(async (context) => {
                const contentControls = context.document.contentControls;
                contentControls.load(['items']);
                await context.sync();
                
                for (const control of contentControls.items) {
                    control.load(['tag']);
                    await context.sync();
                    
                    if (control.tag === tag) {
                        control.delete(false); // Keep content, remove control
                        await context.sync();
                        
                        console.log('Word Integration Service: Content control removed', tag);
                        return { success: true };
                    }
                }
                
                throw new Error(`Content control with tag ${tag} not found`);
            });
            
        } catch (error) {
            console.error('Word Integration Service: Failed to remove content control', error);
            throw error;
        }
    }

    /**
     * Estimate word count from text
     */
    estimateWordCount(text) {
        if (!text || typeof text !== 'string') return 0;
        return text.trim().split(/\s+/).filter(word => word.length > 0).length;
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
                    console.error(`Word Integration Service: Error in event listener for ${event}`, error);
                }
            });
        }
    }

    /**
     * Get current document statistics
     */
    async getDocumentStats() {
        try {
            const context = await this.getDocumentContext();
            const changes = this.getTrackedChanges();
            const controls = await this.getWriteCrewContentControls();
            
            return {
                wordCount: context.wordCount,
                paragraphCount: context.paragraphCount,
                writeCrewChanges: changes.length,
                writeCrewControls: controls.length,
                lastModified: context.lastModifiedDate,
                hasSelection: context.hasSelection
            };
            
        } catch (error) {
            console.error('Word Integration Service: Failed to get document stats', error);
            throw error;
        }
    }

    /**
     * Cleanup resources
     */
    destroy() {
        this.changeTracking.clear();
        this.contentControls.clear();
        this.comments.clear();
        this.eventListeners.clear();
        this.documentContext = null;
        this.isInitialized = false;
    }
}

