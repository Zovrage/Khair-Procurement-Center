import { Button, Card, Descriptions, Empty, Table } from 'antd';

const syncLog = [
  { time: '23.10.2026 09:55', message: 'Синхронизация завершена успешно' },
  { time: '23.10.2026 08:40', message: 'Повторная обработка сделки 1542' },
];

export function SettingsPage() {
  return (
    <Card title="Настройки интеграции">
      <Descriptions bordered column={2}>
        <Descriptions.Item label="Состояние подключения">Готово</Descriptions.Item>
        <Descriptions.Item label="Идентификатор воронки">Закупка и отгрузка</Descriptions.Item>
        <Descriptions.Item label="Последняя синхронизация">23.10.2026 12:00</Descriptions.Item>
        <Descriptions.Item label="Статус">Активна</Descriptions.Item>
      </Descriptions>
      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
        <Button type="primary">Проверить подключение</Button>
        <Button>Ручная синхронизация</Button>
      </div>
      <Table style={{ marginTop: 20 }} dataSource={syncLog} rowKey="time" columns={[{ title: 'Время', dataIndex: 'time', key: 'time' }, { title: 'Событие', dataIndex: 'message', key: 'message' }]} pagination={false} />
    </Card>
  );
}
