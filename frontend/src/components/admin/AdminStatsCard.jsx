import { TrendingUp, TrendingDown } from 'lucide-react';
import '../../styles/AdminTheme.css';

const AdminStatsCard = ({ title, value, icon: Icon, trend, iconClass = 'primary' }) => {
    const isPositive = trend && trend > 0;
    const isNegative = trend && trend < 0;

    return (
        <div className="admin-stat-card glass-premium">
            <div className="admin-stat-header">
                <div>
                    <div className="admin-stat-label">{title}</div>
                    <div className="admin-stat-value">{value}</div>
                    {trend !== undefined && trend !== null && (
                        <div className={`admin-stat-trend ${isPositive ? 'up' : isNegative ? 'down' : ''}`}>
                            {isPositive ? <TrendingUp size={16} /> : isNegative ? <TrendingDown size={16} /> : null}
                            <span>{isPositive ? '+' : ''}{trend}%</span>
                        </div>
                    )}
                </div>
                <div className={`admin-stat-icon-glow ${iconClass}`}>
                    <Icon size={24} />
                </div>
            </div>
        </div>
    );
};

export default AdminStatsCard;
