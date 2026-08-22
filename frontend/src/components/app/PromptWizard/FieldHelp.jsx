import React, { useState, useRef, useEffect } from 'react';
import { HelpCircle, X } from 'lucide-react';
import './Wizard.css';

const FieldHelp = ({ title, content }) => {
    const [isOpen, setIsOpen] = useState(false);
    const popupRef = useRef(null);

    // Close on outside click
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (popupRef.current && !popupRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen]);

    return (
        <span className={`field-help-container ${isOpen ? 'active' : ''}`} ref={popupRef}>
            <button 
                type="button" 
                className={`btn-help-icon ${isOpen ? 'active' : ''}`}
                onClick={(e) => { e.preventDefault(); setIsOpen(!isOpen); }}
                title="Click for help"
            >
                <HelpCircle size={16} />
            </button>
            {isOpen && (
                <div className="field-help-popup">
                    <button type="button" className="btn-close-help" onClick={(e) => { e.preventDefault(); setIsOpen(false); }}>
                        <X size={14} />
                    </button>
                    {title && <h4 className="help-popup-title">{title}</h4>}
                    <div className="help-popup-content">{content}</div>
                </div>
            )}
        </span>
    );
};

export default FieldHelp;
