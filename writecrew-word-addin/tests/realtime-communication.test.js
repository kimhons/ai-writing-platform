/**
 * Comprehensive Testing Framework for Real-time Communication Service
 * Includes unit tests, integration tests, WebSocket mocking, and performance tests
 */

// Mock browser APIs for Node.js environment
global.localStorage = {
    getItem: (key) => {
        if (key === 'writecrew_auth_token') return 'mock_auth_token_12345';
        return null;
    },
    setItem: (key, value) => {},
    removeItem: (key) => {},
    clear: () => {}
};

// Test dependencies
const RealtimeCommunicationService = require('../src/services/realtime-communication');

// Mock WebSocket for testing
class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = MockWebSocket.CONNECTING;
        this.onopen = null;
        this.onmessage = null;
        this.onclose = null;
        this.onerror = null;
        
        // Simulate connection delay
        setTimeout(() => {
            this.readyState = MockWebSocket.OPEN;
            if (this.onopen) {
                this.onopen({ type: 'open' });
            }
        }, 100);
    }
    
    send(data) {
        if (this.readyState !== MockWebSocket.OPEN) {
            throw new Error('WebSocket is not open');
        }
        
        // Store sent messages for verification
        if (!this.sentMessages) {
            this.sentMessages = [];
        }
        this.sentMessages.push(data);
        
        // Simulate message echo for testing
        setTimeout(() => {
            if (this.onmessage) {
                const message = JSON.parse(data);
                
                // Simulate heartbeat response
                if (message.type === 'heartbeat') {
                    this.onmessage({
                        data: JSON.stringify({
                            type: 'heartbeat_response',
                            timestamp: Date.now()
                        })
                    });
                }
                
                // Simulate other responses
                if (message.type !== 'heartbeat') {
                    this.onmessage({
                        data: JSON.stringify({
                            type: 'response',
                            responseToId: message.id,
                            data: { success: true, echo: message }
                        })
                    });
                }
            }
        }, 50);
    }
    
    close(code = 1000, reason = '') {
        this.readyState = MockWebSocket.CLOSED;
        if (this.onclose) {
            this.onclose({ code, reason, type: 'close' });
        }
    }
    
    simulateError(error) {
        if (this.onerror) {
            this.onerror(error);
        }
    }
    
    simulateMessage(message) {
        if (this.onmessage) {
            this.onmessage({
                data: JSON.stringify(message)
            });
        }
    }
    
    static get CONNECTING() { return 0; }
    static get OPEN() { return 1; }
    static get CLOSING() { return 2; }
    static get CLOSED() { return 3; }
}

// Test Suite
class RealtimeCommunicationTestSuite {
    constructor() {
        this.tests = [];
        this.results = {
            passed: 0,
            failed: 0,
            total: 0,
            errors: []
        };
        
        // Mock global WebSocket
        global.WebSocket = MockWebSocket;
        
        this.setupTests();
    }
    
    setupTests() {
        // Unit Tests
        this.addTest('Connection Management', this.testConnectionManagement.bind(this));
        this.addTest('Message Sending', this.testMessageSending.bind(this));
        this.addTest('Message Receiving', this.testMessageReceiving.bind(this));
        this.addTest('Heartbeat System', this.testHeartbeatSystem.bind(this));
        this.addTest('Reconnection Logic', this.testReconnectionLogic.bind(this));
        this.addTest('Message Queue', this.testMessageQueue.bind(this));
        this.addTest('Event Emitter', this.testEventEmitter.bind(this));
        this.addTest('Connection Quality', this.testConnectionQuality.bind(this));
        
        // Integration Tests
        this.addTest('End-to-End Communication', this.testEndToEndCommunication.bind(this));
        this.addTest('Error Recovery', this.testErrorRecovery.bind(this));
        this.addTest('Performance Under Load', this.testPerformanceUnderLoad.bind(this));
        this.addTest('Concurrent Connections', this.testConcurrentConnections.bind(this));
        
        // Edge Cases
        this.addTest('Network Interruption', this.testNetworkInterruption.bind(this));
        this.addTest('Invalid Messages', this.testInvalidMessages.bind(this));
        this.addTest('Memory Leaks', this.testMemoryLeaks.bind(this));
        this.addTest('Cleanup and Destruction', this.testCleanupAndDestruction.bind(this));
    }
    
