import { useMemo, useState } from 'react'
import { Alert, Button, Card, Form, Input, Progress, Space, Spin, Steps, Table, Tag, Typography, message } from 'antd'
import { DownloadOutlined, SaveOutlined } from '@ant-design/icons'
import { useParams } from 'react-router-dom'

import { generationApi, projectApi, systemApi } from '../api/client'
import type { GeneratedFieldResult, GenerationTask } from '../types/api'

type GenerateFormValues = {
  table_name: string
  existing_columns?: string
  field_comments: string
}

function parseFieldComments(input: string): string[] {
  return input
    .split(/[,\n，、；;]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function guessColumnType(item: GeneratedFieldResult): string {
  const comment = item.comment_zh
  const name = item.proposed_name

  if (name === 'id' || name.endsWith('_id')) {
    return 'bigint'
  }
  if (name.startsWith('is_') || name.endsWith('_flag') || name.startsWith('f_')) {
    return 'boolean'
  }
  if (name.endsWith('_at') || name.endsWith('_time')) {
    return 'timestamp'
  }
  if (name.endsWith('_date')) {
    return 'date'
  }
  if (
    comment.includes('数量') ||
    comment.includes('次数') ||
    comment.includes('排序') ||
    name.endsWith('_count') ||
    name.endsWith('_qty') ||
    name.endsWith('_sort')
  ) {
    return 'integer'
  }
  return 'varchar(255)'
}

function buildCreateTableSql(tableName: string, results: GeneratedFieldResult[]): string {
  const columnLines = results.map((item) => {
    const columnType = guessColumnType(item)
    return `  ${item.proposed_name} ${columnType}`
  })
  const commentLines = results.map(
    (item) => `COMMENT ON COLUMN ${tableName}.${item.proposed_name} IS '${item.comment_zh.replaceAll("'", "''")}';`,
  )

  return [
    `CREATE TABLE ${tableName} (`,
    ...columnLines.map((line, index) => `${line}${index < columnLines.length - 1 ? ',' : ''}`),
    ');',
    '',
    `COMMENT ON TABLE ${tableName} IS '自动生成表';`,
    ...commentLines,
  ].join('\n')
}

function getSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    exact: '完全一致',
    lexical: '近似匹配',
    semantic: '语义命中',
    llm: '大模型生成',
    heuristic: '本地兜底',
  }
  return labels[source] || source
}

function getMatchedDescription(item: GeneratedFieldResult): string {
  const reference = item.matched_reference || {}
  const matchedName =
    typeof reference.english_name === 'string'
      ? reference.english_name
      : typeof item.proposed_name === 'string'
        ? item.proposed_name
        : ''
  const matchedZh = typeof reference.canonical_zh === 'string' ? reference.canonical_zh : ''
  const matchedLabel = matchedZh ? `${matchedName}（${matchedZh}）` : matchedName

  if (item.source === 'exact' && matchedLabel) {
    return `与历史字段 ${matchedLabel} 一致`
  }
  if (item.source === 'lexical' && matchedLabel) {
    return `与历史字段 ${matchedLabel} 近似`
  }
  if (item.source === 'semantic' && matchedLabel) {
    return `语义接近历史字段 ${matchedLabel}`
  }
  return item.reason || '-'
}

const generationStageMap: Record<string, { title: string; description: string }> = {
  queued: { title: '已创建任务', description: '等待开始' },
  preparing: { title: '准备中', description: '正在整理输入字段' },
  exact_matching: { title: '本地精确匹配', description: '正在匹配本地映射池' },
  lexical_matching: { title: '近似匹配', description: '正在匹配相近历史字段' },
  semantic_search: { title: '向量检索', description: '正在检索向量数据库' },
  llm_generating: { title: '大模型补全', description: '正在调用大模型生成' },
  post_processing: { title: '结果整理', description: '正在处理冲突和导出信息' },
  completed: { title: '已完成', description: '字段生成完成' },
  failed: { title: '失败', description: '生成过程中出现错误' },
}

const generationStages = [
  'queued',
  'preparing',
  'exact_matching',
  'lexical_matching',
  'semantic_search',
  'llm_generating',
  'post_processing',
  'completed',
]

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

