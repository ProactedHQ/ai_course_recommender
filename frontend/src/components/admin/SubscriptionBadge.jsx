import '../../styles/AdminTheme.css';

const SubscriptionBadge = ({ tier }) => {
    const labels = {
        'explorer': 'Explorer',
        'mentor_elite': 'Mentor Elite',
        'scholar_vvip': 'Scholar VVIP',
        'free': 'Explorer',
        'standard': 'Mentor Elite',
        'premium': 'Scholar VVIP'
    };

    const label = labels[tier?.toLowerCase()] || tier || 'Explorer';
    const tierClass = tier ? tier.toLowerCase().replace('_', '-') : 'explorer';

    return (
        <span className={`admin-badge ${tierClass}`}>
            {label}
        </span>
    );
};

export default SubscriptionBadge;