    addTest(name, testFunction) {
        this.tests.push({ name, testFunction });
    }
    
    async runAllTests() {
        console.log('🧪 Starting Real-time Communication Service Test Suite...\n');
        
        for (const test of this.tests) {
            await this.runTest(test);
        }
        
        this.printResults();
        return this.results;
    }
    
    async runTest(test) {
        console.log(`🔬 Running: ${test.name}`);
        
        try {
            await test.testFunction();
            this.results.passed++;
            console.log(`✅ PASSED: ${test.name}\n`);
        } catch (error) {
            this.results.failed++;
            this.results.errors.push({ test: test.name, error: error.message });
            console.log(`❌ FAILED: ${test.name}`);
            console.log(`   Error: ${error.message}\n`);
        }
        
        this.results.total++;
    }
    
    // Unit Tests
    async testConnectionManagement() {
        const service = new RealtimeCommunicationService({
            baseUrl: 'ws://localhost:8000',
            reconnectAttempts: 3
        });
        
        // Test initial state
        this.assert(service.connectionState === 'disconnected', 'Initial state should be disconnected');
        
        // Test connection
        await service.connect();
        this.assert(service.connectionState === 'connected', 'Should be connected after connect()');
        
        // Test disconnection
        service.disconnect();
        this.assert(service.connectionState === 'disconnected', 'Should be disconnected after disconnect()');
        
        service.destroy();
    }
    
    async testMessageSending() {
        const service = new RealtimeCommunicationService();
        await service.connect();
        
        // Test basic message sending
        await service.sendMessage('test_message', { content: 'Hello World' });
        
        // Verify message was sent
        const websocket = service.websocket;
        this.assert(websocket.sentMessages.length > 0, 'Message should be sent');
        
        const sentMessage = JSON.parse(websocket.sentMessages[websocket.sentMessages.length - 1]);
        this.assert(sentMessage.type === 'test_message', 'Message type should match');
        this.assert(sentMessage.data.content === 'Hello World', 'Message data should match');
        
        service.destroy();
    }
    
    async testMessageReceiving() {
        const service = new RealtimeCommunicationService();
        await service.connect();
        
        let receivedMessage = null;
        
        // Register message handler
        service.onMessage('test_response', (data) => {
            receivedMessage = data;
        });
        
        // Simulate incoming message
        service.websocket.simulateMessage({
            type: 'test_response',
            data: { result: 'success' }
        });
        
        // Wait for message processing
        await this.delay(100);
        
        this.assert(receivedMessage !== null, 'Message should be received');
        this.assert(receivedMessage.result === 'success', 'Message data should match');
        
        service.destroy();
    }
    
    async testHeartbeatSystem() {
        const service = new RealtimeCommunicationService({
            heartbeatInterval: 500 // 500ms for testing
        });
        
        await service.connect();
        
        // Wait for heartbeat
        await this.delay(600);
        
        // Check if heartbeat was sent
        const websocket = service.websocket;
        const heartbeatMessage = websocket.sentMessages.find(msg => {
            const parsed = JSON.parse(msg);
            return parsed.type === 'heartbeat';
        });
        
        this.assert(heartbeatMessage !== undefined, 'Heartbeat should be sent');
        
        service.destroy();
    }
    
    async testReconnectionLogic() {
        const service = new RealtimeCommunicationService({
            reconnectAttempts: 2,
            reconnectDelay: 100
        });
        
        await service.connect();
        
        let reconnectionAttempted = false;
        service.on('connectionStateChanged', (data) => {
            if (data.state === 'reconnecting') {
                reconnectionAttempted = true;
            }
        });
        
        // Simulate connection loss
        service.websocket.close(1006, 'Connection lost');
        
        // Wait for reconnection attempt
        await this.delay(200);
        
        this.assert(reconnectionAttempted, 'Reconnection should be attempted');
        
        service.destroy();
    }
    
