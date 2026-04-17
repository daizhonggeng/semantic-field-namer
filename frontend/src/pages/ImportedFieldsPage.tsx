import { useState } from 'react'
import { Button, Card, Form, Input, Modal, Table, Tag, Typography, message } from 'antd'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { importApi } from '../api/client'
import type { ImportedField } from '../types/api'

type EditValues = {
  table_name: string
  column_name: string
  column_comment_zh?: string
  data_type?: string
}

export function ImportedFieldsPage() {
  const { projectId = '' } = useParams()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<EditValues>()
  const [editingField, setEditingField] = useState<ImportedField | null>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['imported-fields', projectId],
    queryFn: () => importApi.fields(projectId),
  })

  return (
    <>
      {contextHolder}
      <Card
        title="已导入表结构"
        extra={<Typography.Text type="secondary">支持修改表名、字段名、中文注释和数据类型</Typography.Text>}
      >
        <Table<ImportedField>
          loading={isLoading}
          rowKey={(record) => record.id}
          dataSource={data || []}
          pagination={{ pageSize: 12 }}
          columns={[
            { title: '表名', dataIndex: 'table_name', width: 180 },
            { title: '字段名', dataIndex: 'column_name', width: 220 },
            {
              title: '中文注释',
              dataIndex: 'column_comment_zh',
              render: (value) => value || <Tag color="default">无</Tag>,
            },
            {
              title: '归一化语义',
              dataIndex: 'canonical_comment_zh',
              render: (value) => value || <Tag color="warning">未入语义池</Tag>,
            },
            { title: '类型', dataIndex: 'data_type', width: 160 },
            {
              title: '操作',
              width: 100,
              render: (_, record) => (
                <Button
                  size="small"
                  onClick={() => {
                    setEditingField(record)
                    form.setFieldsValue({
                      table_name: record.table_name,
                      column_name: record.column_name,
                      column_comment_zh: record.column_comment_zh || undefined,
                      data_type: record.data_type || undefined,
                    })
                  }}
                >
                  编辑
                </Button>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title="编辑导入字段"
        open={!!editingField}
        onCancel={() => {
          setEditingField(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            if (!editingField) return
            try {
              await importApi.updateField(projectId, editingField.id, values)
              messageApi.success('字段已更新')
              setEditingField(null)
              form.resetFields()
              await queryClient.invalidateQueries({ queryKey: ['imported-fields', projectId] })
            } catch {
              messageApi.error('字段更新失败')
            }
          }}
        >
          <Form.Item name="table_name" label="表名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="column_name" label="字段名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="column_comment_zh" label="中文注释">
            <Input />
          </Form.Item>
          <Form.Item name="data_type" label="数据类型">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
