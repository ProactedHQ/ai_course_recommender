import { useState, useEffect } from 'react';
import { Search, ShieldAlert, ShieldCheck, ShieldOff } from 'lucide-react';
import adminApi from '../../api/adminApi';
import { useAdminData } from '../../hooks/useAdminData';
import { useToast } from '../../context/ToastContext';
import AdminModal from '../../components/admin/AdminModal';
import '../../styles/AdminTheme.css';

const AdminManagement = () => {
    const { fetchData, loading: dataLoading } = useAdminData();
    const toast = useToast();
    const [users, setUsers] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [isPromoteModalOpen, setIsPromoteModalOpen] = useState(false);
    const [emailToPromote, setEmailToPromote] = useState('');

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const data = await fetchData('admin_users', () => adminApi.getUsers());
            setUsers(data || []);
        } catch (err) {
            console.error('Failed to load users:', err);
            toast.error('Failed to sync user directory.');
        }
    };

    const handlePromote = async () => {
        const foundUser = users.find(u => u.email.toLowerCase() === emailToPromote.toLowerCase());

        if (!foundUser) {
            toast.error('No user found with that email address.');
            return;
        }

        if (foundUser.is_staff) {
            toast.error('This user is already an administrator.');
            return;
        }

        try {
            await adminApi.updateUser(foundUser.id, { is_staff: true });
            toast.success(`Successfully promoted ${foundUser.email} to Admin.`);
            setIsPromoteModalOpen(false);
            setEmailToPromote('');
            loadUsers();
        } catch (err) {
            toast.error(`Promotion failed: ${err.message}`);
        }
    };

    const handleRevoke = async (user) => {
        if(window.confirm(`Are you sure you want to revoke admin privileges from ${user.email}?`)) {
            try {
                await adminApi.updateUser(user.id, { is_staff: false });
                toast.success(`Revoked privileges from ${user.email}`);
                loadUsers();
            } catch (err) {
                toast.error(`Failed to revoke privileges: ${err.message}`);
            }
        }
    };

    const adminUsers = users.filter(u => u.is_staff);

    return (
        <div className="admin-dashboard-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h1 style={{ color: 'var(--admin-text-primary)', fontFamily: 'var(--admin-font-heading)' }}>Admin Management</h1>
                <button 
                    className="admin-btn admin-btn-primary" 
                    onClick={() => setIsPromoteModalOpen(true)}
                    style={{ padding: '0.75rem 1.25rem', gap: '0.5rem' }}
                >
                    <ShieldAlert size={18} />
                    Promote to Admin
                </button>
            </div>

            <div className="admin-card">
                <div className="admin-table-container">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Administrator</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {adminUsers.length === 0 ? (
                                <tr>
                                    <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>
                                        <p style={{ color: 'var(--admin-text-muted)' }}>No administrators found.</p>
                                    </td>
                                </tr>
                            ) : (
                                adminUsers.map((user) => (
                                    <tr key={user.id}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                <span style={{ fontWeight: 600, color: 'var(--admin-text-primary)' }}>
                                                    {user.username || user.email?.split('@')[0] || 'Unknown Admin'}
                                                </span>
                                            </div>
                                        </td>
                                        <td style={{ fontSize: '0.875rem' }}>{user.email}</td>
                                        <td>
                                            <span className="admin-badge success">
                                                <ShieldCheck size={14} style={{ marginRight: '0.25rem' }} /> Active Admin
                                            </span>
                                        </td>
                                        <td>
                                            <button
                                                className="admin-btn admin-btn-secondary"
                                                style={{ padding: '0.5rem', color: 'var(--admin-accent-danger)' }}
                                                title="Revoke Admin Privileges"
                                                onClick={() => handleRevoke(user)}
                                            >
                                                <ShieldOff size={16} /> Revoke
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <AdminModal
                isOpen={isPromoteModalOpen}
                onClose={() => setIsPromoteModalOpen(false)}
                title="Promote User to Admin"
                footer={(
                    <>
                        <button className="admin-btn admin-btn-secondary" onClick={() => setIsPromoteModalOpen(false)}>Cancel</button>
                        <button className="admin-btn admin-btn-primary" onClick={handlePromote}>Promote Status</button>
                    </>
                )}
            >
                <div>
                    <label style={{ display: 'block', color: 'var(--admin-text-primary)', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500 }}>
                        User Email Address
                    </label>
                    <div style={{ position: 'relative' }}>
                        <Search
                            size={18}
                            style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-text-muted)' }}
                        />
                        <input
                            type="email"
                            placeholder="Enter exact email address..."
                            className="admin-search-input"
                            value={emailToPromote}
                            onChange={(e) => setEmailToPromote(e.target.value)}
                            style={{ paddingLeft: '2.75rem', width: '100%' }}
                        />
                    </div>
                    <p style={{ color: 'var(--admin-text-muted)', marginTop: '0.75rem', fontSize: '0.875rem' }}>
                        The user must already be registered in the system before they can be promoted to an administrator role.
                    </p>
                </div>
            </AdminModal>
        </div>
    );
};

export default AdminManagement;
