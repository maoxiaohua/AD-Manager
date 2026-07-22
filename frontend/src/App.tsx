import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { Spin, Flex } from 'antd';
import AuthLayout from './layouts/AuthLayout';
import MainLayout from './layouts/MainLayout';
import ProtectedRoute from './layouts/ProtectedRoute';
import LoginPage from './pages/Login';
import DashboardPage from './pages/Dashboard';
import ComputersPage from './pages/Computers';
import UsersPage from './pages/Users';
import GroupsPage from './pages/Groups';
import SyncPage from './pages/Sync';
import SettingsPage from './pages/Settings';

export default function App() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <Flex justify="center" align="center" style={{ height: '100vh' }}>
        <Spin size="large" tip="Initializing..." />
      </Flex>
    );
  }

  return (
    <Routes>
      {/* Public routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/computers" element={<ComputersPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/groups" element={<GroupsPage />} />
          <Route path="/sync" element={<SyncPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
