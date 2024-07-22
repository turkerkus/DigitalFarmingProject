import React, { useEffect, useState } from 'react';

const WebSocketComponent = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [socket, setSocket] = useState(null);

    useEffect(() => {
        const newSocket = new WebSocket('ws://localhost:5000');
        setSocket(newSocket);

        newSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setMessages((prevMessages) => [...prevMessages, data]);
        };

        newSocket.onclose = () => {
            console.log('WebSocket connection closed');
        };

        newSocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return () => {
            newSocket.close();
        };
    }, []);

    const sendMessage = () => {
        if (socket) {
            socket.send(JSON.stringify({ action: 'send-message', content: input }));
            setInput('');
        }
    };

    return (
        <div>
            <h3>WebSocket Messages</h3>
            <ul>
                {messages.map((message, index) => (
                    <li key={index}>{message.content}</li>
                ))}
            </ul>
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message"
            />
            <button onClick={sendMessage}>Send</button>
        </div>
    );
};

export default WebSocketComponent;