export function GeneratePage() {
  const { projectId = '' } = useParams()
  const [form] = Form.useForm<GenerateFormValues>()
  const [messageApi, contextHolder] = message.useMessage()
  const [results, setResults] = useState<GeneratedFieldResult[]>([])
  const [generationTask, setGenerationTask] = useState<GenerationTask | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const tableName = Form.useWatch('table_name', form) || 'new_table'
  const createTableSql = useMemo(() => buildCreateTableSql(tableName, results), [results, tableName])

  return (
    <>
      {contextHolder}
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card title="字段生成">
          <Typography.Paragraph type="secondary">
            直接输入多个中文字段，支持英文逗号、中文逗号和换行分隔。
          </Typography.Paragraph>
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              table_name: 'new_table',
              field_comments: '用户编号，用户名，联系电话，删除标志，创建时间',
            }}
            onFinish={async (values) => {
              const comments = parseFieldComments(values.field_comments)
              if (!comments.length) {
                messageApi.warning('请先输入至少一个中文字段')
                return
              }

              try {
                setIsGenerating(true)
                setResults([])
                const task = await generationApi.createTask(projectId, {
                  table_name: values.table_name,
                  db_type: 'pg',
                  existing_columns: (values.existing_columns || '')
                    .split(',')
                    .map((item) => item.trim())
                    .filter(Boolean),
                  preview_only: true,
                  items: comments.map((comment) => ({
                    comment_zh: comment,
                    nullable: true,
                  })),
                })
                let done = false
                while (!done) {
                  const status = await generationApi.getTask(projectId, task.task_id)
                  setGenerationTask(status)
                  if (status.status === 'completed' && status.result) {
                    setResults(status.result.results)
                    const health = await systemApi.aiHealth()
                    if (!health.reachable) {
                      messageApi.warning('AI 当前不可用，本次结果可能来自本地匹配或兜底策略')
                    } else {
                      messageApi.success(`已生成 ${status.result.results.length} 个字段`)
                    }
                    done = true
                  } else if (status.status === 'failed') {
                    messageApi.error(status.error || '字段生成失败')
                    done = true
                  } else {
                    await sleep(800)
                  }
                }
              } catch {
                messageApi.error('字段生成失败')
              } finally {
                setIsGenerating(false)
              }
            }}
          >
            <Form.Item name="table_name" label="目标表名" rules={[{ required: true }]}>
              <Input placeholder="例如：user_profile" />
            </Form.Item>
            <Form.Item name="existing_columns" label="当前表已有字段">
              <Input placeholder="例如：id, created_at, updated_at" />
            </Form.Item>
            <Form.Item
              name="field_comments"
              label="中文字段列表"
              rules={[{ required: true }]}
              extra="示例：用户编号，用户名，联系电话，删除标志"
            >
              <Input.TextArea rows={6} placeholder="多个字段用逗号或换行分隔" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={isGenerating}>
              生成字段名
            </Button>
          </Form>
        </Card>

        {generationTask && isGenerating ? (
          <Card title="执行进度">
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Alert
                type={generationTask.status === 'failed' ? 'error' : 'info'}
                showIcon
                message={generationTask.message}
                description={generationTask.status === 'running' ? '系统会依次经过本地匹配、向量检索和大模型补全。' : generationTask.error}
              />
              <Progress percent={generationTask.progress} status={generationTask.status === 'failed' ? 'exception' : undefined} />
              <Steps
                current={Math.max(generationStages.indexOf(generationTask.stage), 0)}
                items={generationStages.slice(0, 7).map((stage) => ({
                  title: generationStageMap[stage].title,
                  description: generationStageMap[stage].description,
                }))}
              />
              <Spin spinning={generationTask.status === 'running'}>
                <Typography.Text type="secondary">
                  当前阶段：{generationStageMap[generationTask.stage]?.title || generationTask.stage}
                </Typography.Text>
              </Spin>
            </Space>
          </Card>
        ) : null}

        <Card
          title="生成结果"
          extra={
            results.length ? (
              <Space>
                <Button
                  icon={<SaveOutlined />}
                  onClick={async () => {
                    try {
                      await projectApi.confirmMappings(projectId, {
                        items: results.map((item) => ({
                          canonical_zh: item.comment_zh,
                          english_name: item.proposed_name,
                          alias_zh_list: [],
                        })),
                      })
                      messageApi.success('已确认并回写到本地映射池')
                    } catch {
                      messageApi.error('映射回写失败')
                    }
                  }}
                >
                  写入语义池
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => {
                    const blob = new Blob([createTableSql], { type: 'text/sql;charset=utf-8' })
                    const url = URL.createObjectURL(blob)
                    const link = document.createElement('a')
                    link.href = url
                    link.download = `${tableName}.sql`
                    link.click()
                    URL.revokeObjectURL(url)
                  }}
                >
                  导出建表语句
                </Button>
              </Space>
            ) : null
          }
        >
          <Table<GeneratedFieldResult>
            rowKey={(record) => `${record.comment_zh}-${record.proposed_name}`}
            dataSource={results}
            pagination={false}
            locale={{ emptyText: '还没有生成结果' }}
            columns={[
              { title: '中文字段', dataIndex: 'comment_zh' },
              { title: '字段名', dataIndex: 'proposed_name' },
              {
                title: '来源',
                dataIndex: 'source',
                render: (value) => <Tag>{getSourceLabel(value)}</Tag>,
              },
              {
                title: '命中说明',
                render: (_, record) => getMatchedDescription(record),
              },
            ]}
          />
        </Card>

        <Card title="建表语句预览">
          <Input.TextArea value={results.length ? createTableSql : ''} rows={Math.max(8, results.length + 4)} readOnly />
        </Card>
      </Space>
    </>
  )
}
