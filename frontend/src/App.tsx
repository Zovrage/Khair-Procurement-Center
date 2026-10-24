import { Layout, Menu, Typography } from 'antd';
import { useMemo } from 'react';
import { Link, Route, Routes } from 'react-router-dom';
import { DashboardPage } from './pages/DashboardPage';
import { FactoriesPage } from './pages/FactoriesPage';
import { RequestsPage } from './pages/RequestsPage';
import { SettingsPage } from './pages/SettingsPage';

const { Header, Content, Sider } = Layout;

const navItems = [
  { key: 'requests', label: <Link to="/">Центр заявок</Link> },
  { key: 'factories', label: <Link to="/factories">Заводы</Link> },
  { key: 'settings', label: <Link to="/settings">Настройки интеграции</Link> },
];

export function App() {
  const title = useMemo(() => 'Khair Procurement Center', []);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="light" breakpoint="lg" collapsedWidth={80}>
        <div style={{ padding: 16 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>{title}</Typography.Title>
        </div>
        <Menu items={navItems} mode="inline" defaultSelectedKeys={['requests']} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', paddingInline: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography.Text strong>Центр закупок</Typography.Text>
          <Typography.Text>Администратор</Typography.Text>
        </Header>
        <Content style={{ margin: 20 }}>
          <Routes>
            <Route path="/" element={<RequestsPage />} />
            <Route path="/factories" element={<FactoriesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}
