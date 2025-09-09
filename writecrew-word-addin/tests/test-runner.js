/**
 * WriteCrew Test Runner
 * Comprehensive testing framework for all WriteCrew Word Add-in components
 */

// Import test suites
const { TestRunner: RealtimeTestRunner } = require('./realtime-communication.test');

class WritCrewTestRunner {
    constructor() {
        this.testSuites = [];
        this.results = {
            totalTests: 0,
            totalPassed: 0,
            totalFailed: 0,
            suiteResults: [],
            startTime: null,
            endTime: null,
            duration: 0
        };
        
        this.setupTestSuites();
    }
    
    setupTestSuites() {
        // Add all test suites
        this.addTestSuite('Real-time Communication', RealtimeTestRunner);
        
        // Add more test suites as they are created
        // this.addTestSuite('Agent Card Component', AgentCardTestRunner);
        // this.addTestSuite('Chat Interface', ChatInterfaceTestRunner);
        // this.addTestSuite('Suggestions Panel', SuggestionsPanelTestRunner);
        // this.addTestSuite('Main Controller', MainControllerTestRunner);
    }
    
    addTestSuite(name, testRunner) {
        this.testSuites.push({ name, testRunner });
    }
    
    async runAllTests() {
        console.log('🚀 WriteCrew Comprehensive Test Suite');
        console.log('=====================================\n');
        
        this.results.startTime = Date.now();
        
        for (const suite of this.testSuites) {
            await this.runTestSuite(suite);
        }
        
        this.results.endTime = Date.now();
        this.results.duration = this.results.endTime - this.results.startTime;
        
        this.printFinalResults();
        
        return this.results;
    }
    
    async runTestSuite(suite) {
        console.log(`📦 Running Test Suite: ${suite.name}`);
        console.log('─'.repeat(50));
        
        try {
            const suiteResults = await suite.testRunner.runAllTests();
            
            this.results.suiteResults.push({
                name: suite.name,
                ...suiteResults
            });
            
            this.results.totalTests += suiteResults.tests.total;
            this.results.totalPassed += suiteResults.tests.passed;
            this.results.totalFailed += suiteResults.tests.failed;
            
            console.log(`✅ ${suite.name} Complete: ${suiteResults.tests.passed}/${suiteResults.tests.total} passed\n`);
            
        } catch (error) {
            console.error(`❌ ${suite.name} Failed: ${error.message}\n`);
            this.results.totalFailed++;
        }
    }
    
    printFinalResults() {
        console.log('\n🏁 FINAL TEST RESULTS');
        console.log('=====================');
        console.log(`⏱️  Duration: ${this.results.duration}ms`);
        console.log(`📊 Total Tests: ${this.results.totalTests}`);
        console.log(`✅ Passed: ${this.results.totalPassed}`);
        console.log(`❌ Failed: ${this.results.totalFailed}`);
        console.log(`🎯 Success Rate: ${((this.results.totalPassed / this.results.totalTests) * 100).toFixed(1)}%`);
        
        console.log('\n📦 Suite Breakdown:');
        this.results.suiteResults.forEach(suite => {
            const successRate = ((suite.tests.passed / suite.tests.total) * 100).toFixed(1);
            console.log(`   ${suite.name}: ${suite.tests.passed}/${suite.tests.total} (${successRate}%)`);
        });
        
        if (this.results.totalFailed === 0) {
            console.log('\n🎉 ALL TESTS PASSED! WriteCrew is ready for production.');
        } else {
            console.log('\n⚠️  Some tests failed. Please review and fix before deployment.');
        }
    }
}

// Continuous Integration Test Runner
class CITestRunner extends WritCrewTestRunner {
    constructor() {
        super();
        this.ciConfig = {
            failFast: process.env.CI_FAIL_FAST === 'true',
            verbose: process.env.CI_VERBOSE === 'true',
            coverage: process.env.CI_COVERAGE === 'true',
            timeout: parseInt(process.env.CI_TIMEOUT) || 300000 // 5 minutes
        };
    }
    
