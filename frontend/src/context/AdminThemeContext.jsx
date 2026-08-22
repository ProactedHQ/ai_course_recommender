import React, { createContext, useContext, useState, useEffect } from 'react';

const AdminThemeContext = createContext();

export const useAdminTheme = () => {
    const context = useContext(AdminThemeContext);
    if (!context) {
        throw new Error('useAdminTheme must be used within an AdminThemeProvider');
    }
    return context;
};

export const AdminThemeProvider = ({ children }) => {
    // Default theme is 'blue-dark'
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('admin-theme') || 'blue-dark';
    });

    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
        return localStorage.getItem('admin-sidebar-collapsed') === 'true';
    });

    useEffect(() => {
        // Apply theme to the root element or a specific shell container
        document.documentElement.setAttribute('data-admin-theme', theme);
        localStorage.setItem('admin-theme', theme);
    }, [theme]);

    useEffect(() => {
        localStorage.setItem('admin-sidebar-collapsed', isSidebarCollapsed);
    }, [isSidebarCollapsed]);

    const toggleTheme = () => {
        setTheme(prev => {
            if (prev === 'blue-dark') return 'midnight';
            if (prev === 'midnight') return 'light';
            return 'blue-dark';
        });
    };

    const toggleSidebar = () => {
        setIsSidebarCollapsed(prev => !prev);
    };

    return (
        <AdminThemeContext.Provider value={{
            theme,
            setTheme,
            toggleTheme,
            isSidebarCollapsed,
            toggleSidebar
        }}>
            {children}
        </AdminThemeContext.Provider>
    );
};
