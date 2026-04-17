import {
  DatabaseOutlined,
  DeleteOutlined,
  EditOutlined,
  NodeIndexOutlined,
  PlusOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { Button, Empty, Form, Input, Modal, Popconfirm, Space, Tag, Typography, message } from 'antd'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../app/AuthContext'
import { projectApi, systemApi } from '../api/client'

type ProjectFormValues = {
  name: string
  description?: string
}

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function ProjectsPage() {
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [createOpen, setCreateOpen] = useState(false)
  const [editingProjectId, setEditingProjectId] = useState<number | null>(null)
  const [form] = Form.useForm<ProjectFormValues>()
  const { user } = useAuth()
  const { data } = useQuery({
    queryKey: ['projects'],
    queryFn: projectApi.list,
  })
  const { data: aiHealth } = useQuery({
    queryKey: ['ai-health'],
    queryFn: systemApi.aiHealth,
  })

  const projects = data || []
  const ownedCount = projects.filter((item) => item.owner_id === user?.id).length
  const sharedCount = projects.length - ownedCount

  return (
    <>
      {contextHolder}
      <div className="projects-shell">
        <div className="projects-workbench projects-workbench--redesigned">
          <section className="projects-hero-grid">
            <div className="projects-hero-panel">
              <div className="projects-hero-kicker">PROJECT WORKSPACE</div>
              <Typography.Title level={1} className="projects-hero-title">
                Semantic Field Namer
              </Typography.Title>
              <Typography.Paragraph className="projects-hero-subtitle">
                把导入结构、结构编辑、风格分析和字段生成收敛到一个工作台里，持续沉淀你自己的字段命名体系。
              </Typography.Paragraph>

              <Space wrap size={[12, 12]}>
                <Button
                  type="primary"
                  size="large"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    form.resetFields()
                    setCreateOpen(true)
                  }}
                >
                  新建项目
                </Button>
                <div className="projects-hero-chip">
                  <DatabaseOutlined />
                  <span>共 {projects.length} 个项目</span>
                </div>
                <div className="projects-hero-chip">
                  <EditOutlined />
                  <span>我创建 {ownedCount} 个</span>
                </div>
                <div className="projects-hero-chip">
                  <TeamOutlined />
                  <span>共享给我 {sharedCount} 个</span>
                </div>
              </Space>
            </div>

            <div className="projects-signal-panel">
              <div className="projects-signal-card">
                <div className="projects-card-topline">
                  <div className="projects-signal-label">AI 状态</div>
                  <Link to="/settings/ai">
                    <Button
                      type="text"
                      shape="circle"
                      icon={<SettingOutlined />}
                      aria-label="编辑 AI 配置"
                    />
                  </Link>
                </div>
                <div className="projects-signal-value">
                  {aiHealth?.reachable ? `已连接 · ${aiHealth.model}` : '未连接'}
                </div>
                <div className="projects-signal-meta">
                  {aiHealth?.source_name ? `当前来源：${aiHealth.source_name}` : '未配置来源'}
                </div>
              </div>

              <div className="projects-signal-card">
                <div className="projects-signal-label">工作流</div>
                <div className="projects-signal-flow">
                  <span>导入</span>
                  <span>编辑</span>
                  <span>分析</span>
                  <span>生成</span>
                </div>
              </div>
            </div>
          </section>

          <div className="projects-section-head projects-section-head--clean">
            <div>
              <Typography.Title level={3} style={{ margin: 0 }}>
                我的项目
              </Typography.Title>
              <Typography.Text type="secondary">进入项目后即可继续导入结构、调阈值和生成字段</Typography.Text>
            </div>
          </div>

          {projects.length ? (
            <div className="project-grid project-grid--luxury">
            {projects.map((item) => (
                <article key={item.id} className="project-card">
                  <div className="project-card-head">
                    <div>
                      <Typography.Title level={4} style={{ margin: 0 }}>
                        {item.name}
                      </Typography.Title>
                      <Typography.Paragraph type="secondary" className="project-desc">
                        {item.description || '暂无描述'}
                      </Typography.Paragraph>
                    </div>
                    <div className="project-card-head-actions">
                      <Tag color={item.owner_id === user?.id ? 'green' : 'blue'}>
                        {item.owner_id === user?.id ? 'Owner' : 'Shared'}
                      </Tag>
                      {item.owner_id === user?.id ? (
                        <Popconfirm
                          title="确认删除项目？"
                          description="删除后项目、导入结构、映射和生成历史都会被清空。"
                          okText="确认删除"
                          cancelText="取消"
                          onConfirm={async () => {
                            try {
                              await projectApi.delete(item.id)
                              messageApi.success('项目已删除')
                              await queryClient.invalidateQueries({ queryKey: ['projects'] })
                            } catch {
                              messageApi.error('项目删除失败')
                            }
                          }}
                        >
                          <Button
                            danger
                            type="text"
                            shape="circle"
                            icon={<DeleteOutlined />}
                            aria-label={`删除项目 ${item.name}`}
                          />
                        </Popconfirm>
                      ) : null}
                    </div>
                  </div>

                  <div className="project-card-meta">更新于 {formatDate(item.updated_at)}</div>

                  <div className="project-primary-actions">
                    <Link to={`/projects/${item.id}/import`}>
                      <Button icon={<NodeIndexOutlined />}>导入结构</Button>
                    </Link>
                    <Link to={`/projects/${item.id}/schema-fields`}>
                      <Button icon={<EditOutlined />}>结构编辑</Button>
                    </Link>
                    {item.owner_id === user?.id ? (
                      <Button
                        icon={<EditOutlined />}
                        onClick={() => {
                          setEditingProjectId(item.id)
                          form.setFieldsValue({
                            name: item.name,
                            description: item.description || undefined,
                          })
                          setCreateOpen(true)
                        }}
                      >
                        编辑
                      </Button>
                    ) : null}
                    <Link to={`/projects/${item.id}/generate`}>
                      <Button type="primary" icon={<DatabaseOutlined />}>
                        字段生成
                      </Button>
                    </Link>
                  </div>

                  <div className="project-secondary-actions">
                    <Link to={`/projects/${item.id}/style`}>风格分析</Link>
                    <Link to={`/projects/${item.id}/members`}>成员管理</Link>
                    <Link to={`/projects/${item.id}/history`}>生成历史</Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="project-empty-card project-empty-card--luxury">
              <Empty description="还没有项目，先创建一个开始使用" />
            </div>
          )}
        </div>
      </div>

      <Modal
        title={editingProjectId ? '编辑项目' : '新建项目'}
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false)
          setEditingProjectId(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText={editingProjectId ? '保存' : '创建'}
        cancelText="取消"
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            try {
              if (editingProjectId) {
                await projectApi.update(editingProjectId, values)
                messageApi.success('项目已更新')
              } else {
                await projectApi.create(values)
                messageApi.success('项目已创建')
              }
              setCreateOpen(false)
              setEditingProjectId(null)
              form.resetFields()
              await queryClient.invalidateQueries({ queryKey: ['projects'] })
            } catch {
              messageApi.error(editingProjectId ? '项目更新失败' : '创建项目失败')
            }
          }}
        >
          <Form.Item name="name" label="项目名称" rules={[{ required: true }]}>
            <Input placeholder="例如：土地直供分析" />
          </Form.Item>
          <Form.Item name="description" label="项目说明">
            <Input.TextArea rows={4} placeholder="简单说明项目用途" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
