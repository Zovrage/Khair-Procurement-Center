import { Button, Card, Descriptions, Spin, Table, Typography } from 'antd';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, formatDateTime, type Factory } from '../api/client';

interface FactoryRequest {
  id: string;
  bitrix_deal_id: string;
  bitrix_title: string;
  factory_order_numbers: string[];
  dispatch_datetime?: string | null;
  dispatch_method?: string | null;
}

interface AuditEntry {
  id: string;
  action: string;
  actor_id?: string | null;
  details?: string | null;
  created_at: string;
}

export function FactoryDetailPage({ canViewHistory }: { canViewHistory: boolean }) {
  const { factoryId = '' } = useParams();
  const factoryQuery = useQuery({
    queryKey: ['factory', factoryId],
    queryFn: () => apiRequest<Factory>(`/api/v1/factories/${factoryId}`),
  });
  const relatedQuery = useQuery({
    queryKey: ['factory-requests', factoryId],
    queryFn: () => apiRequest<FactoryRequest[]>(`/api/v1/factories/${factoryId}/requests`),
  });
  const historyQuery = useQuery({
    queryKey: ['factory-history', factoryId],
    queryFn: () => apiRequest<AuditEntry[]>(`/api/v1/factories/${factoryId}/history`),
    enabled: canViewHistory,
  });
  if (factoryQuery.isLoading) return <Spin />;
  if (!factoryQuery.data) return <Card>Завод не найден</Card>;
  const factory = factoryQuery.data;
  return (
    <Card title={<Link to="/factories">Заводы</Link>}>
      <Typography.Title level={3}>{factory.name}</Typography.Title>
      <Descriptions bordered column={{ xs: 1, md: 2 }}>
        <Descriptions.Item label="Краткое название">{factory.short_name ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Статус">{factory.status === 'active' ? 'Активен' : 'Архивный'}</Descriptions.Item>
        <Descriptions.Item label="Контактное лицо">{factory.contact_person ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Телефон">{factory.phone ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="WhatsApp">{factory.whatsapp ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Email">{factory.email ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Сайт">{factory.website ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Адрес">{factory.address ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Продукция">{factory.products ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Отправка по умолчанию">{factory.default_dispatch_method ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Условия оплаты">{factory.payment_terms ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Срок изготовления">{factory.production_lead_time_days != null ? `${factory.production_lead_time_days} дн.` : '—'}</Descriptions.Item>
        <Descriptions.Item label="Комментарий">{factory.comment ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Создан">{formatDateTime(factory.created_at)}</Descriptions.Item>
        <Descriptions.Item label="Изменён">{formatDateTime(factory.updated_at)}</Descriptions.Item>
      </Descriptions>
      <Typography.Title level={4} style={{ marginTop: 24 }}>Связанные заявки</Typography.Title>
      {relatedQuery.isError && <Typography.Text type="danger">{relatedQuery.error.message}</Typography.Text>}
      <Table
        rowKey="id"
        dataSource={relatedQuery.data ?? []}
        loading={relatedQuery.isLoading}
        columns={[
          { title: 'ID сделки', dataIndex: 'bitrix_deal_id', key: 'deal', render: (id, request) => <Link to={`/requests/${request.id}`}>№{id}</Link> },
          { title: 'Название', dataIndex: 'bitrix_title', key: 'title' },
          { title: 'Дата отправки', dataIndex: 'dispatch_datetime', key: 'dispatch_datetime', render: formatDateTime },
          { title: 'Номера заказов', dataIndex: 'factory_order_numbers', key: 'orders', render: (values: string[]) => values?.join(', ') || '—' },
          { title: 'Способ отправки', dataIndex: 'dispatch_method', key: 'method', render: (value) => value ?? '—' },
          { title: '', key: 'link', render: (_, request) => <Link to={`/requests/${request.id}`}>Открыть заявку</Link> },
        ]}
      />
      {canViewHistory && (
        <>
          <Typography.Title level={4} style={{ marginTop: 24 }}>История изменений</Typography.Title>
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
        </>
      )}
    </Card>
  );
}
