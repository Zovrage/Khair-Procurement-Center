import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, Typography, message } from 'antd';
import { useState } from 'react';
import { apiRequest, type UserProfile } from '../api/client';

interface LoginPageProps {
  onLogin: (user: UserProfile) => void;
  demoMode: boolean;
}

export function LoginPage({ onLogin, demoMode }: LoginPageProps) {
  const [loading, setLoading] = useState(false);

  async function submit(values: { username: string; password: string }) {
    setLoading(true);
    try {
      await apiRequest<UserProfile>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(values),
      });
      const user = await apiRequest<UserProfile>('/auth/me');
      onLogin(user);
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось войти');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <Card className="login-card">
        <Typography.Title level={3}>Khair Procurement Center</Typography.Title>
        <Typography.Paragraph type="secondary">Войдите, чтобы продолжить работу</Typography.Paragraph>
        <Form layout="vertical" onFinish={submit}>
          <Form.Item name="username" label="Логин" rules={[{ required: true, message: 'Введите логин' }]}>
            <Input prefix={<UserOutlined />} autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="Пароль" rules={[{ required: true, message: 'Введите пароль' }]}>
            <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>Войти</Button>
        </Form>
        {demoMode && <Typography.Paragraph type="secondary" className="demo-hint">Демо-доступ: admin / admin123</Typography.Paragraph>}
      </Card>
    </div>
  );
}
