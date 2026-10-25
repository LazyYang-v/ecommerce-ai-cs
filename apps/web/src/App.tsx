import { Layout, Menu } from 'antd'
import { MessageSquare, ShoppingBag } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { AppRoutes } from './routes'

export default function App() {
  const location = useLocation()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Header style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        <div style={{ color: '#fff', fontWeight: 600, whiteSpace: 'nowrap' }}>
          电商智能客服 · Phase 1
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={[
            {
              key: '/products',
              icon: <ShoppingBag size={16} />,
              label: <Link to="/products">商品</Link>,
            },
            {
              key: '/chat',
              icon: <MessageSquare size={16} />,
              label: <Link to="/chat">客服测试</Link>,
            },
          ]}
        />
      </Layout.Header>
      <Layout.Content
        style={{ padding: 24, maxWidth: 960, width: '100%', margin: '0 auto' }}
      >
        <AppRoutes />
      </Layout.Content>
    </Layout>
  )
}