    async testMessageQueue() {
        const service = new RealtimeCommunicationService();
        
        // Send message while disconnected
        service.sendMessage('queued_message', { test: true });
        
        this.assert(service.messageQueue.length === 1, 'Message should be queued');
        
        // Connect and verify message is sent
        await service.connect();
        await this.delay(100);
        
        this.assert(service.messageQueue.length === 0, 'Queue should be empty after connection');
        
        service.destroy();
    }
    
    async testEventEmitter() {
        const service = new RealtimeCommunicationService();
        
        let eventReceived = false;
        let eventData = null;
        
        // Register event listener
        const unsubscribe = service.on('test_event', (data) => {
            eventReceived = true;
            eventData = data;
        });
        
        // Emit event
        service.emit('test_event', { message: 'test' });
        
        this.assert(eventReceived, 'Event should be received');
        this.assert(eventData.message === 'test', 'Event data should match');
        
        // Test unsubscribe
        unsubscribe();
        eventReceived = false;
        service.emit('test_event', { message: 'test2' });
        
        this.assert(!eventReceived, 'Event should not be received after unsubscribe');
        
        service.destroy();
    }
    
    async testConnectionQuality() {
        const service = new RealtimeCommunicationService();
        await service.connect();
        
        // Simulate low latency
        service.updateLatencyMetrics(50);
        this.assert(service.connectionQuality.status === 'excellent', 'Should be excellent quality');
        
        // Simulate high latency
        service.updateLatencyMetrics(2000);
        this.assert(service.connectionQuality.status === 'poor', 'Should be poor quality');
        
        service.destroy();
    }
    
    // Integration Tests
    async testEndToEndCommunication() {
        const service = new RealtimeCommunicationService();
        await service.connect();
        
        // Test high-level API
        const response = await service.requestAgentAction('test_agent', 'test_action', { param: 'value' });
        
        this.assert(response.success === true, 'Should receive successful response');
        this.assert(response.echo.data.agentId === 'test_agent', 'Response should contain original data');
        
        service.destroy();
    }
    
    async testErrorRecovery() {
        const service = new RealtimeCommunicationService({
            reconnectAttempts: 1,
            reconnectDelay: 100
        });
        
        await service.connect();
        
        let errorHandled = false;
        service.on('connectionError', () => {
            errorHandled = true;
        });
        
        // Simulate error
        service.websocket.simulateError(new Error('Test error'));
        
        await this.delay(50);
        
        this.assert(errorHandled, 'Error should be handled');
        
        service.destroy();
    }
    
    async testPerformanceUnderLoad() {
        const service = new RealtimeCommunicationService();
        await service.connect();
        
        const startTime = Date.now();
        const messageCount = 100;
        const promises = [];
        
        // Send multiple messages concurrently
        for (let i = 0; i < messageCount; i++) {
            promises.push(service.sendMessage('load_test', { index: i }));
        }
        
        await Promise.all(promises);
        
        const endTime = Date.now();
        const duration = endTime - startTime;
        const messagesPerSecond = (messageCount / duration) * 1000;
        
        console.log(`   Performance: ${messagesPerSecond.toFixed(2)} messages/second`);
        
        this.assert(messagesPerSecond > 10, 'Should handle at least 10 messages per second');
        
        service.destroy();
    }
    
    async testConcurrentConnections() {
        const services = [];
        
        // Create multiple service instances
        for (let i = 0; i < 5; i++) {
            const service = new RealtimeCommunicationService();
            services.push(service);
        }
        
        // Connect all services
        await Promise.all(services.map(service => service.connect()));
        
        // Verify all are connected
        services.forEach((service, index) => {
            this.assert(service.connectionState === 'connected', `Service ${index} should be connected`);
        });
        
        // Cleanup
        services.forEach(service => service.destroy());
    }
    
