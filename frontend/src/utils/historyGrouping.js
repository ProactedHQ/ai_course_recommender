/**
 * Groups prompts by month and year
 * @param {Array} prompts - Array of prompt objects with created_at timestamps
 * @returns {Array} Array of groups with month headers and items
 */
export function groupPromptsByMonth(prompts) {
    if (!prompts || prompts.length === 0) {
        return [];
    }

    // Sort prompts by created_at (newest first)
    const sorted = [...prompts]
        .filter(p => p.created_at && !isNaN(new Date(p.created_at).getTime()))
        .sort((a, b) => {
            const dateA = new Date(a.created_at);
            const dateB = new Date(b.created_at);
            return dateB - dateA; // Descending order
        });

    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    const groups = [];
    const monthMap = new Map();

    sorted.forEach(prompt => {
        const date = new Date(prompt.created_at);
        const month = date.getMonth();
        const year = date.getFullYear();

        // Create a key for the month-year combination
        const key = `${year}-${month}`;

        if (!monthMap.has(key)) {
            monthMap.set(key, {
                month,
                year,
                items: [],
                isCurrentMonth: month === currentMonth && year === currentYear
            });
        }

        monthMap.get(key).items.push(prompt);
    });

    // Convert map to array and sort by date (newest first)
    const sortedGroups = Array.from(monthMap.values()).sort((a, b) => {
        if (a.year !== b.year) {
            return b.year - a.year;
        }
        return b.month - a.month;
    });

    return sortedGroups;
}

/**
 * Formats month and year for display
 * @param {number} month - Month index (0-11)
 * @param {number} year - Full year
 * @returns {string} Formatted month name and year (e.g., "December 2025")
 */
export function formatMonthYear(month, year) {
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    return `${monthNames[month]} ${year}`;
}
