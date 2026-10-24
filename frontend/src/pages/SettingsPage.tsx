import { ReloadOutlined, SyncOutlined } from '@ant-design/icons';
import { Button, Card, Descriptions, Space, Table, Tag, Typography, message } from 'antd';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest, formatDateTime } from '../api/client';

interface IntegrationStatus {
  configured: boolean;
  demo_mode: boolean;
  portal_url?: string | null;
  pipeline_id?: string | null;
  last_sync_at?: string | null;
  credentials_configured: boolean;
  timezone: string;
}

interface SyncLog {
  id: string;
  status: string;
  message?: string | null;
  created_at: string;
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const statusQuery = useQuery({
    queryKey: ['integration-status'],
    queryFn: () => apiRequest<IntegrationStatus>('/api/v1/integrations/bitrix24/status'),
  });
  const logQuery = useQuery({
    queryKey: ['integration-log'],
    queryFn: () => apiRequest<SyncLog[]>('/api/v1/integrations/bitrix24/events'),
  });
  const syncMutation = useMutation({
    mutationFn: () => apiRequest<{ message: string }>('/api/v1/integrations/bitrix24/sync', { method: 'POST' }),
    onSuccess: async (result) => {
      message.success(result.message);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['integration-status'] }),
        queryClient.invalidateQueries({ queryKey: ['integration-log'] }),
        queryClient.invalidateQueries({ queryKey: ['requests'] }),
      ]);
    },
    onError: (error) => message.error(error instanceof Error ? error.message : 'Не удалось синхронизировать Bitrix24'),
  });

  const status = statusQuery.data;
  return (
    <Card title={<div><Typography.Title level={3} style={{ margin: 0 }}>Настройки интеграции</Typography.Title><Typography.Text type="secondary">Параметры Bitrix24 задаются на сервере через .env</Typography.Text></div>}>
      {statusQuery.isError && <Typography.Text type="danger">{statusQuery.error.message}</Typography.Text>}
      <Descriptions bordered column={{ xs: 1, md: 2 }} style={{ marginTop: 16 }}>
        <Descriptions.Item label="Состояние подключения">
          <Tag color={status?.configured ? 'green' : 'orange'}>{status?.configured ? 'Настроено' : 'Не настроено'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Демо-режим">{status?.demo_mode ? 'Включён' : 'Выключен'}</Descriptions.Item>
        <Descriptions.Item label="Портал">{status?.portal_url ?? 'Не указан'}</Descriptions.Item>
        <Descriptions.Item label="ID воронки">{status?.pipeline_id ?? 'Не указан'}</Descriptions.Item>
        <Descriptions.Item label="Входящий вебхук">{status?.credentials_configured ? 'Настроен (значение скрыто)' : 'Не настроен'}</Descriptions.Item>
        <Descriptions.Item label="Часовой пояс">{status?.timezone ?? 'Europe/Moscow'}</Descriptions.Item>
        <Descriptions.Item label="Последняя синхронизация">{formatDateTime(status?.last_sync_at)}</Descriptions.Item>
      </Descriptions>
      {!status?.configured && (
        <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
          Для подключения задайте на сервере <Typography.Text code>BITRIX_WEBHOOK_URL</Typography.Text>, <Typography.Text code>BITRIX_PORTAL_URL</Typography.Text> и <Typography.Text code>BITRIX_DEAL_PIPELINE_ID</Typography.Text>, затем перезапустите backend. Секрет вебхука не передаётся в браузер.
        </Typography.Paragraph>
      )}
      <Space style={{ marginTop: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={() => statusQuery.refetch()} loading={statusQuery.isFetching}>Проверить настройки</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={() => syncMutation.mutate()} loading={syncMutation.isPending} disabled={!status?.configured}>
          Синхронизировать сейчас
        </Button>
      </Space>
      <Typography.Title level={4} style={{ marginTop: 28 }}>Журнал синхронизаций</Typography.Title>
      {logQuery.isError && <Typography.Text type="danger">{logQuery.error.message}</Typography.Text>}
      <Table
        rowKey="id"
        dataSource={logQuery.data ?? []}
        loading={logQuery.isLoading}
        pagination={false}
        locale={{ emptyText: 'Записей о синхронизации пока нет' }}
        columns={[
          { title: 'Время', dataIndex: 'created_at', key: 'created_at', render: formatDateTime },
          { title: 'Статус', dataIndex: 'status', key: 'status', render: (value: string) => <Tag color={value === 'success' ? 'green' : 'red'}>{value === 'success' ? 'Успешно' : 'Ошибка'}</Tag> },
          { title: 'Сообщение', dataIndex: 'message', key: 'message', render: (value?: string | null) => value ?? '—' },
        ]}
      />
    </Card>
  );
}
