import React, { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Login.css';
import Register from './Register';
import '../styles/Register.css';
import { AuthContext } from '../contexts/AuthContext';
import Header from "./Header";

const Login = () => {
  const { setUserId } = useContext(AuthContext);
  const { setName } = useContext(AuthContext);

  useEffect(() => {
    document.title = 'Digital Farming Login';
  }, []);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const [register, setRegister] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const socket = new WebSocket('ws://localhost:5000');

    socket.onopen = () => {
      socket.send(JSON.stringify({ action: 'authenticate', username, password }));
    };

    socket.onmessage = (event) => {
      const result = JSON.parse(event.data);

      if (result.authenticated) {
        setUserId(result.user_id);
        setName(result.name);
        navigate('/dashboard');
      } else {
        alert('Invalid credentials');
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      alert('Error during authentication');
    };
  };

  return (
      <>
        <Header />
        <div className="login-container">
          {register ? (
              <Register onBack={() => setRegister(false)} />
          ) : (
              <form onSubmit={handleSubmit}>
                <h2>Login</h2>
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                <button type="submit">Login</button>
                <button type="button" onClick={() => setRegister(true)}>Register</button>
              </form>
          )}
        </div>
      </>
  );
};

export default Login;