    async runCITests() {
        console.log('🤖 Running WriteCrew CI Test Suite');
        console.log(`   Fail Fast: ${this.ciConfig.failFast}`);
        console.log(`   Verbose: ${this.ciConfig.verbose}`);
        console.log(`   Coverage: ${this.ciConfig.coverage}`);
        console.log(`   Timeout: ${this.ciConfig.timeout}ms\n`);
        
        // Set timeout for entire test suite
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => {
                reject(new Error(`Test suite timeout after ${this.ciConfig.timeout}ms`));
            }, this.ciConfig.timeout);
        });
        
        try {
            const results = await Promise.race([
                this.runAllTests(),
                timeoutPromise
            ]);
            
            // Generate CI reports
            this.generateCIReports(results);
            
            // Exit with appropriate code
            const success = results.totalFailed === 0;
            process.exit(success ? 0 : 1);
            
        } catch (error) {
            console.error('❌ CI Test Suite Failed:', error.message);
            process.exit(1);
        }
    }
    
    generateCIReports(results) {
        // Generate JUnit XML report for CI systems
        const junitXml = this.generateJUnitXML(results);
        
        // Write to file if in CI environment
        if (process.env.CI) {
            const fs = require('fs');
            fs.writeFileSync('test-results.xml', junitXml);
            console.log('📄 JUnit XML report generated: test-results.xml');
        }
        
        // Generate coverage report if enabled
        if (this.ciConfig.coverage) {
            this.generateCoverageReport(results);
        }
    }
    
    generateJUnitXML(results) {
        let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
        xml += `<testsuites tests="${results.totalTests}" failures="${results.totalFailed}" time="${results.duration / 1000}">\n`;
        
        results.suiteResults.forEach(suite => {
            xml += `  <testsuite name="${suite.name}" tests="${suite.tests.total}" failures="${suite.tests.failed}" time="${suite.duration || 0}">\n`;
            
            // Add individual test cases (simplified)
            for (let i = 0; i < suite.tests.passed; i++) {
                xml += `    <testcase name="Test ${i + 1}" classname="${suite.name}"/>\n`;
            }
            
            suite.tests.errors?.forEach(error => {
                xml += `    <testcase name="${error.test}" classname="${suite.name}">\n`;
                xml += `      <failure message="${error.error}"/>\n`;
                xml += `    </testcase>\n`;
            });
            
            xml += '  </testsuite>\n';
        });
        
        xml += '</testsuites>';
        return xml;
    }
    
    generateCoverageReport(results) {
        console.log('📊 Coverage report generation not implemented yet');
        // TODO: Implement code coverage reporting
    }
}

// Performance Test Runner
class PerformanceTestRunner {
    constructor() {
        this.performanceTests = [];
        this.results = [];
    }
    
    addPerformanceTest(name, testFunction, options = {}) {
        this.performanceTests.push({
            name,
            testFunction,
            iterations: options.iterations || 100,
            warmup: options.warmup || 10,
            timeout: options.timeout || 30000
        });
    }
    
    async runPerformanceTests() {
        console.log('⚡ Running Performance Tests...\n');
        
        for (const test of this.performanceTests) {
            await this.runPerformanceTest(test);
        }
        
        this.printPerformanceResults();
        return this.results;
    }
    
    async runPerformanceTest(test) {
        console.log(`⚡ ${test.name}`);
        
        // Warmup
        for (let i = 0; i < test.warmup; i++) {
            await test.testFunction();
        }
        
        // Actual test
        const times = [];
        const startTime = performance.now();
        
        for (let i = 0; i < test.iterations; i++) {
            const iterationStart = performance.now();
            await test.testFunction();
            const iterationEnd = performance.now();
            times.push(iterationEnd - iterationStart);
        }
        
        const endTime = performance.now();
        
        // Calculate statistics
        const totalTime = endTime - startTime;
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const minTime = Math.min(...times);
        const maxTime = Math.max(...times);
        const throughput = (test.iterations / totalTime) * 1000;
        
        const result = {
            name: test.name,
            iterations: test.iterations,
            totalTime,
            avgTime,
            minTime,
            maxTime,
            throughput
        };
        
        this.results.push(result);
        
        console.log(`   Avg: ${avgTime.toFixed(2)}ms`);
        console.log(`   Min: ${minTime.toFixed(2)}ms`);
        console.log(`   Max: ${maxTime.toFixed(2)}ms`);
        console.log(`   Throughput: ${throughput.toFixed(2)} ops/sec\n`);
    }
    