    // Edge Case Tests
    async testNetworkInterruption() {
        const service = new RealtimeCommunicationService({
            reconnectAttempts: 1,
            reconnectDelay: 100
        });
        
        await service.connect();
        
        // Send message during connection
        const messagePromise = service.sendMessage('test', { data: 'test' }, { expectResponse: true });
        
        // Simulate network interruption
        setTimeout(() => {
            service.websocket.close(1006, 'Network error');
        }, 50);
        
        try {
            await messagePromise;
            this.assert(false, 'Message should fail due to network interruption');
        } catch (error) {
            this.assert(error.message.includes('timeout') || error.message.includes('Network'), 'Should handle network interruption');
        }
        
        service.destroy();
    }
    
    async testInvalidMessages() {
        const service = new RealtimeCommunicationService();
        await service.connect();
        
        let errorCount = 0;
        const originalConsoleError = console.error;
        console.error = () => errorCount++;
        
        // Send invalid JSON
        service.websocket.simulateMessage('invalid json');
        
        // Send message with missing fields
        service.websocket.simulateMessage({});
        
        await this.delay(100);
        
        console.error = originalConsoleError;
        
        this.assert(errorCount > 0, 'Should handle invalid messages gracefully');
        
        service.destroy();
    }
    
    async testMemoryLeaks() {
        const service = new RealtimeCommunicationService();
        
        // Add many event listeners
        for (let i = 0; i < 1000; i++) {
            service.on('test_event', () => {});
        }
        
        // Add many message handlers
        for (let i = 0; i < 1000; i++) {
            service.onMessage('test_message', () => {});
        }
        
        const initialListeners = service.eventListeners.get('test_event').length;
        const initialHandlers = service.messageHandlers.get('test_message').length;
        
        this.assert(initialListeners === 1000, 'Should have 1000 event listeners');
        this.assert(initialHandlers === 1000, 'Should have 1000 message handlers');
        
        // Cleanup
        service.destroy();
        
        // Verify cleanup
        this.assert(service.eventListeners.size === 0, 'Event listeners should be cleared');
        this.assert(service.messageHandlers.size === 0, 'Message handlers should be cleared');
    }
    
    async testCleanupAndDestruction() {
        const service = new RealtimeCommunicationService();
        await service.connect();
        
        // Add some pending messages
        service.sendMessage('test', {}, { expectResponse: true }).catch(() => {});
        
        // Add some queued messages
        service.messageQueue.push({ type: 'test' });
        
        this.assert(service.pendingMessages.size > 0, 'Should have pending messages');
        this.assert(service.messageQueue.length > 0, 'Should have queued messages');
        
        // Destroy service
        service.destroy();
        
        // Verify cleanup
        this.assert(service.connectionState === 'disconnected', 'Should be disconnected');
        this.assert(service.pendingMessages.size === 0, 'Pending messages should be cleared');
        this.assert(service.messageQueue.length === 0, 'Message queue should be cleared');
        this.assert(service.websocket === null || service.websocket.readyState === MockWebSocket.CLOSED, 'WebSocket should be closed');
    }
    
