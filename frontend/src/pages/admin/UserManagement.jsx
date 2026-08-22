import { useState, useEffect } from 'react';
import { Search, Edit, Eye, UserX, Loader2, Filter } from 'lucide-react';
import adminApi from '../../api/adminApi';
import SubscriptionBadge from '../../components/admin/SubscriptionBadge';
import AdminModal from '../../components/admin/AdminModal';
import { useAdminData } from '../../hooks/useAdminData';
import { useToast } from '../../context/ToastContext';
import '../../styles/AdminTheme.css';

const UserManagement = () => {
    const { fetchData, loading: dataLoading } = useAdminData();
    const toast = useToast();
    const [users, setUsers] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterTier, setFilterTier] = useState('all');
    const [error, setError] = useState(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [newTier, setNewTier] = useState('explorer');

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const data = await fetchData('admin_users', () => adminApi.getUsers());
            setUsers(data || []);
        } catch (err) {
            console.error('Failed to load users:', err);
            setError(err.message);
            toast.error('Failed to sync user directory.');
        }
    };

    const handleOpenEdit = (user) => {
        setEditingUser(user);
        setNewTier(user.subscription_tier || 'explorer');
        setIsEditModalOpen(true);
    };

    const handleEditSubscription = async () => {
        if (!editingUser) return;

        try {
            await adminApi.updateUser(editingUser.id, { subscription_tier: newTier });
            toast.success(`Updated ${editingUser.username || editingUser.email} to ${newTier}`);
            setIsEditModalOpen(false);
            loadUsers();
        } catch (err) {
            console.error('Failed to update subscription:', err);
            toast.error(`Update failed: ${err.message}`);
        }
    };

    const handleDeleteUser = async (user) => {
        if(window.confirm(`Are you absolutely sure you want to delete ${user.email}? This action is irreversible and restricted to the root admin.`)) {
            try {
                await adminApi.deleteUser(user.id);
                toast.success('User permanently deleted.');
                loadUsers();
            } catch (err) {
                console.error('Failed to delete user:', err);
                toast.error(err.response?.data?.error || `Deletion failed: ${err.message}`);
            }
        }
    };

    const filteredUsers = users.filter(user => {
        const matchesSearch = !searchTerm ||
            user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.username?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesTier = filterTier === 'all' ||
            (user.subscription_tier || 'explorer').toLowerCase() === filterTier.toLowerCase();

        return matchesSearch && matchesTier;
    });

    if (dataLoading && !users.length) {
        return (
            <div className="admin-dashboard-fade-in">
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>User Management</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--admin-text-muted)' }}>
                    <div className="admin-loading-spinner"></div>
                    <span>Synchronizing user directory...</span>
                </div>
            </div>
        );
    }

    if (error && !users.length) {
        return (
            <div className="admin-dashboard-fade-in">
                <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>User Management</h1>
                <div className="admin-card" style={{ borderLeft: '4px solid var(--admin-accent-danger)' }}>
                    <p style={{ color: 'var(--admin-accent-danger)', fontWeight: 600 }}>Synchronization Error</p>
                    <p style={{ color: 'var(--admin-text-muted)', marginTop: '0.5rem' }}>{error}</p>
                    <button className="admin-btn admin-btn-primary" onClick={loadUsers} style={{ marginTop: '1.5rem' }}>
                        Retry Synchronization
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard-fade-in">
            <h1 style={{ marginBottom: '2rem', color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>User Management</h1>

            <div className="admin-search-bar">
                <div style={{ position: 'relative', flex: 1 }}>
                    <Search
                        size={18}
                        style={{
                            position: 'absolute',
                            left: '1rem',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            color: 'var(--admin-text-muted)'
                        }}
                    />
                    <input
                        type="text"
                        placeholder="Search by email or name..."
                        className="admin-search-input"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{ paddingLeft: '2.75rem' }}
                    />
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Filter size={18} color="var(--admin-text-muted)" />
                    <select
                        className="admin-search-input"
                        value={filterTier}
                        onChange={(e) => setFilterTier(e.target.value)}
                        style={{ minWidth: '150px' }}
                    >
                        <option value="all">All Tiers</option>
                        <option value="explorer">Explorer</option>
                        <option value="mentor_elite">Mentor Elite</option>
                        <option value="scholar_vvip">Scholar VVIP</option>
                    </select>
                </div>
            </div>

            <div className="admin-card">
                <div className="admin-table-container">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Email</th>
                                <th>Subscription</th>
                                <th>Joined</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredUsers.length === 0 ? (
                                <tr>
                                    <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>
                                        <p style={{ color: 'var(--admin-text-muted)' }}>No users matching criteria</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredUsers.map((user) => (
                                    <tr key={user.id}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                <div style={{
                                                    width: '40px',
                                                    height: '40px',
                                                    borderRadius: '10px',
                                                    background: 'linear-gradient(135deg, var(--admin-accent-primary), var(--admin-accent-secondary))',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontWeight: 700,
                                                    color: 'white',
                                                    fontSize: '0.9rem'
                                                }}>
                                                    {user.username?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || 'U'}
                                                </div>
                                                <span style={{ fontWeight: 600, color: 'var(--admin-text-primary)' }}>
                                                    {user.username || user.email?.split('@')[0] || 'Unknown'}
                                                </span>
                                            </div>
                                        </td>
                                        <td style={{ fontSize: '0.875rem' }}>{user.email}</td>
                                        <td>
                                            <SubscriptionBadge tier={user.subscription_tier || 'explorer'} />
                                        </td>
                                        <td style={{ fontSize: '0.875rem' }}>
                                            {user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}
                                        </td>
                                        <td>
                                            <span className={`admin-badge ${user.is_active !== false ? 'success' : 'danger'}`}>
                                                {user.is_active !== false ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                                <button className="admin-btn admin-btn-secondary" style={{ padding: '0.5rem' }} title="View Details">
                                                    <Eye size={16} />
                                                </button>
                                                <button
                                                    className="admin-btn admin-btn-primary"
                                                    style={{ padding: '0.5rem' }}
                                                    title="Edit Subscription"
                                                    onClick={() => handleOpenEdit(user)}
                                                >
                                                    <Edit size={16} />
                                                </button>
                                                <button
                                                    className="admin-btn"
                                                    style={{ padding: '0.5rem', background: 'var(--admin-accent-danger)', color: 'white', border: 'none' }}
                                                    title="Delete User (Root Admin Only)"
                                                    onClick={() => handleDeleteUser(user)}
                                                >
                                                    <UserX size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <AdminModal
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
                title="Edit User Subscription"
                footer={(
                    <>
                        <button className="admin-btn admin-btn-secondary" onClick={() => setIsEditModalOpen(false)}>Cancel</button>
                        <button className="admin-btn admin-btn-primary" onClick={handleEditSubscription}>Save Changes</button>
                    </>
                )}
            >
                <div>
                    <p style={{ color: 'var(--admin-text-muted)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                        Modifying subscription for <strong style={{ color: 'var(--admin-text-primary)' }}>{editingUser?.username || editingUser?.email}</strong>
                    </p>
                    <label style={{ display: 'block', color: 'var(--admin-text-primary)', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500 }}>
                        Select Subscription Tier
                    </label>
                    <select
                        className="admin-search-input"
                        style={{ width: '100%' }}
                        value={newTier}
                        onChange={(e) => setNewTier(e.target.value)}
                    >
                        <option value="explorer">Explorer</option>
                        <option value="mentor_elite">Mentor Elite</option>
                        <option value="scholar_vvip">Scholar VVIP</option>
                    </select>
                </div>
            </AdminModal>
        </div>
    );
};

export default UserManagement;
