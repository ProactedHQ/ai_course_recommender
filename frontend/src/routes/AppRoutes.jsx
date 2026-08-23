import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";

import Home from "../pages/Home";
import SignIn from "../pages/auth/SignIn";
import SignUp from "../pages/auth/SignUp";
import AuthCallback from "../pages/auth/AuthCallback";
import ResetPassword from "../pages/auth/ResetPassword";
import AppShell from "../pages/app/AppShell";
import NewPrompt from "../pages/app/NewPrompt";
import HistoryDetail from "../pages/app/HistoryDetail";
import ProfileSettings from "../pages/app/ProfileSettings";
import Subscription from "../pages/app/Subscription";
import Onboarding from "../pages/app/Onboarding";
import Billing from "../pages/app/Billing";
import Dashboard from "../pages/dashboard/Dashboard";
import ProtectedRoute from "../components/layout/ProtectedRoute";

// Admin Imports
import AdminProtectedRoute from "../components/layout/AdminProtectedRoute";
import AdminShell from "../pages/admin/AdminShell";
import AdminDashboard from "../pages/admin/AdminDashboard";
import UserManagement from "../pages/admin/UserManagement";
import SubscriptionManager from "../pages/admin/SubscriptionManager";
import ActivityLogs from "../pages/admin/ActivityLogs";
import Analytics from "../pages/admin/Analytics";
import ChatLogs from "../pages/admin/ChatLogs";
import AdminManagement from "../pages/admin/AdminManagement";

// Placeholder Legal Pages
import LegalPrivacy from "../pages/legal/LegalPrivacy";
import TermsOfService from "../pages/legal/TermsOfService";
import LegalCookies from "../pages/legal/LegalCookies";
import About from "../pages/About";

// Blog Routes
import BlogList from "../pages/blog/BlogList";
import BlogPost from "../pages/blog/BlogPost";

import WhatsAppFloatingButton from "../components/common/WhatsAppFloatingButton";
import ScrollToHash from "../components/common/ScrollToHash";

function PublicOnlyWhatsApp() {
  const location = useLocation();
  const publicPaths = ["/", "/signin", "/signup", "/privacy-policy", "/terms-of-service", "/cookie-policy", "/about", "/reset-password", "/auth/callback"];

  // Only show if the current path is in publicPaths
  // and specifically NOT under /app or /dashboard or /onboarding etc.
  const isPublic = (publicPaths.includes(location.pathname) ||
    (!location.pathname.startsWith('/app') &&
      !location.pathname.startsWith('/dashboard') &&
      !location.pathname.startsWith('/onboarding') &&
      !location.pathname.startsWith('/billing'))) &&
    !location.pathname.startsWith('/admin');

  if (!isPublic) return null;

  return <WhatsAppFloatingButton />;
}

function AppRoutes() {
  return (
    <BrowserRouter>
      <ScrollToHash />
      <PublicOnlyWhatsApp />
      <Routes>

        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/kedira-insider" element={<BlogList />} />
        <Route path="/kedira-insider/:slug" element={<BlogPost />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/reset-password" element={<ResetPassword />} />


        {/* Protected App Routes */}
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/app/new" replace />} />
          <Route path="new" element={<NewPrompt />} />
          <Route path="history/:id" element={<HistoryDetail />} />
          <Route path="settings" element={<ProfileSettings />} />
          <Route path="subscription" element={<Subscription />} />
          {/* Redirect /app/admin to /admin for convenience */}
          <Route path="admin" element={<Navigate to="/admin" replace />} />
          {/* Catch-all for unknown app routes -> redirect to dashboard */}
          <Route path="*" element={<Navigate to="/app" replace />} />
        </Route>

        <Route
          path="/dashboard"
          element={<Navigate to="/app" replace />}
        />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/billing"
          element={
            <ProtectedRoute>
              <Billing />
            </ProtectedRoute>
          }
        />

        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <AdminProtectedRoute>
              <AdminShell />
            </AdminProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="subscriptions" element={<SubscriptionManager />} />
          <Route path="activity" element={<ActivityLogs />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="chats" element={<ChatLogs />} />
          <Route path="admins" element={<AdminManagement />} />
        </Route>

        {/* Legal Routes */}
        <Route path="/privacy-policy" element={<LegalPrivacy />} />
        <Route path="/terms-of-service" element={<TermsOfService />} />
        <Route path="/cookie-policy" element={<LegalCookies />} />
      </Routes>

    </BrowserRouter>
  );
}

export default AppRoutes;