    // Utility Methods
    assert(condition, message) {
        if (!condition) {
            throw new Error(message);
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    printResults() {
        console.log('\n📊 Test Results:');
        console.log(`✅ Passed: ${this.results.passed}`);
        console.log(`❌ Failed: ${this.results.failed}`);
        console.log(`📈 Total: ${this.results.total}`);
        console.log(`🎯 Success Rate: ${((this.results.passed / this.results.total) * 100).toFixed(1)}%`);
        
        if (this.results.errors.length > 0) {
            console.log('\n❌ Failed Tests:');
            this.results.errors.forEach(error => {
                console.log(`   ${error.test}: ${error.error}`);
            });
        }
        
        console.log('\n🏁 Test Suite Complete!');
    }
}

// Performance Benchmark Suite
class PerformanceBenchmarkSuite {
    constructor() {
        this.benchmarks = [];
        this.results = [];
    }
    
    addBenchmark(name, benchmarkFunction) {
        this.benchmarks.push({ name, benchmarkFunction });
    }
    
    async runBenchmarks() {
        console.log('⚡ Starting Performance Benchmarks...\n');
        
        for (const benchmark of this.benchmarks) {
            await this.runBenchmark(benchmark);
        }
        
        this.printBenchmarkResults();
    }
    
    async runBenchmark(benchmark) {
        console.log(`⚡ Running: ${benchmark.name}`);
        
        const startTime = performance.now();
        const result = await benchmark.benchmarkFunction();
        const endTime = performance.now();
        
        const duration = endTime - startTime;
        
        this.results.push({
            name: benchmark.name,
            duration,
            result
        });
        
        console.log(`   Duration: ${duration.toFixed(2)}ms`);
        if (result.throughput) {
            console.log(`   Throughput: ${result.throughput.toFixed(2)} ops/sec`);
        }
        console.log();
    }
    
    printBenchmarkResults() {
        console.log('📊 Benchmark Results:');
        this.results.forEach(result => {
            console.log(`   ${result.name}: ${result.duration.toFixed(2)}ms`);
        });
    }
}

// Test Runner
class TestRunner {
    static async runAllTests() {
        console.log('🚀 WriteCrew Real-time Communication Service Test Runner\n');
        
        // Run unit and integration tests
        const testSuite = new RealtimeCommunicationTestSuite();
        const testResults = await testSuite.runAllTests();
        
        // Run performance benchmarks
        const benchmarkSuite = new PerformanceBenchmarkSuite();
        
        benchmarkSuite.addBenchmark('Connection Speed', async () => {
            const service = new RealtimeCommunicationService();
            const startTime = performance.now();
            await service.connect();
            const endTime = performance.now();
            service.destroy();
            return { connectionTime: endTime - startTime };
        });
        
        benchmarkSuite.addBenchmark('Message Throughput', async () => {
            const service = new RealtimeCommunicationService();
            await service.connect();
            
            const messageCount = 1000;
            const startTime = performance.now();
            
            const promises = [];
            for (let i = 0; i < messageCount; i++) {
                promises.push(service.sendMessage('benchmark', { index: i }));
            }
            
            await Promise.all(promises);
            const endTime = performance.now();
            
            service.destroy();
            
            const duration = endTime - startTime;
            const throughput = (messageCount / duration) * 1000;
            
            return { throughput };
        });
        
        benchmarkSuite.addBenchmark('Memory Usage', async () => {
            const service = new RealtimeCommunicationService();
            await service.connect();
            
            const initialMemory = process.memoryUsage ? process.memoryUsage().heapUsed : 0;
            
            // Create load
            for (let i = 0; i < 10000; i++) {
                service.sendMessage('memory_test', { data: 'x'.repeat(100) });
            }
            
            const finalMemory = process.memoryUsage ? process.memoryUsage().heapUsed : 0;
            const memoryIncrease = finalMemory - initialMemory;
            
            service.destroy();
            
            return { memoryIncrease: memoryIncrease / 1024 / 1024 }; // MB
        });
        
        await benchmarkSuite.runBenchmarks();
        
        return {
            tests: testResults,
            benchmarks: benchmarkSuite.results
        };
    }
}

// Export test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        TestRunner,
        RealtimeCommunicationTestSuite,
        PerformanceBenchmarkSuite,
        MockWebSocket
    };
} else {
    window.RealtimeCommunicationTestRunner = TestRunner;
}

// Auto-run tests if this file is executed directly
if (typeof require !== 'undefined' && require.main === module) {
    TestRunner.runAllTests().then(results => {
        const success = results.tests.failed === 0;
        process.exit(success ? 0 : 1);
    });
}

