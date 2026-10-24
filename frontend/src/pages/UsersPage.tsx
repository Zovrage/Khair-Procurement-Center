import { EditOutlined, PlusOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, Modal, Select, Space, Switch, Table, Tag, Typography, message } from 'antd';
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest, type Role } from '../api/client';

interface AppUser {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

const roleOptions = [
  { value: 'admin', label: 'Администратор' },
  { value: 'buyer', label: 'Закупщик' },
  { value: 'manager', label: 'Руководитель' },
];

export function UsersPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<AppUser>();
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const usersQuery = useQuery({
    queryKey: ['users'],
    queryFn: () => apiRequest<AppUser[]>('/api/v1/users'),
  });
  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => apiRequest<AppUser>(
      editing ? `/api/v1/users/${editing.id}` : '/api/v1/users',
      { method: editing ? 'PATCH' : 'POST', body: JSON.stringify(values) },
    ),
    onSuccess: async () => {
      message.success(editing ? 'Пользователь обновлён' : 'Пользователь создан');
      setModalOpen(false);
      setEditing(undefined);
      form.resetFields();
      await queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error) => message.error(error instanceof Error ? error.message : 'Не удалось сохранить пользователя'),
  });

  function openCreate() {
    setEditing(undefined);
    form.resetFields();
    form.setFieldsValue({ role: 'buyer', is_active: true });
    setModalOpen(true);
  }

  function openEdit(user: AppUser) {
    setEditing(user);
    form.setFieldsValue({ full_name: user.full_name, role: user.role, is_active: user.is_active, password: '' });
    setModalOpen(true);
  }

  return (
    <>
      <Card
        title={<div><Typography.Title level={3} style={{ margin: 0 }}>Пользователи</Typography.Title><Typography.Text type="secondary">Управление учётными записями и ролями</Typography.Text></div>}
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить пользователя</Button>}
      >
        {usersQuery.isError && <Typography.Text type="danger">{usersQuery.error.message}</Typography.Text>}
        <Table
          rowKey="id"
          dataSource={usersQuery.data ?? []}
          loading={usersQuery.isLoading}
          pagination={{ pageSize: 20 }}
          columns={[
            { title: 'Имя', dataIndex: 'full_name', key: 'full_name' },
            { title: 'Логин', dataIndex: 'username', key: 'username' },
            { title: 'Роль', dataIndex: 'role', key: 'role', render: (role: Role) => roleOptions.find((item) => item.value === role)?.label ?? role },
            { title: 'Статус', dataIndex: 'is_active', key: 'is_active', render: (active: boolean) => <Tag color={active ? 'green' : 'default'}>{active ? 'Активен' : 'Отключён'}</Tag> },
            { title: 'Действия', key: 'actions', render: (_: unknown, user: AppUser) => <Button icon={<EditOutlined />} onClick={() => openEdit(user)}>Изменить</Button> },
          ]}
        />
      </Card>
      <Modal
        title={editing ? `Учётная запись: ${editing.username}` : 'Новый пользователь'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
        confirmLoading={saveMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(values) => {
          if (editing && !values.password) delete values.password;
          saveMutation.mutate(values);
        }}>
          {!editing && (
            <Form.Item name="username" label="Логин" rules={[{ required: true, min: 2, message: 'Введите логин (не менее 2 символов)' }]}>
              <Input autoComplete="off" />
            </Form.Item>
          )}
          <Form.Item name="full_name" label="Имя" rules={[{ required: true, whitespace: true, message: 'Введите имя пользователя' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="role" label="Роль" rules={[{ required: true }]}>
            <Select options={roleOptions} />
          </Form.Item>
          {!editing && (
            <Form.Item name="password" label="Пароль" rules={[{ required: true, min: 12, message: 'Пароль должен быть не короче 12 символов' }]}>
              <Input.Password autoComplete="new-password" />
            </Form.Item>
          )}
          {editing && (
            <Form.Item name="password" label="Новый пароль (оставьте пустым без изменений)" rules={[{ min: 12, message: 'Пароль должен быть не короче 12 символов' }]}>
              <Input.Password autoComplete="new-password" />
            </Form.Item>
          )}
          {editing && (
            <Form.Item name="is_active" label="Учётная запись активна" valuePropName="checked">
              <Switch />
            </Form.Item>
          )}
          <Space>
            <Typography.Text type="secondary">Изменения прав и пароля сохраняются на сервере.</Typography.Text>
          </Space>
        </Form>
      </Modal>
    </>
  );
}
