// Test script to simulate frontend session behavior
const https = require('https');

const API_BASE_URL = 'https://i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com/prod';

// Simulate a fake JWT token (this won't work for real auth, but we can test structure)
const fakeToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vLXVzZXItMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.fake';

async function testSessionFlow() {
    let activeSessionId = null;
    
    console.log('Testing session flow...');
    console.log('Initial activeSessionId:', activeSessionId);
    
    // First message
    const firstMessage = 'こんにちは';
    console.log('\n=== First Message ===');
    console.log('Sending message with sessionId:', activeSessionId);
    
    const firstRequestBody = JSON.stringify({
        message: firstMessage,
        sessionId: activeSessionId
    });
    
    console.log('Request body:', firstRequestBody);
    
    try {
        const firstResponse = await makeRequest(firstRequestBody, fakeToken);
        console.log('First response:', firstResponse);
        
        if (firstResponse.sessionId) {
            activeSessionId = firstResponse.sessionId;
            console.log('Saved sessionId from first response:', activeSessionId);
        }
        
        // Second message
        const secondMessage = 'ありがとう';
        console.log('\n=== Second Message ===');
        console.log('Sending message with sessionId:', activeSessionId);
        
        const secondRequestBody = JSON.stringify({
            message: secondMessage,
            sessionId: activeSessionId
        });
        
        console.log('Request body:', secondRequestBody);
        
        const secondResponse = await makeRequest(secondRequestBody, fakeToken);
        console.log('Second response:', secondResponse);
        
    } catch (error) {
        console.error('Test failed:', error.message);
    }
}

function makeRequest(body, token) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com',
            port: 443,
            path: '/prod/chat',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'Content-Length': Buffer.byteLength(body)
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(new Error(`Failed to parse response: ${data}`));
                }
            });
        });

        req.on('error', (e) => {
            reject(e);
        });

        req.write(body);
        req.end();
    });
}

// Run the test
testSessionFlow();