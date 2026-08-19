import { WebSocket } from 'ws';

const ws = new WebSocket('ws://localhost:8000/ws/general')
ws.on('open', () => {
    console.log('connected');
    ws.send('hello from client');
});
ws.on('message', (data: Buffer) => {
    console.log('received: ', data.toString());
    const jsonData = JSON.parse(data.toString());
    if (jsonData.type === 'history') {
        console.log(jsonData.messages);
    } else {
        console.log(jsonData.text);
    }
})