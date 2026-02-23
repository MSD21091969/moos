import { WebSocket } from 'ws';

// The user is authenticated as 'Sam' on the frontend
const WS_URL = 'ws://localhost:18789?token=mock_token';

console.log(`Connecting to ${WS_URL}...`);
const ws = new WebSocket(WS_URL);

ws.on('open', () => {
    console.log('Connected to WebSocket!');

    // We need a session first. Since we don't have a real sessionId from AgentRunner,
    const msg = {
        type: 'request',
        id: 'msg-1',
        method: 'agent.request',
        params: {
            sessionKey: 'test-session-123',
            message: 'Hello agent, are you there?'
        }
    };

    console.log('Sending message:', msg);
    ws.send(JSON.stringify(msg));
});

ws.on('message', (data) => {
    console.log('Received message:', data.toString());
});

ws.on('error', (err) => {
    console.error('WebSocket Error:', err.message);
});

ws.on('close', (code, reason) => {
    console.log(`Connection closed: ${code} ${reason.toString()}`);
    process.exit(0);
});

// Timeout after 10 seconds
setTimeout(() => {
    console.log('Test timed out after 10 seconds');
    ws.close();
    process.exit(1);
}, 10000);
