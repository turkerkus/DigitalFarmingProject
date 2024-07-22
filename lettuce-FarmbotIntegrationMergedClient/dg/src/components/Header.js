// src/components/Header.js
import '../styles/Header.css';
import React from 'react';
import { useNavigate } from 'react-router-dom';

const Header = ({ isLoggedIn }) => {
    const navigate = useNavigate();

    const handleLogout = () => {
        navigate('/');
    };


    return (
        <div className="Header">
            <header>
                <h1>Digital Farming Lettuce</h1>
                {isLoggedIn && (
                    <div className="header-buttons">
                        <button className="logout-button" onClick={handleLogout}>
                            <i className="fas fa-sign-out-alt"></i> Logout
                        </button>
                    </div>
                )}
            </header>
        </div>
    );
};

export default Header;