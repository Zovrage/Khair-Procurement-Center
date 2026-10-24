import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { Button, Card, DatePicker, Input, Modal, Select, Space, Spin, Table, Typography, message } from 'antd';
import dayjs from 'dayjs';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest, formatDateTime, type Factory, type ProcurementRequest, type RequestFactory } from '../api/client';

const dispatchOptions = ['WhatsApp', 'Почта', 'Сайт'].map((value) => ({ label: value, value }));

interface AuditEntry {
  id: string;
  action: string;
  actor_id?: string | null;
  details?: string | null;
  created_at: string;
}

export function RequestDetailPage({ canEdit, canViewHistory }: { canEdit: boolean; canViewHistory: boolean }) {
  const { requestId = '' } = useParams();
  const queryClient = useQueryClient();
  const [factoryModal, setFactoryModal] = useState(false);
  const [factoryId, setFactoryId] = useState<string>();
  const [factorySearch, setFactorySearch] = useState('');
  const [newOrderByRelation, setNewOrderByRelation] = useState<Record<string, string>>({});
  const [editingOrder, setEditingOrder] = useState<{ id: string; value: string }>();

  const requestQuery = useQuery({
    queryKey: ['request', requestId],
    queryFn: () => apiRequest<ProcurementRequest & { created_at: string; updated_at: string }>(`/api/v1/requests/${requestId}`),
  });
  const relationQuery = useQuery({
    queryKey: ['request-factories', requestId],
    queryFn: () => apiRequest<RequestFactory[]>(`/api/v1/requests/${requestId}/factories`),
  });
  const factoriesQuery = useQuery({
    queryKey: ['factories', 'active', factorySearch],
    queryFn: () => apiRequest<{ items: Factory[] }>(`/api/v1/factories?active_only=true&page_size=100&q=${encodeURIComponent(factorySearch)}`),
  });
  const historyQuery = useQuery({
    queryKey: ['request-history', requestId],
    queryFn: () => apiRequest<AuditEntry[]>(`/api/v1/requests/${requestId}/history`),
    enabled: canViewHistory,
  });

  const relations = relationQuery.data ?? [];
  const linkedIds = useMemo(() => new Set(relations.map((relation) => relation.factory_id)), [relations]);

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['request', requestId] }),
      queryClient.invalidateQueries({ queryKey: ['request-factories', requestId] }),
      queryClient.invalidateQueries({ queryKey: ['request-history', requestId] }),
      queryClient.invalidateQueries({ queryKey: ['requests'] }),
    ]);
  }

  const addFactoryMutation = useMutation({
    mutationFn: () => apiRequest(`/api/v1/requests/${requestId}/factories`, {
      method: 'POST',
      body: JSON.stringify({ factory_id: factoryId }),
    }),
    onSuccess: async () => {
      message.success('Завод добавлен к заявке');
      setFactoryModal(false);
      setFactoryId(undefined);
      await refresh();
    },
    onError: (error) => message.error(error instanceof Error ? error.message : 'Не удалось добавить завод'),
  });

  const detail = requestQuery.data;
  if (requestQuery.isLoading || relationQuery.isLoading) return <Spin />;
  if (!detail) return <Card title="Заявка не найдена">Не удалось загрузить заявку. <Link to="/">Вернуться к списку</Link></Card>;

  async function updateRelation(relation: RequestFactory, patch: object) {
    try {
      await apiRequest(`/api/v1/request-factories/${relation.id}`, { method: 'PATCH', body: JSON.stringify(patch) });
      message.success('Данные сохранены');
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось сохранить данные');
    }
  }

  async function addOrder(relation: RequestFactory) {
    const orderNumber = (newOrderByRelation[relation.id] ?? '').trim();
    if (!orderNumber) {
      message.warning('Введите номер заказа');
      return;
    }
    try {
      await apiRequest(`/api/v1/request-factories/${relation.id}/order-numbers`, {
        method: 'POST',
        body: JSON.stringify({ order_number: orderNumber }),
      });
      setNewOrderByRelation((current) => ({ ...current, [relation.id]: '' }));
      message.success('Номер заказа добавлен');
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось добавить номер заказа');
    }
  }

  async function deleteOrder(orderNumberId: string) {
    try {
      await apiRequest(`/api/v1/order-numbers/${orderNumberId}`, { method: 'DELETE' });
      message.success('Номер заказа удалён');
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось удалить номер заказа');
    }
  }

  async function saveOrderEdit() {
    if (!editingOrder?.value.trim()) {
      message.warning('Номер заказа не может быть пустым');
      return;
    }
    try {
      await apiRequest(`/api/v1/order-numbers/${editingOrder.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ order_number: editingOrder.value.trim() }),
      });
      setEditingOrder(undefined);
      message.success('Номер заказа обновлён');
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось изменить номер заказа');
    }
  }

  async function deleteRelation(relation: RequestFactory) {
    try {
      await apiRequest(`/api/v1/request-factories/${relation.id}`, { method: 'DELETE' });
      message.success('Связь с заводом удалена');
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Не удалось удалить связь');
    }
  }

  return (
    <Space direction="vertical" size="large" className="full-width">
      <Card
        title={<Space><Link to="/">Центр заявок</Link><span>/</span><span>Заявка №{detail.bitrix_deal_id}</span></Space>}
        extra={detail.bitrix_url ? <Button href={detail.bitrix_url} target="_blank" rel="noreferrer">Открыть в Bitrix24</Button> : null}
      >
        <Typography.Title level={4}>{detail.bitrix_title}</Typography.Title>
        <div className="request-summary">
          <div><Typography.Text type="secondary">ID сделки</Typography.Text><div>{detail.bitrix_deal_id}</div></div>
          <div><Typography.Text type="secondary">Стадия</Typography.Text><div>{detail.bitrix_stage_id ?? '—'}</div></div>
          <div><Typography.Text type="secondary">Ответственный ID</Typography.Text><div>{detail.bitrix_responsible_id ?? '—'}</div></div>
          <div><Typography.Text type="secondary">Создана</Typography.Text><div>{formatDateTime(detail.bitrix_created_at)}</div></div>
        </div>
      </Card>

      <Card title="Заводы" extra={canEdit && <Button type="primary" icon={<PlusOutlined />} onClick={() => setFactoryModal(true)}>Добавить завод</Button>}>
        {relations.length === 0 && <Typography.Text type="secondary">К заявке пока не привязаны заводы.</Typography.Text>}
        <Space direction="vertical" size="middle" className="full-width">
          {relations.map((relation) => (
            <Card
              key={relation.id}
              type="inner"
              title={<Link to={`/factories/${relation.factory_id}`}>{relation.factory_name}</Link>}
              extra={canEdit && <Button danger type="text" icon={<DeleteOutlined />} onClick={() => Modal.confirm({
                title: 'Удалить связь завода с заявкой?',
                content: 'Номера заказов и дата отправки для этой связи также будут удалены.',
                okText: 'Удалить',
                cancelText: 'Отмена',
                onOk: () => deleteRelation(relation),
              })}>Удалить связь</Button>}
            >
              <div className="dispatch-fields">
                <div>
                  <Typography.Text type="secondary">Дата и время отправки</Typography.Text>
                  <DatePicker
                    showTime={{ format: 'HH:mm' }}
                    format="DD.MM.YYYY HH:mm"
                    value={relation.dispatch_datetime ? dayjs(relation.dispatch_datetime) : null}
                    disabled={!canEdit}
                    onChange={(value) => updateRelation(relation, { dispatch_datetime: value?.toISOString() ?? null })}
                    placeholder="Не отправлено"
                  />
                </div>
                <div>
                  <Typography.Text type="secondary">Способ отправки</Typography.Text>
                  <Select
                    options={dispatchOptions}
                    value={relation.dispatch_method ?? undefined}
                    disabled={!canEdit}
                    onChange={(value) => updateRelation(relation, { dispatch_method: value })}
                    placeholder="Выберите способ"
                    allowClear
                  />
                </div>
                <div><Typography.Text type="secondary">Последнее изменение</Typography.Text><div>{formatDateTime(relation.updated_at)}</div></div>
              </div>
              <Typography.Text strong>Номера заказов</Typography.Text>
              <Space wrap className="order-list">
                {(relation.order_number_records ?? []).map((orderNumber) => (
                  <span className="order-chip" key={orderNumber.id}>
                    {orderNumber.order_number}
                    {canEdit && <Button size="small" type="text" onClick={() => setEditingOrder({ id: orderNumber.id, value: orderNumber.order_number })}>Изменить</Button>}
                    {canEdit && <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={() => deleteOrder(orderNumber.id)} aria-label={`Удалить ${orderNumber.order_number}`} />}
                  </span>
                ))}
              </Space>
              {canEdit && (
                <Space.Compact className="order-input">
                  <Input
                    value={newOrderByRelation[relation.id] ?? ''}
                    onChange={(event) => setNewOrderByRelation((current) => ({ ...current, [relation.id]: event.target.value }))}
                    onPressEnter={() => addOrder(relation)}
                    placeholder="Новый номер заказа"
                  />
                  <Button icon={<PlusOutlined />} onClick={() => addOrder(relation)}>Добавить</Button>
                </Space.Compact>
              )}
            </Card>
          ))}
        </Space>
      </Card>
      {canViewHistory && (
        <Card title="История изменений">
          {historyQuery.isError && <Typography.Text type="danger">{historyQuery.error.message}</Typography.Text>}
          <Table
            rowKey="id"
            dataSource={historyQuery.data ?? []}
            loading={historyQuery.isLoading}
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: 'История изменений пока пуста' }}
            columns={[
              { title: 'Время', dataIndex: 'created_at', key: 'created_at', render: formatDateTime },
              { title: 'Действие', dataIndex: 'action', key: 'action' },
              { title: 'Пользователь ID', dataIndex: 'actor_id', key: 'actor_id', render: (value) => value ?? '—' },
              { title: 'Детали', dataIndex: 'details', key: 'details', render: (value) => value ?? '—' },
            ]}
          />
        </Card>
      )}

      <Modal
        title="Добавить завод к заявке"
        open={factoryModal}
        onCancel={() => setFactoryModal(false)}
        onOk={() => addFactoryMutation.mutate()}
        okText="Добавить"
        cancelText="Отмена"
        confirmLoading={addFactoryMutation.isPending}
        okButtonProps={{ disabled: !factoryId }}
      >
        <Select
          showSearch
          optionFilterProp="label"
          className="full-width"
          placeholder="Найдите завод"
          value={factoryId}
          onChange={setFactoryId}
          onSearch={setFactorySearch}
          loading={factoriesQuery.isLoading}
          options={(factoriesQuery.data?.items ?? [])
            .filter((factory) => !linkedIds.has(factory.id))
            .map((factory) => ({ value: factory.id, label: factory.name }))}
        />
      </Modal>
      <Modal
        title="Изменить номер заказа"
        open={Boolean(editingOrder)}
        onCancel={() => setEditingOrder(undefined)}
        onOk={saveOrderEdit}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Input
          value={editingOrder?.value ?? ''}
          onChange={(event) => setEditingOrder((current) => current ? { ...current, value: event.target.value } : current)}
          onPressEnter={saveOrderEdit}
        />
      </Modal>
    </Space>
  );
}
