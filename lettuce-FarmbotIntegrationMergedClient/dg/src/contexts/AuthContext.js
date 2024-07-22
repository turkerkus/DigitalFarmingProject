// src/contexts/AuthContext.js
import React, { createContext, useState } from 'react';

// Create the context
export const AuthContext = createContext();

// Create the provider component
export const AuthProvider = ({ children }) => {
    const [user_id, setUserId] = useState(null);
    const [name, setName] = useState(null);

    return (
        <AuthContext.Provider value={{ user_id, setUserId, name, setName }}>
            {children}
        </AuthContext.Provider>
    );
};
