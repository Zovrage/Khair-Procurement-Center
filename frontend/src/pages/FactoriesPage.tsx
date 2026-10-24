import { EditOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, InputNumber, Modal, Select, Space, Table, Tag, Typography, message } from 'antd';
import type { TablePaginationConfig } from 'antd/es/table';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest, type Factory } from '../api/client';

const emptyFactory: Partial<Factory> = { status: 'active' };

interface FactoryList {
  items: Factory[];
  total: number;
  page: number;
  page_size: number;
}

export function FactoriesPage({ canEdit }: { canEdit: boolean }) {
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<string>();
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Factory>();
  const [form] = Form.useForm<Factory>();
  const queryClient = useQueryClient();
  const factoriesQuery = useQuery({
    queryKey: ['factories', query, status, page],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: '20' });
      if (query) params.set('q', query);
      if (status) params.set('status', status);
      return apiRequest<FactoryList>(`/api/v1/factories?${params}`);
    },
  });

  const saveMutation = useMutation({
    mutationFn: (values: Factory) => apiRequest<Factory>(
      editing ? `/api/v1/factories/${editing.id}` : '/api/v1/factories',
      { method: editing ? 'PATCH' : 'POST', body: JSON.stringify(values) },
    ),
    onSuccess: async () => {
      message.success(editing ? 'Данные завода обновлены' : 'Завод создан');
      setModalOpen(false);
      setEditing(undefined);
      form.resetFields();
      await queryClient.invalidateQueries({ queryKey: ['factories'] });
    },
    onError: (error) => message.error(error instanceof Error ? error.message : 'Не удалось сохранить завод'),
  });

  function openCreate() {
    setEditing(undefined);
    form.resetFields();
    form.setFieldsValue(emptyFactory);
    setModalOpen(true);
  }

  function openEdit(factory: Factory) {
    setEditing(factory);
    form.setFieldsValue(factory);
    setModalOpen(true);
  }

  async function archive(factory: Factory) {
    try {
      await apiRequest(`/api/v1/factories/${factory.id}/archive`, { method: 'POST' });
      message.success('Завод перенесён в архив');
      await queryClient.invalidateQueries({ queryKey: ['factories'] });
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось архивировать завод');
    }
  }

  return (
    <>
      <Card
        title={<div><Typography.Title level={3} style={{ margin: 0 }}>Заводы</Typography.Title><Typography.Text type="secondary">Справочник поставщиков</Typography.Text></div>}
        extra={canEdit && <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить завод</Button>}
      >
        <Space wrap className="request-filters">
          <Input.Search
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            onSearch={(value) => { setQuery(value.trim()); setPage(1); }}
            placeholder="Поиск по названию или контакту"
            prefix={<SearchOutlined />}
            allowClear
            style={{ width: 320 }}
          />
          <Select
            allowClear
            placeholder="Все статусы"
            style={{ width: 180 }}
            value={status}
            onChange={(value) => { setStatus(value); setPage(1); }}
            options={[{ value: 'active', label: 'Активные' }, { value: 'archived', label: 'Архивные' }]}
          />
        </Space>
        {factoriesQuery.isError && <Typography.Text type="danger">{factoriesQuery.error.message}</Typography.Text>}
        <Table
          dataSource={factoriesQuery.data?.items ?? []}
          loading={factoriesQuery.isLoading}
          rowKey="id"
          scroll={{ x: 1000 }}
          pagination={{
            current: page,
            pageSize: factoriesQuery.data?.page_size ?? 20,
            total: factoriesQuery.data?.total ?? 0,
            showSizeChanger: false,
            showTotal: (total) => `Всего: ${total}`,
          }}
          onChange={(pagination: TablePaginationConfig) => setPage(pagination.current ?? 1)}
          columns={[
            { title: 'Название завода', dataIndex: 'name', key: 'name', render: (name: string, factory) => <Link to={`/factories/${factory.id}`}>{name}</Link> },
            { title: 'Контактное лицо', dataIndex: 'contact_person', key: 'contact_person', render: (value) => value ?? '—' },
            { title: 'Телефон', dataIndex: 'phone', key: 'phone', render: (value) => value ?? '—' },
            { title: 'Email', dataIndex: 'email', key: 'email', render: (value) => value ?? '—' },
            { title: 'Основная продукция', dataIndex: 'products', key: 'products', render: (value) => value ?? '—' },
            { title: 'Отправка по умолчанию', dataIndex: 'default_dispatch_method', key: 'default_dispatch_method', render: (value) => value ?? '—' },
            { title: 'Статус', dataIndex: 'status', key: 'status', render: (value: Factory['status']) => <Tag color={value === 'active' ? 'green' : 'default'}>{value === 'active' ? 'Активен' : 'Архивный'}</Tag> },
            ...(canEdit ? [{
              title: 'Действия',
              key: 'actions',
              render: (_: unknown, factory: Factory) => (
                <Space>
                  <Button icon={<EditOutlined />} onClick={() => openEdit(factory)}>Изменить</Button>
                  {factory.status === 'active' && <Button danger onClick={() => Modal.confirm({
                    title: `Архивировать завод «${factory.name}»?`,
                    okText: 'Архивировать',
                    cancelText: 'Отмена',
                    onOk: () => archive(factory),
                  })}>В архив</Button>}
                </Space>
              ),
            }] : []),
          ]}
        />
      </Card>
      <Modal
        title={editing ? 'Редактирование завода' : 'Новый завод'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        okText="Сохранить"
        cancelText="Отмена"
        confirmLoading={saveMutation.isPending}
        width={720}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => saveMutation.mutate(values)}
          initialValues={emptyFactory}
        >
          <div className="form-grid">
            <Form.Item name="name" label="Название завода" rules={[{ required: true, whitespace: true, message: 'Введите название' }]}>
              <Input maxLength={255} />
            </Form.Item>
            <Form.Item name="short_name" label="Краткое название"><Input maxLength={100} /></Form.Item>
            <Form.Item name="contact_person" label="Контактное лицо"><Input /></Form.Item>
            <Form.Item name="phone" label="Телефон"><Input /></Form.Item>
            <Form.Item name="whatsapp" label="WhatsApp"><Input /></Form.Item>
            <Form.Item name="email" label="Email" rules={[{ type: 'email', message: 'Проверьте адрес email' }]}><Input /></Form.Item>
            <Form.Item name="website" label="Сайт"><Input placeholder="https://" /></Form.Item>
            <Form.Item name="address" label="Адрес"><Input /></Form.Item>
            <Form.Item name="products" label="Основная продукция"><Input /></Form.Item>
            <Form.Item name="default_dispatch_method" label="Способ отправки по умолчанию">
              <Select allowClear options={['WhatsApp', 'Почта', 'Сайт'].map((value) => ({ value, label: value }))} />
            </Form.Item>
            <Form.Item name="payment_terms" label="Условия оплаты"><Input /></Form.Item>
            <Form.Item name="production_lead_time_days" label="Срок изготовления, дней"><InputNumber min={0} className="full-width" /></Form.Item>
            <Form.Item name="status" label="Статус">
              <Select options={[{ value: 'active', label: 'Активен' }, { value: 'archived', label: 'Архивный' }]} />
            </Form.Item>
            <Form.Item name="comment" label="Комментарий" className="wide-field"><Input.TextArea rows={3} /></Form.Item>
          </div>
        </Form>
      </Modal>
    </>
  );
}
