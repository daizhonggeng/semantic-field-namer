import { Badge, Card, Space, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'

import { systemApi } from '../api/client'

export function AIStatusBadge() {
  const { data } = useQuery({
    queryKey: ['ai-health'],
    queryFn: systemApi.aiHealth,
    refetchInterval: 30_000,
  })

  const status = !data?.configured ? 'default' : data.reachable ? 'success' : 'error'
  const text = !data?.configured
    ? 'AI 未配置'
    : data.reachable
      ? `AI 已连接 · ${data.model}`
      : `AI 不可用 · ${data.model}`
  const detail = !data?.configured
    ? '未配置 AI 网关'
    : data.reachable
      ? `当前来源：${data.source_name || '默认来源'}`
      : '第三方 AI 网关不可用'

  return (
    <Card size="small" styles={{ body: { padding: '8px 12px' } }}>
      <Space align="start" size={12}>
        <Space direction="vertical" size={2}>
          <Badge status={status} text={text} />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {detail}
          </Typography.Text>
        </Space>
      </Space>
    </Card>
  )
}
