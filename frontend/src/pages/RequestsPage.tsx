import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import { Button, Card, DatePicker, Input, Select, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, formatDateTime, type Factory, type ProcurementRequest } from '../api/client';

interface RequestListResponse {
  items: ProcurementRequest[];
  total: number;
  page: number;
  page_size: number;
}

interface RequestFilters {
  stages: string[];
  responsible_ids: string[];
}

interface FactoryOptions {
  items: Factory[];
}

export function RequestsPage({ canViewHistory }: { canViewHistory: boolean }) {
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [factoryId, setFactoryId] = useState<string>();
  const [completed, setCompleted] = useState<string>();
  const [stage, setStage] = useState<string>();
  const [responsibleId, setResponsibleId] = useState<string>();
  const [dateRange, setDateRange] = useState<[string, string]>();
  const [history, setHistory] = useState(false);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<{ field: string; order: string }>({ field: 'created_at', order: 'desc' });
  const factoriesQuery = useQuery({
    queryKey: ['factories', 'active'],
    queryFn: () => apiRequest<FactoryOptions>('/api/v1/factories?active_only=true&page_size=100'),
  });
  const filtersQuery = useQuery({
    queryKey: ['request-filters'],
    queryFn: () => apiRequest<RequestFilters>('/api/v1/request-filters'),
  });
  const requestsQuery = useQuery({
    queryKey: ['requests', search, factoryId, completed, stage, responsibleId, dateRange, page, sort, history],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: '20', sort_by: sort.field, sort_order: sort.order });
      if (search) params.set('q', search);
      if (factoryId) params.set('factory_id', factoryId);
      if (completed) params.set('only_completed', String(completed === 'complete'));
      if (stage) params.set('stage', stage);
      if (responsibleId) params.set('responsible_id', responsibleId);
      if (dateRange) {
        params.set('from_date', dateRange[0]);
        params.set('to_date', dateRange[1]);
      }
      if (history) params.set('history', 'true');
      return apiRequest<RequestListResponse>(`/api/v1/requests?${params.toString()}`);
    },
  });

  const columns: ColumnsType<ProcurementRequest> = [
    {
      title: 'ID заявки',
      dataIndex: 'bitrix_deal_id',
      key: 'bitrix_deal_id',
      sorter: true,
      render: (_, item) => <Link to={`/requests/${item.id}`}>№{item.bitrix_deal_id}</Link>,
    },
    {
      title: 'Название сделки',
      dataIndex: 'bitrix_title',
      key: 'title',
      sorter: true,
      render: (title: string, item) => <Link to={`/requests/${item.id}`}>{title}</Link>,
    },
    { title: 'Ответственный (ID)', dataIndex: 'bitrix_responsible_id', key: 'responsible', render: (value) => value ?? '—' },
    { title: 'Дата создания', dataIndex: 'bitrix_created_at', key: 'created_at', sorter: true, render: formatDateTime },
    { title: 'Стадия', dataIndex: 'bitrix_stage_id', key: 'stage', render: (value) => value ?? '—' },
    { title: 'Заводы', dataIndex: 'factories_count', key: 'factories_count', align: 'center' },
    { title: 'Последняя отправка', dataIndex: 'last_dispatch', key: 'last_dispatch', render: formatDateTime },
    {
      title: 'Заполненность',
      dataIndex: 'procurement_complete',
      key: 'procurement_complete',
      render: (complete: boolean) => <Tag color={complete ? 'green' : 'orange'}>{complete ? 'Заполнено' : 'Не заполнено'}</Tag>,
    },
    {
      title: 'Bitrix24',
      dataIndex: 'bitrix_url',
      key: 'bitrix_url',
      render: (url?: string | null) => url ? <Button size="small" href={url} target="_blank" rel="noreferrer">Открыть</Button> : '—',
    },
  ];

  function onTableChange(pagination: TablePaginationConfig, _filters: unknown, sorter: unknown) {
    const item = Array.isArray(sorter) ? sorter[0] : sorter as { field?: string; order?: string };
    setPage(pagination.current ?? 1);
    if (item?.field === 'title' || item?.field === 'created_at') {
      setSort({ field: item.field, order: item.order === 'ascend' ? 'asc' : 'desc' });
    }
  }

  return (
    <Card
      title={<div><Typography.Title level={3} style={{ margin: 0 }}>{history ? 'История заявок' : 'Центр заявок'}</Typography.Title><Typography.Text type="secondary">Заявки закупки из CRM</Typography.Text></div>}
      extra={<Button icon={<ReloadOutlined />} onClick={() => requestsQuery.refetch()} loading={requestsQuery.isFetching}>Обновить</Button>}
    >
      <Space wrap className="request-filters">
        {canViewHistory && (
          <Button type={history ? 'primary' : 'default'} onClick={() => { setHistory((value) => !value); setPage(1); }}>
            {history ? 'Показать активные' : 'История'}
          </Button>
        )}
        <Input.Search
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onSearch={(value) => { setPage(1); setSearch(value.trim()); }}
          onPressEnter={() => { setPage(1); setSearch(query.trim()); }}
          prefix={<SearchOutlined />}
          placeholder="Поиск по названию или ID"
          allowClear
          style={{ width: 300 }}
        />
        <Select
          allowClear
          placeholder="Все заводы"
          style={{ width: 250 }}
          value={factoryId}
          onChange={(value) => { setFactoryId(value); setPage(1); }}
          options={(factoriesQuery.data?.items ?? []).map((factory) => ({ value: factory.id, label: factory.name }))}
        />
        <Select
          allowClear
          placeholder="Все стадии"
          style={{ width: 200 }}
          value={stage}
          onChange={(value) => { setStage(value); setPage(1); }}
          options={(filtersQuery.data?.stages ?? []).map((value) => ({ value, label: value }))}
        />
        <Select
          allowClear
          placeholder="Все ответственные"
          style={{ width: 200 }}
          value={responsibleId}
          onChange={(value) => { setResponsibleId(value); setPage(1); }}
          options={(filtersQuery.data?.responsible_ids ?? []).map((value) => ({ value, label: `ID ${value}` }))}
        />
        <DatePicker.RangePicker
          format="DD.MM.YYYY"
          placeholder={['Дата с', 'Дата по']}
          onChange={(dates) => {
            if (!dates?.[0] || !dates[1]) {
              setDateRange(undefined);
            } else {
              setDateRange([dates[0].startOf('day').toISOString(), dates[1].endOf('day').toISOString()]);
            }
            setPage(1);
          }}
        />
        <Select
          allowClear
          placeholder="Все статусы заполнения"
          style={{ width: 220 }}
          value={completed}
          onChange={(value) => { setCompleted(value); setPage(1); }}
          options={[{ value: 'complete', label: 'Заполнено' }, { value: 'incomplete', label: 'Не заполнено' }]}
        />
      </Space>
      {requestsQuery.isError && <Typography.Text type="danger" className="error-text">{requestsQuery.error.message}</Typography.Text>}
      <Table
        rowKey="id"
        dataSource={requestsQuery.data?.items ?? []}
        columns={columns}
        loading={requestsQuery.isLoading || requestsQuery.isFetching}
        onChange={onTableChange}
        pagination={{
          current: page,
          pageSize: requestsQuery.data?.page_size ?? 20,
          total: requestsQuery.data?.total ?? 0,
          showSizeChanger: false,
          showTotal: (total) => `Всего: ${total}`,
        }}
        locale={{ emptyText: requestsQuery.isError ? 'Не удалось загрузить заявки' : 'Заявок пока нет' }}
        scroll={{ x: 1100 }}
      />
    </Card>
  );
}
