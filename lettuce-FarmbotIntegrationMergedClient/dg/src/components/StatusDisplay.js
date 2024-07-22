import React, { useState, useEffect } from 'react';

const StatusDisplay = () => {
  const [status, setStatus] = useState('offline');
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Establish a WebSocket connection
    const socket = new WebSocket('ws://localhost:5000');
    setSocket(socket);

    socket.onopen = () => {
      // Request status update when connection is established
      socket.send(JSON.stringify({ action: 'get-status' }));
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.status) {
        setStatus(data.status);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error: ', error);
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed');
      setStatus('offline');
    };

    // Clean up the WebSocket connection on component unmount
    return () => {
      socket.close();
    };
  }, []);

  return (
      <div className={`status-display ${status === 'active' ? 'active' : 'offline'}`}>
        <label>FarmBot Status: </label>
        <span className="status">{status}</span>
      </div>
  );
};

export default StatusDisplay;
