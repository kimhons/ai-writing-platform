/*
 * WriteCrew Commands - Office Ribbon Integration
 * Handles commands executed from the Office ribbon
 */

/**
 * Initialize Office.js when ready
 */
Office.onReady(() => {
    console.log('WriteCrew Commands: Office.js ready');
});

/**
 * Show WriteCrew task pane
 * Called when user clicks WriteCrew button in ribbon
 */
function showTaskPane(event) {
    console.log('WriteCrew Commands: Show task pane requested');
    
    // The task pane will be shown automatically by Office.js
    // based on the manifest configuration
    
    // Complete the event
    if (event) {
        event.completed();
    }
}

/**
 * Quick insert AI suggestion
 * Ribbon command for quick AI assistance
 */
function quickAISuggestion(event) {
    console.log('WriteCrew Commands: Quick AI suggestion requested');
    
    Word.run(async (context) => {
        try {
            // Get current selection
            const selection = context.document.getSelection();
            selection.load('text');
            await context.sync();
            
            // Insert a placeholder or trigger AI suggestion
            if (selection.text.trim() === '') {
                selection.insertText('[WriteCrew AI Suggestion]', Word.InsertLocation.replace);
            } else {
                // Add comment with AI suggestion request
                selection.insertComment('WriteCrew: AI suggestion requested for this text');
            }
            
            await context.sync();
            
            // Notify task pane if open
            Office.ribbon.requestUpdate({
                tabs: [{
                    id: 'WriteCrew.Tab',
                    groups: [{
                        id: 'WriteCrew.Group1',
                        controls: [{
                            id: 'WriteCrew.QuickSuggestion',
                            enabled: true
                        }]
                    }]
                }]
            });
            
        } catch (error) {
            console.error('WriteCrew Commands: Quick AI suggestion failed', error);
        }
        
        // Complete the event
        if (event) {
            event.completed();
        }
    });
}

/**
 * Toggle WriteCrew tracking
 * Enable/disable WriteCrew change tracking
 */
function toggleTracking(event) {
    console.log('WriteCrew Commands: Toggle tracking requested');
    
    Word.run(async (context) => {
        try {
            // Get document properties to check tracking state
            const properties = context.document.properties;
            properties.load('customProperties');
            await context.sync();
            
            // Toggle tracking state
            let isTracking = false;
            try {
                const trackingProperty = properties.customProperties.getItem('WriteCrewTracking');
                trackingProperty.load('value');
                await context.sync();
                isTracking = trackingProperty.value === 'true';
            } catch (error) {
                // Property doesn't exist, create it
                properties.customProperties.add('WriteCrewTracking', 'false');
                await context.sync();
            }
            
            // Update tracking state
            const newTrackingState = !isTracking;
            properties.customProperties.getItem('WriteCrewTracking').value = newTrackingState.toString();
            await context.sync();
            
            // Add visual indicator
            const body = context.document.body;
            const statusText = newTrackingState ? 
                'WriteCrew tracking enabled' : 
                'WriteCrew tracking disabled';
            
            body.insertParagraph(statusText, Word.InsertLocation.start);
            await context.sync();
            
            console.log(`WriteCrew Commands: Tracking ${newTrackingState ? 'enabled' : 'disabled'}`);
            
        } catch (error) {
            console.error('WriteCrew Commands: Toggle tracking failed', error);
        }
        
        // Complete the event
        if (event) {
            event.completed();
        }
    });
}

/**
 * Open WriteCrew settings
 * Show settings dialog or pane
 */
function openSettings(event) {
    console.log('WriteCrew Commands: Open settings requested');
    
    // This would typically open a dialog or navigate to settings
    // For now, we'll just log the action
    
    try {
        // Could open a dialog here
        Office.context.ui.displayDialogAsync(
            'https://localhost:3000/settings.html',
            { height: 60, width: 60 },
            (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    console.log('WriteCrew Commands: Settings dialog opened');
                } else {
                    console.error('WriteCrew Commands: Failed to open settings dialog', result.error);
                }
            }
        );
    } catch (error) {
        console.error('WriteCrew Commands: Open settings failed', error);
    }
    
    // Complete the event
    if (event) {
        event.completed();
    }
}

/**
 * Export document with WriteCrew metadata
 * Export document including all WriteCrew changes and metadata
 */
function exportWithMetadata(event) {
    console.log('WriteCrew Commands: Export with metadata requested');
    
    Word.run(async (context) => {
        try {
            // Get document properties
            const properties = context.document.properties;
            properties.load(['title', 'author']);
            
            // Get all WriteCrew content controls
            const contentControls = context.document.contentControls;
            contentControls.load(['items']);
            await context.sync();
            
            // Collect WriteCrew metadata
            const writeCrewControls = [];
            for (const control of contentControls.items) {
                control.load(['tag', 'title', 'text']);
                await context.sync();
                
                if (control.tag && control.tag.startsWith('writecrew-')) {
                    writeCrewControls.push({
                        tag: control.tag,
                        title: control.title,
                        text: control.text.substring(0, 100) // First 100 chars
                    });
                }
            }
            
            // Create metadata summary
            const metadataSummary = `
WriteCrew Export Summary
========================
Document: ${properties.title || 'Untitled'}
Author: ${properties.author || 'Unknown'}
Export Date: ${new Date().toISOString()}
WriteCrew Elements: ${writeCrewControls.length}

WriteCrew Changes:
${writeCrewControls.map(control => `- ${control.title}: ${control.text}...`).join('\n')}
            `;
            
            // Insert metadata at end of document
            const body = context.document.body;
            body.insertBreak(Word.BreakType.page, Word.InsertLocation.end);
            body.insertText(metadataSummary, Word.InsertLocation.end);
            
            await context.sync();
            
            console.log('WriteCrew Commands: Export with metadata completed', {
                controlsFound: writeCrewControls.length
            });
            
        } catch (error) {
            console.error('WriteCrew Commands: Export with metadata failed', error);
        }
        
        // Complete the event
        if (event) {
            event.completed();
        }
    });
}

// Make functions available globally for Office.js
window.showTaskPane = showTaskPane;
window.quickAISuggestion = quickAISuggestion;
window.toggleTracking = toggleTracking;
window.openSettings = openSettings;
window.exportWithMetadata = exportWithMetadata;