    printPerformanceResults() {
        console.log('📊 Performance Test Summary:');
        this.results.forEach(result => {
            console.log(`   ${result.name}: ${result.avgTime.toFixed(2)}ms avg, ${result.throughput.toFixed(2)} ops/sec`);
        });
    }
}

// Memory Leak Test Runner
class MemoryLeakTestRunner {
    constructor() {
        this.memoryTests = [];
        this.results = [];
    }
    
    addMemoryTest(name, testFunction, options = {}) {
        this.memoryTests.push({
            name,
            testFunction,
            iterations: options.iterations || 1000,
            threshold: options.threshold || 10 // MB
        });
    }
    
    async runMemoryTests() {
        console.log('🧠 Running Memory Leak Tests...\n');
        
        for (const test of this.memoryTests) {
            await this.runMemoryTest(test);
        }
        
        this.printMemoryResults();
        return this.results;
    }
    
    async runMemoryTest(test) {
        console.log(`🧠 ${test.name}`);
        
        // Force garbage collection if available
        if (global.gc) {
            global.gc();
        }
        
        const initialMemory = process.memoryUsage().heapUsed;
        
        // Run test iterations
        for (let i = 0; i < test.iterations; i++) {
            await test.testFunction();
            
            // Periodic garbage collection
            if (i % 100 === 0 && global.gc) {
                global.gc();
            }
        }
        
        // Force final garbage collection
        if (global.gc) {
            global.gc();
        }
        
        const finalMemory = process.memoryUsage().heapUsed;
        const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024; // MB
        
        const result = {
            name: test.name,
            iterations: test.iterations,
            initialMemory: initialMemory / 1024 / 1024,
            finalMemory: finalMemory / 1024 / 1024,
            memoryIncrease,
            threshold: test.threshold,
            passed: memoryIncrease <= test.threshold
        };
        
        this.results.push(result);
        
        console.log(`   Initial: ${result.initialMemory.toFixed(2)}MB`);
        console.log(`   Final: ${result.finalMemory.toFixed(2)}MB`);
        console.log(`   Increase: ${memoryIncrease.toFixed(2)}MB`);
        console.log(`   Threshold: ${test.threshold}MB`);
        console.log(`   Status: ${result.passed ? '✅ PASSED' : '❌ FAILED'}\n`);
    }
    
    printMemoryResults() {
        console.log('📊 Memory Test Summary:');
        const passed = this.results.filter(r => r.passed).length;
        const total = this.results.length;
        
        console.log(`   Passed: ${passed}/${total}`);
        
        this.results.forEach(result => {
            const status = result.passed ? '✅' : '❌';
            console.log(`   ${status} ${result.name}: ${result.memoryIncrease.toFixed(2)}MB increase`);
        });
    }
}

// Main Test Runner Export
module.exports = {
    WritCrewTestRunner,
    CITestRunner,
    PerformanceTestRunner,
    MemoryLeakTestRunner
};

// CLI execution
if (require.main === module) {
    const args = process.argv.slice(2);
    const command = args[0] || 'test';
    
    switch (command) {
        case 'test':
            new WritCrewTestRunner().runAllTests();
            break;
        case 'ci':
            new CITestRunner().runCITests();
            break;
        case 'performance':
            new PerformanceTestRunner().runPerformanceTests();
            break;
        case 'memory':
            new MemoryLeakTestRunner().runMemoryTests();
            break;
        default:
            console.log('Usage: node test-runner.js [test|ci|performance|memory]');
            process.exit(1);
    }
}

