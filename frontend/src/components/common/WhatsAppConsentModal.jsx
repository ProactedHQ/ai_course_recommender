import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { MessageCircle, X } from 'lucide-react';
import './WhatsAppConsentModal.css';

const WHATSAPP_GROUP_LINK = "https://chat.whatsapp.com/KGUrKvbzPI95D5oOmbHovP";

const WhatsAppConsentModal = ({ isOpen, onClose }) => {
    const modalRef = useRef(null);

    // Close on ESC key
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') onClose();
        };

        if (isOpen) {
            document.addEventListener('keydown', handleKeyDown);
            // Lock body scroll
            document.body.style.overflow = 'hidden';
        }

        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onClose]);

    // Handle outside click
    const handleOverlayClick = (e) => {
        if (modalRef.current && !modalRef.current.contains(e.target)) {
            onClose();
        }
    };

    const handleJoin = () => {
        // Track event if analytics were present here
        // console.log('User joined WhatsApp group');

        window.open(WHATSAPP_GROUP_LINK, '_blank', 'noopener,noreferrer');
        onClose();
    };

    if (!isOpen) return null;

    return createPortal(
        <div className="wa-consent-overlay" onClick={handleOverlayClick}>
            <div className="wa-consent-modal" ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="wa-modal-title">
                <div className="wa-modal-header">
                    <div className="wa-modal-icon">
                        <MessageCircle size={32} strokeWidth={2.5} />
                    </div>
                    <h2 id="wa-modal-title" className="wa-modal-title">
                        Join PROACTED WhatsApp Support Group
                    </h2>
                </div>

                <div className="wa-modal-body">
                    <p>
                        You are about to join the official PROACTED WhatsApp support group for Kenyan students.
                        This group is used for support, updates, and guidance related to course recommendations.
                        You can leave the group at any time.
                    </p>
                </div>

                <div className="wa-actions">
                    <button className="btn-wa-join" onClick={handleJoin} autoFocus>
                        Join WhatsApp Group
                    </button>
                    <button className="btn-wa-cancel" onClick={onClose}>
                        Cancel
                    </button>
                </div>
            </div>
        </div>,
        document.body
    );
};

export default WhatsAppConsentModal;
