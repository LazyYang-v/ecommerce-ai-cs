import { useMutation } from '@tanstack/react-query'
import { Card, Input, List, Typography } from 'antd'
import { useState } from 'react'
import { sendTestMessage } from '../api/chat'

interface ChatBubble {
  role: 'user' | 'agent'
  content: string
  requestId?: string | null
}

export default function ChatTestPage() {
  const [message, setMessage] = useState('')
  const [bubbles, setBubbles] = useState<ChatBubble[]>([])

  const mutation = useMutation({
    mutationFn: sendTestMessage,
    onSuccess: (data) => {
      setBubbles((prev) => [
        ...prev,
        { role: 'agent', content: data.response, requestId: data.request_id },
      ])
    },
    onError: (err) => {
      setBubbles((prev) => [
        ...prev,
        { role: 'agent', content: `调用失败：${(err as Error).message}` },
      ])
    },
  })

  const send = () => {
    const text = message.trim()
    if (!text || mutation.isPending) return
    setBubbles((prev) => [...prev, { role: 'user', content: text }])
    mutation.mutate(text)
    setMessage('')
  }

  return (
    <Card title="客服链路测试（前端 → Business API → Agent → Business API → 前端）">
      <List
        dataSource={bubbles}
        locale={{ emptyText: '发送一条消息试试，例如：我的订单在哪里？' }}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={item.role === 'user' ? '我' : '客服（Agent 测试响应）'}
              description={
                <>
                  <div>{item.content}</div>
                  {item.requestId && (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      request_id: {item.requestId}
                    </Typography.Text>
                  )}
                </>
              }
            />
          </List.Item>
        )}
      />
      <Input.Search
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onSearch={send}
        placeholder="输入消息"
        enterButton="发送"
        loading={mutation.isPending}
        disabled={mutation.isPending}
      />
      <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
        Phase 1 的 Agent 返回确定性测试响应（LangGraph 最小图），Phase 2 接入 DeepSeek 后为真实回复。
      </Typography.Text>
    </Card>
  )
}
