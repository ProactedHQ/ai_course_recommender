import { Outlet } from 'react-router-dom';
import AdminSidebar from '../../components/admin/AdminSidebar';
import AdminHeader from '../../components/admin/AdminHeader';
import { AdminThemeProvider, useAdminTheme } from '../../context/AdminThemeContext';
import { ToastProvider } from '../../context/ToastContext';
import ToastContainer from '../../components/common/ToastContainer';
import IdleLogout from '../../components/admin/IdleLogout';
import '../../styles/AdminTheme.css';

const AdminShell = () => {
    const { isSidebarCollapsed } = useAdminTheme();

    return (
        <div className="admin-container">
            <IdleLogout />
            <ToastContainer />
            <div className="admin-layout">
                <AdminSidebar />
                <div className={`admin-main-wrapper ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}
                    style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        marginLeft: isSidebarCollapsed ? '80px' : '280px',
                        transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                    }}
                >
                    <AdminHeader />
                    <main className="admin-main-content" style={{ padding: '1rem 2rem', margin: 0 }}>
                        <Outlet />
                    </main>
                </div>
            </div>
        </div>
    );
};

const AdminShellWrapper = () => (
    <AdminThemeProvider>
        <ToastProvider>
            <AdminShell />
        </ToastProvider>
    </AdminThemeProvider>
);

export default AdminShellWrapper;
