import React from 'react';

// Simplified SVG Line Chart
export const AdminLineChart = ({ data = [], height = 150, color = 'var(--admin-accent-primary)' }) => {
    if (!data.length) return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--admin-text-muted)' }}>No data available</div>;

    const maxVal = Math.max(...data.map(d => d.value), 1);
    const minVal = Math.min(...data.map(d => d.value), 0);
    const range = maxVal - minVal;

    const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * 100;
        const y = 100 - ((d.value - minVal) / range) * 80 - 10; // Leave some padding
        return `${x},${y}`;
    }).join(' ');

    const areaPoints = `0,100 ${points} 100,100`;

    return (
        <div style={{ width: '100%', height, position: 'relative' }}>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height: '100%', display: 'block' }}>
                <defs>
                    <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                        <stop offset="100%" stopColor={color} stopOpacity="0" />
                    </linearGradient>
                </defs>
                <path d={areaPoints} fill="url(#chartGradient)" />
                <polyline
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    points={points}
                    style={{ vectorEffect: 'non-scaling-stroke' }}
                />
            </svg>
        </div>
    );
};

// Simplified SVG Bar Chart
export const AdminBarChart = ({ data = [], height = 150, color = 'var(--admin-accent-success)' }) => {
    if (!data.length) return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--admin-text-muted)' }}>No data available</div>;

    const maxVal = Math.max(...data.map(d => d.value), 1);
    const barWidth = 100 / (data.length * 1.5);

    return (
        <div style={{ width: '100%', height, position: 'relative' }}>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height: '100%', display: 'block' }}>
                {data.map((d, i) => {
                    const x = (i / data.length) * 100 + (barWidth / 2);
                    const h = (d.value / maxVal) * 90;
                    return (
                        <rect
                            key={i}
                            x={x}
                            y={100 - h}
                            width={barWidth}
                            height={h}
                            fill={color}
                            rx="1"
                            style={{ transition: 'all 0.3s ease' }}
                        >
                            <title>{`${d.label}: ${d.value}`}</title>
                        </rect>
                    );
                })}
            </svg>
        </div>
    );
};

const AdminChart = { Line: AdminLineChart, Bar: AdminBarChart };
export default AdminChart;
