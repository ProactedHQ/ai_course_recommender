import React from 'react';
import { Sun, Moon, Palette } from 'lucide-react';
import { useAdminTheme } from '../../context/AdminThemeContext';

const ThemeSwitcher = () => {
    const { theme, toggleTheme } = useAdminTheme();

    const getIcon = () => {
        if (theme === 'light') return <Sun size={18} />;
        if (theme === 'midnight') return <Palette size={18} />;
        return <Moon size={18} />;
    };

    const getLabel = () => {
        if (theme === 'light') return 'Light Mode';
        if (theme === 'midnight') return 'Midnight';
        return 'Blue Dark';
    };

    return (
        <button
            className="admin-btn admin-btn-secondary"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'blue-dark' ? 'Midnight' : theme === 'midnight' ? 'Light' : 'Blue Dark'}`}
            style={{
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                border: '1px solid var(--admin-border-color)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.2s ease',
                background: 'var(--admin-bg-tertiary)'
            }}
        >
            {getIcon()}
            <span style={{ fontWeight: 600 }}>{getLabel()}</span>
        </button>
    );
};

export default ThemeSwitcher;
