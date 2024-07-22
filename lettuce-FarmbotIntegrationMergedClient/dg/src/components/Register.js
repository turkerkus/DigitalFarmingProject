import React, { useState } from 'react';
import { registrationSchema } from './validationSchema';
import { useNavigate } from 'react-router-dom';

const Register = ({ onBack }) => {
    const [name, setName] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [errors, setErrors] = useState({});
    const navigate = useNavigate();
    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            await registrationSchema.validate({ name, password, confirmPassword }, { abortEarly: false });
            setErrors({});

            const socket = new WebSocket('ws://localhost:5000');

            socket.onopen = () => {
                socket.send(JSON.stringify({ action: 'register', name, password }));
            };

            socket.onmessage = (event) => {
                const result = JSON.parse(event.data);
                if (result.error) {
                    setErrors({ form: result.error });
                } else {
                    window.location.reload();
                }
            };

            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                setErrors({ form: 'Error during registration' });
            };
        } catch (err) {
            const validationErrors = {};
            err.inner.forEach(error => {
                validationErrors[error.path] = error.message;
            });
            setErrors(validationErrors);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <h2>Create a new account</h2>
            <label>Name:</label>
            <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
            />
            {errors.name && <p style={{ color: 'red' }}>{errors.name}</p>}
            <label>Password:</label>
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            {errors.password && <p style={{ color: 'red' }}>{errors.password}</p>}
            <label>Confirm password:</label>
            <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
            />
            {errors.confirmPassword && <p style={{ color: 'red' }}>{errors.confirmPassword}</p>}
            {errors.form && <p style={{ color: 'red' }}>{errors.form}</p>}
            <button type="submit">Create account</button>
            <button type="button" onClick={onBack}>Back</button>
        </form>
    );
};

export default Register;
