import { useState } from 'react'
import { Button, Card, Modal, Space, Table, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { generationApi } from '../api/client'
import type { HistoryItem } from '../types/api'

function formatDateTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  const hours = `${date.getHours()}`.padStart(2, '0')
  const minutes = `${date.getMinutes()}`.padStart(2, '0')
  const seconds = `${date.getSeconds()}`.padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

export function HistoryPage() {
  const { projectId = '' } = useParams()
  const [selectedHistory, setSelectedHistory] = useState<HistoryItem | null>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['history', projectId],
    queryFn: () => generationApi.history(projectId),
  })

  const buildSummaryPreview = (summary: Record<string, unknown>) => {
    const total = summary.total ?? '-'
    const breakdown =
      summary.source_breakdown && typeof summary.source_breakdown === 'object'
        ? Object.entries(summary.source_breakdown as Record<string, number>)
            .map(([key, value]) => `${key}:${value}`)
            .join(' / ')
        : '-'
    return `总数 ${total} · 来源 ${breakdown}`
  }

  const downloadSql = (record: HistoryItem) => {
    const generatedSql =
      record.summary && typeof record.summary.generated_sql === 'string'
        ? record.summary.generated_sql
        : ''
    if (!generatedSql) {
      return
    }
    const blob = new Blob([generatedSql], { type: 'text/sql;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${record.table_name}_${record.id}.sql`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <Card title="生成历史">
        <Table
          loading={isLoading}
          rowKey="id"
          dataSource={data || []}
          columns={[
            { title: '批次 ID', dataIndex: 'id' },
            { title: '表名', dataIndex: 'table_name' },
            { title: '创建时间', dataIndex: 'created_at', render: (value) => formatDateTime(value) },
            {
              title: '摘要',
              dataIndex: 'summary',
              render: (value) => (
                <Typography.Text ellipsis={{ tooltip: buildSummaryPreview(value) }}>
                  {buildSummaryPreview(value)}
                </Typography.Text>
              ),
            },
            {
              title: '操作',
              render: (_, record) => (
                <Space>
                  <Button size="small" onClick={() => setSelectedHistory(record)}>
                    展开
                  </Button>
                  <Button
                    size="small"
                    onClick={() => downloadSql(record)}
                    disabled={!record.summary || typeof record.summary.generated_sql !== 'string'}
                  >
                    下载 SQL
                  </Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title={selectedHistory ? `历史详情 #${selectedHistory.id}` : '历史详情'}
        open={!!selectedHistory}
        onCancel={() => setSelectedHistory(null)}
        footer={null}
        width={860}
      >
        {selectedHistory ? (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Typography.Text type="secondary">表名</Typography.Text>
              <div>{selectedHistory.table_name}</div>
            </div>
            <div>
              <Typography.Text type="secondary">创建时间</Typography.Text>
              <div>{formatDateTime(selectedHistory.created_at)}</div>
            </div>
            <div>
              <Typography.Text type="secondary">摘要</Typography.Text>
              <pre style={{ whiteSpace: 'pre-wrap', margin: '8px 0 0' }}>
                {JSON.stringify(selectedHistory.summary, null, 2)}
              </pre>
            </div>
            <div>
              <Typography.Text type="secondary">建表 SQL</Typography.Text>
              <pre style={{ whiteSpace: 'pre-wrap', margin: '8px 0 0' }}>
                {typeof selectedHistory.summary.generated_sql === 'string'
                  ? selectedHistory.summary.generated_sql
                  : '该历史记录还没有保存建表 SQL'}
              </pre>
            </div>
            <div>
              <Button
                onClick={() => downloadSql(selectedHistory)}
                disabled={typeof selectedHistory.summary.generated_sql !== 'string'}
              >
                下载 SQL
              </Button>
            </div>
          </Space>
        ) : null}
      </Modal>
    </>
  )
}
