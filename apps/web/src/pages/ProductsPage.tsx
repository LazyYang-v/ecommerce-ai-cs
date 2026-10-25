import { useQuery } from '@tanstack/react-query'
import { Card, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useState } from 'react'
import { getProducts, type Product } from '../api/products'

export default function ProductsPage() {
  const [page, setPage] = useState(1)

  const { data, isPending, error } = useQuery({
    queryKey: ['products', page],
    queryFn: () => getProducts(page),
  })

  const columns: ColumnsType<Product> = [
    { title: '商品名称', dataIndex: 'name', key: 'name' },
    {
      title: '价格（元）',
      dataIndex: 'price',
      key: 'price',
      width: 120,
      align: 'right',
    },
    { title: '库存', dataIndex: 'stock', key: 'stock', width: 100, align: 'right' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) =>
        status === 'on_sale' ? <Tag color="green">在售</Tag> : <Tag>下架</Tag>,
    },
  ]

  return (
    <Card title="商品列表（数据来自 Business API）">
      {error && <p>加载失败：{(error as Error).message}</p>}
      <Table<Product>
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={isPending}
        pagination={{
          total: data?.total ?? 0,
          pageSize: data?.page_size ?? 20,
          current: page,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 件商品`,
        }}
      />
    </Card>
  )
}
