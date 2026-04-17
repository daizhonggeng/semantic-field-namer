import { useMemo, useState } from 'react'
import { Button, Card, Checkbox, Col, Form, Input, InputNumber, Modal, Popconfirm, Row, Space, Table, Tag, Typography, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { systemApi } from '../api/client'
import type { AIConfigSource } from '../types/api'

type AIFormValues = {
  name: string
  provider_type: 'openai_compatible'
  base_url: string
  api_key?: string
  model: string
  timeout_seconds: number
  max_retries: number
  is_active: boolean
}

export function AISettingsPage() {
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [form] = Form.useForm<AIFormValues>()
  const [editingSource, setEditingSource] = useState<AIConfigSource | null>(null)
  const [open, setOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['ai-sources'],
    queryFn: systemApi.listAiSources,
  })

  const sources = data || []
  const activeSource = useMemo(() => sources.find((item) => item.is_active) || null, [sources])

  const openCreate = () => {
    setEditingSource(null)
    form.setFieldsValue({
      name: '',
      provider_type: 'openai_compatible',
      base_url: '',
      api_key: '',
      model: 'gpt-5.4',
      timeout_seconds: 30,
      max_retries: 2,
      is_active: !activeSource,
    })
    setOpen(true)
  }

  const openEdit = (source: AIConfigSource) => {
    setEditingSource(source)
    form.setFieldsValue({
      name: source.name,
      provider_type: 'openai_compatible',
      base_url: source.base_url,
      api_key: '',
      model: source.model,
      timeout_seconds: source.timeout_seconds,
      max_retries: source.max_retries,
      is_active: source.is_active,
    })
    setOpen(true)
  }

  return (
    <>
      {contextHolder}
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card
          title="AI 配置"
          extra={
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              新增来源
            </Button>
          }
        >
          <Space direction="vertical" size={8}>
            <Typography.Text strong>
              当前来源：{activeSource ? `${activeSource.name} · ${activeSource.model}` : '未配置'}
            </Typography.Text>
            <Typography.Text type="secondary">
              当前仅支持 OpenAI 兼容格式来源，可配置多个并切换默认来源。
            </Typography.Text>
          </Space>
        </Card>

        <Row gutter={[16, 16]}>
          {sources.map((source) => (
            <Col xs={24} xl={12} key={source.id}>
              <Card
                title={
                  <Space>
                    <Typography.Text strong>{source.name}</Typography.Text>
                    {source.is_active ? <Tag color="green">当前启用</Tag> : null}
                    {source.is_readonly ? <Tag>只读</Tag> : null}
                  </Space>
                }
                extra={<Tag>{source.provider_type}</Tag>}
              >
                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                  <Typography.Text type="secondary">模型：{source.model}</Typography.Text>
                  <Typography.Text type="secondary">地址：{source.base_url}</Typography.Text>
                  <Typography.Text type="secondary">Key：{source.api_key_masked}</Typography.Text>
                  <Typography.Text type="secondary">
                    超时 / 重试：{source.timeout_seconds}s / {source.max_retries}
                  </Typography.Text>
                  <Space wrap>
                    {!source.is_active ? (
                      <Button
                        onClick={async () => {
                          try {
                            await systemApi.activateAiSource(source.id)
                            messageApi.success('已切换默认来源')
                            await queryClient.invalidateQueries({ queryKey: ['ai-sources'] })
                            await queryClient.invalidateQueries({ queryKey: ['ai-health'] })
                          } catch {
                            messageApi.error('切换默认来源失败')
                          }
                        }}
                      >
                        设为默认
                      </Button>
                    ) : null}
                    {!source.is_readonly ? <Button onClick={() => openEdit(source)}>编辑</Button> : null}
                    {!source.is_readonly ? (
                      <Popconfirm
                        title="确认删除该来源？"
                        description="删除后将无法继续使用该来源。"
                        okText="确认删除"
                        cancelText="取消"
                        onConfirm={async () => {
                          try {
                            await systemApi.deleteAiSource(source.id)
                            messageApi.success('来源已删除')
                            await queryClient.invalidateQueries({ queryKey: ['ai-sources'] })
                            await queryClient.invalidateQueries({ queryKey: ['ai-health'] })
                          } catch {
                            messageApi.error('删除来源失败')
                          }
                        }}
                      >
                        <Typography.Link type="danger">删除</Typography.Link>
                      </Popconfirm>
                    ) : null}
                  </Space>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>

        <Card title="来源列表">
          <Table<AIConfigSource>
            loading={isLoading}
            rowKey="id"
            dataSource={sources}
            pagination={false}
            columns={[
              { title: '名称', dataIndex: 'name' },
              { title: '格式', dataIndex: 'provider_type' },
              { title: '模型', dataIndex: 'model' },
              {
                title: '默认',
                dataIndex: 'is_active',
                render: (value) => (value ? <Tag color="green">是</Tag> : <Tag>否</Tag>),
              },
              { title: '地址', dataIndex: 'base_url' },
            ]}
          />
        </Card>
      </Space>

      <Modal
        title={editingSource ? '编辑 AI 来源' : '新增 AI 来源'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            try {
              if (editingSource) {
                await systemApi.updateAiSource(editingSource.id, values)
                messageApi.success('AI 来源已更新')
              } else {
                if (!values.api_key) {
                  messageApi.error('请填写 API Key')
                  return
                }
                await systemApi.createAiSource({ ...values, api_key: values.api_key })
                messageApi.success('AI 来源已新增')
              }
              setOpen(false)
              await queryClient.invalidateQueries({ queryKey: ['ai-sources'] })
              await queryClient.invalidateQueries({ queryKey: ['ai-health'] })
            } catch {
              messageApi.error(editingSource ? 'AI 来源更新失败' : 'AI 来源新增失败')
            }
          }}
        >
          <Form.Item name="name" label="来源名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="provider_type" label="格式" initialValue="openai_compatible">
            <Input disabled />
          </Form.Item>
          <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item
            name="api_key"
            label={editingSource ? 'API Key（留空则保持不变）' : 'API Key'}
            rules={editingSource ? [] : [{ required: true }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item name="model" label="模型" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="timeout_seconds" label="超时（秒）" rules={[{ required: true }]}>
            <InputNumber min={1} max={300} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="max_retries" label="重试次数" rules={[{ required: true }]}>
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_active" valuePropName="checked">
            <Checkbox>设为默认来源</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
