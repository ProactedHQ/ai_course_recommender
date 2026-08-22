import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    MoreVertical, Trash2, Share,
    History as HistoryIcon, Clock
} from 'lucide-react';
import { usePromptHistory } from '../../hooks/usePromptHistory';
import { groupPromptsByMonth, formatMonthYear } from '../../utils/historyGrouping';
import './PromptHistoryList.css';

const PromptHistoryList = ({ history, loading, onClose, isCollapsed }) => {
    const { deleteHistoryItem } = usePromptHistory();
    const [openMenuId, setOpenMenuId] = useState(null);


    // Close menu when clicking outside - MUST be before any conditional returns
    useEffect(() => {
        const handleClickOutside = () => setOpenMenuId(null);
        if (openMenuId) {
            document.addEventListener('click', handleClickOutside);
            return () => document.removeEventListener('click', handleClickOutside);
        }
    }, [openMenuId]);

    const navigate = useNavigate();

    // Handler functions
    const handleMenuToggle = (e, itemId) => {
        e.preventDefault();
        e.stopPropagation();
        setOpenMenuId(openMenuId === itemId ? null : itemId);
    };

    const handleDelete = async (e, itemId) => {
        e.preventDefault();
        e.stopPropagation();
        if (window.confirm("Are you sure you want to delete this recommendation?")) {
            setOpenMenuId(null);
            await deleteHistoryItem(itemId);
        }
    };

    // Navigate to the detail page where the full Share button lives.
    // Share requires the full recommendation data which is only loaded there.
    const handleShare = (e, itemId) => {
        e.preventDefault();
        e.stopPropagation();
        setOpenMenuId(null);
        if (onClose) onClose();
        // Pass autoShare state so HistoryDetail/PromptResult knows to trigger modal
        navigate(`/app/history/${itemId}`, { state: { autoShare: true } });
    };

    // Early returns AFTER all hooks
    if (isCollapsed) {
        return (
            <div className="history-mini-anchor" title="View History">
                <Clock size={18} />
            </div>
        );
    }

    if (loading) {
        return <div className="history-loader">Loading history...</div>;
    }

    if (!history || history.length === 0) {
        return <div className="empty-history">No history yet</div>;
    }

    // Group by month
    const groupedHistory = groupPromptsByMonth(history);


    return (
        <React.Fragment>
            <div className="prompt-history-list">
                {groupedHistory.map((group, groupIndex) => (
                    <div key={`${group.year}-${group.month}`} className="history-month-group">
                        {/* Only show header for past months */}
                        {!group.isCurrentMonth && (
                            <div className="month-header">
                                {formatMonthYear(group.month, group.year)}
                            </div>
                        )}

                        {group.items.map(item => (
                            <div key={item.id} className="history-item-wrapper">
                                <NavLink
                                    to={`/app/history/${item.id}`}
                                    className="history-item"
                                    onClick={onClose}
                                >
                                    <span className="history-item-title">{item.title}</span>
                                </NavLink>

                                <button
                                    className={`history-menu-btn ${openMenuId === item.id ? 'active' : ''}`}
                                    onClick={(e) => handleMenuToggle(e, item.id)}
                                    aria-label="More options"
                                >
                                    <MoreVertical size={14} strokeWidth={2.5} />
                                </button>

                                {openMenuId === item.id && (
                                    <div className="history-dropdown-menu">
                                        <button
                                            className="menu-item"
                                            onClick={(e) => handleShare(e, item.id)}
                                        >
                                            <Share size={14} />
                                            <span>Share</span>
                                        </button>
                                        <button
                                            className="menu-item menu-item-delete"
                                            onClick={(e) => handleDelete(e, item.id)}
                                        >
                                            <Trash2 size={13} />
                                            <span>Delete</span>
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                ))}
            </div>

        </React.Fragment>
    );
};

export default PromptHistoryList;
