import { Button, Card, Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const sampleData = [
  {
    id: 1542,
    title: 'Склад в Новороссийске',
    client: 'ООО Восход',
    manager: 'Анна Смирнова',
    createdAt: '23.10.2026 09:40',
    stage: 'Закупка и отгрузка',
    factoriesCount: 2,
    lastDispatch: '23.10.2026 11:15',
    completeness: 'Готово',
  },
  {
    id: 1688,
    title: 'Торговый комплекс Крым',
    client: 'ООО КрымМеталл',
    manager: 'Алексей Федоров',
    createdAt: '25.10.2026 12:00',
    stage: 'Подбор поставщика',
    factoriesCount: 1,
    lastDispatch: null,
    completeness: 'Не заполнено',
  },
];

const columns: ColumnsType<typeof sampleData[number]> = [
  { title: 'ID заявки', dataIndex: 'id', key: 'id' },
  { title: 'Название сделки', dataIndex: 'title', key: 'title' },
  { title: 'Клиент', dataIndex: 'client', key: 'client' },
  { title: 'Ответственный', dataIndex: 'manager', key: 'manager' },
  { title: 'Дата создания', dataIndex: 'createdAt', key: 'createdAt' },
  { title: 'Стадия', dataIndex: 'stage', key: 'stage' },
  { title: 'Заводы', dataIndex: 'factoriesCount', key: 'factoriesCount' },
  { title: 'Последняя отправка', dataIndex: 'lastDispatch', key: 'lastDispatch', render: (value) => value ?? '—' },
  { title: 'Заполненность', dataIndex: 'completeness', key: 'completeness', render: (value) => <Tag color={value === 'Готово' ? 'green' : 'orange'}>{value}</Tag> },
];

export function RequestsPage() {
  return (
    <Card title="Центр заявок" extra={<Button type="primary">Обновить</Button>}>
      <Table dataSource={sampleData} columns={columns} rowKey="id" pagination={{ pageSize: 10 }} />
    </Card>
  );
}
