import { Button, Card, Table, Tag } from 'antd';

const sampleFactories = [
  { id: '1', name: 'Краснодарский завод кровельных материалов', contact: 'Иван Петров', phone: '+7 (861) 111-22-33', email: 'sales@kzkm.ru', products: 'Металлочерепица', status: 'Активен' },
  { id: '2', name: 'Екатеринбургский завод металлопроката', contact: 'Ольга Смирнова', phone: '+7 (343) 333-44-55', email: 'sales@ezm.ru', products: 'Профлист', status: 'Архивный' },
];

export function FactoriesPage() {
  return (
    <Card title="Заводы" extra={<Button type="primary">Добавить завод</Button>}>
      <Table
        dataSource={sampleFactories}
        rowKey="id"
        columns={[
          { title: 'Название', dataIndex: 'name', key: 'name' },
          { title: 'Контактное лицо', dataIndex: 'contact', key: 'contact' },
          { title: 'Телефон', dataIndex: 'phone', key: 'phone' },
          { title: 'Email', dataIndex: 'email', key: 'email' },
          { title: 'Основная продукция', dataIndex: 'products', key: 'products' },
          { title: 'Статус', dataIndex: 'status', key: 'status', render: (value) => <Tag color={value === 'Активен' ? 'green' : 'default'}>{value}</Tag> },
        ]}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
}
