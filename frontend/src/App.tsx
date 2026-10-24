import { LogoutOutlined, ShopOutlined, UnorderedListOutlined, SettingOutlined, TeamOutlined } from '@ant-design/icons';
import { Alert, Button, Layout, Menu, message, Spin, Typography } from 'antd';
import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { apiRequest, setDisplayTimeZone, type UserProfile } from './api/client';

const FactoriesPage = lazy(() => import('./pages/FactoriesPage').then((module) => ({ default: module.FactoriesPage })));
const FactoryDetailPage = lazy(() => import('./pages/FactoryDetailPage').then((module) => ({ default: module.FactoryDetailPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((module) => ({ default: module.LoginPage })));
const RequestDetailPage = lazy(() => import('./pages/RequestDetailPage').then((module) => ({ default: module.RequestDetailPage })));
const RequestsPage = lazy(() => import('./pages/RequestsPage').then((module) => ({ default: module.RequestsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((module) => ({ default: module.SettingsPage })));
const UsersPage = lazy(() => import('./pages/UsersPage').then((module) => ({ default: module.UsersPage })));

const { Header, Content, Sider } = Layout;

export function App() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [demoMode, setDemoMode] = useState(false);
  const [healthError, setHealthError] = useState<string>();
  const location = useLocation();
  const queryClient = useQueryClient();

  useEffect(() => {
    apiRequest<{ demo_mode: boolean; timezone: string }>('/health')
      .then((health) => {
        setDemoMode(health.demo_mode);
        setDisplayTimeZone(health.timezone);
      })
      .catch((error: unknown) => {
        setHealthError(error instanceof Error ? error.message : 'Backend недоступен');
      });
  }, []);

  useEffect(() => {
    apiRequest<UserProfile>('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setCheckingSession(false));
  }, []);

  const navItems = useMemo(() => [
    { key: '/', icon: <UnorderedListOutlined />, label: <Link to="/">Центр заявок</Link> },
    { key: '/factories', icon: <ShopOutlined />, label: <Link to="/factories">Заводы</Link> },
    ...(user?.role === 'admin' ? [
      { key: '/users', icon: <TeamOutlined />, label: <Link to="/users">Пользователи</Link> },
      { key: '/settings', icon: <SettingOutlined />, label: <Link to="/settings">Настройки интеграции</Link> },
    ] : []),
  ], [user?.role]);

  async function logout() {
    try {
      await apiRequest<void>('/auth/logout', { method: 'POST' });
      queryClient.clear();
      setUser(null);
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось завершить сеанс');
    }
  }

  function completeLogin(profile: UserProfile) {
    setUser(profile);
  }

  if (checkingSession) return <div className="app-loading"><Spin size="large" /></div>;
  if (!user) {
    return (
      <>
        {healthError && <Alert message="Нет соединения с сервером" description={healthError} type="error" showIcon />}
        <Suspense fallback={<div className="app-loading"><Spin /></div>}>
          <LoginPage onLogin={completeLogin} demoMode={demoMode} />
        </Suspense>
      </>
    );
  }

  const canEdit = user.role === 'admin' || user.role === 'buyer';
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={250} theme="light" breakpoint="lg" collapsedWidth={80}>
        <div className="brand">
          <Typography.Text strong>Хайр Строй</Typography.Text>
          <Typography.Text type="secondary">Закупки</Typography.Text>
        </div>
        <Menu items={navItems} mode="inline" selectedKeys={[location.pathname.startsWith('/requests/') ? '/' : location.pathname.startsWith('/factories/') ? '/factories' : location.pathname]} />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Typography.Text strong>Khair Procurement Center</Typography.Text>
          <div className="user-header">
            <Typography.Text>{user.full_name} · {user.role === 'admin' ? 'Администратор' : user.role === 'buyer' ? 'Закупщик' : 'Руководитель'}</Typography.Text>
            <Button type="text" icon={<LogoutOutlined />} onClick={logout}>Выйти</Button>
          </div>
        </Header>
        <Content className="app-content">
          {demoMode && <Alert message="Демонстрационный режим. Данные показаны отдельно от Bitrix24." type="info" showIcon closable className="demo-banner" />}
          {healthError && <Alert message="Не удалось проверить режим приложения" description={healthError} type="error" showIcon className="demo-banner" />}
          <Suspense fallback={<div className="app-loading"><Spin /></div>}>
            <Routes>
              <Route path="/" element={<RequestsPage canViewHistory={user.role === 'admin' || user.role === 'manager'} />} />
              <Route path="/requests/:requestId" element={<RequestDetailPage canEdit={canEdit} canViewHistory={user.role === 'admin' || user.role === 'manager'} />} />
              <Route path="/factories" element={<FactoriesPage canEdit={canEdit} />} />
              <Route path="/factories/:factoryId" element={<FactoryDetailPage canViewHistory={user.role === 'admin' || user.role === 'manager'} />} />
              {user.role === 'admin' && <Route path="/users" element={<UsersPage />} />}
              {user.role === 'admin' && <Route path="/settings" element={<SettingsPage />} />}
              <Route path="*" element={<RequestsPage canViewHistory={user.role === 'admin' || user.role === 'manager'} />} />
            </Routes>
          </Suspense>
        </Content>
      </Layout>
    </Layout>
  );
}
