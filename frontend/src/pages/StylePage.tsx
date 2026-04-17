import { useEffect, useState } from 'react'
import { Alert, Button, Card, Descriptions, Form, InputNumber, Progress, Space, Spin, Steps, Typography, message } from 'antd'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { styleApi } from '../api/client'
import type { StyleTask } from '../types/api'

const styleStages = ['loading_fields', 'calculating_stats', 'llm_summary', 'completed']

const styleStageMap: Record<string, { title: string; description: string }> = {
  loading_fields: { title: '读取字段', description: '正在读取当前项目的全部字段' },
  calculating_stats: { title: '统计风格', description: '正在统计命名规则与缩写偏好' },
  llm_summary: { title: '生成摘要', description: '正在提炼命名风格摘要' },
  completed: { title: '已完成', description: '风格分析完成' },
  failed: { title: '失败', description: '风格分析失败' },
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

export function StylePage() {
  const { projectId = '' } = useParams()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [thresholdForm] = Form.useForm()
  const [styleTask, setStyleTask] = useState<StyleTask | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const { data, isLoading } = useQuery({
    queryKey: ['style-profile', projectId],
    queryFn: () => styleApi.profile(projectId),
  })

  useEffect(() => {
    if (data?.matching_thresholds) {
      thresholdForm.setFieldsValue(data.matching_thresholds)
    }
  }, [data, thresholdForm])

  return (
    <>
      {contextHolder}
      <Card
        title="命名风格指纹"
        extra={
          <Button
            type="primary"
            loading={isAnalyzing}
            onClick={async () => {
              try {
                setIsAnalyzing(true)
                const task = await styleApi.analyzeTask(projectId)
                let done = false
                while (!done) {
                  const status = await styleApi.getAnalyzeTask(projectId, task.task_id)
                  setStyleTask(status)
                  if (status.status === 'completed' && status.result) {
                    messageApi.success('风格分析已刷新')
                    await queryClient.invalidateQueries({ queryKey: ['style-profile', projectId] })
                    done = true
                  } else if (status.status === 'failed') {
                    messageApi.error(status.error || '风格分析失败')
                    done = true
                  } else {
                    await sleep(800)
                  }
                }
              } catch {
                messageApi.error('风格分析失败')
              } finally {
                setIsAnalyzing(false)
              }
            }}
          >
            重新分析
          </Button>
        }
        loading={isLoading}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {styleTask && isAnalyzing ? (
            <Card size="small" title="执行进度">
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Alert
                  type={styleTask.status === 'failed' ? 'error' : 'info'}
                  showIcon
                  message={styleTask.message}
                  description={styleTask.status === 'running' ? '系统会先统计当前项目的命名规则，再决定是否调用大模型生成摘要。': styleTask.error}
                />
                <Progress percent={styleTask.progress} status={styleTask.status === 'failed' ? 'exception' : undefined} />
                <Steps
                  current={Math.max(styleStages.indexOf(styleTask.stage), 0)}
                  items={styleStages.map((stage) => ({
                    title: styleStageMap[stage].title,
                    description: styleStageMap[stage].description,
                  }))}
                />
                <Spin spinning={styleTask.status === 'running'}>
                  <Typography.Text type="secondary">
                    当前阶段：{styleStageMap[styleTask.stage]?.title || styleTask.stage}
                  </Typography.Text>
                </Spin>
              </Space>
            </Card>
          ) : null}
          <div>
            <Typography.Title level={4}>命名军规</Typography.Title>
            <Typography.Paragraph>{data?.summary}</Typography.Paragraph>
          </div>
          <Card size="small" title="匹配阈值配置">
            <Form
              form={thresholdForm}
              layout="inline"
              onFinish={async (values) => {
                try {
                  await styleApi.updateThresholds(projectId, values)
                  messageApi.success('阈值已保存')
                  await queryClient.invalidateQueries({ queryKey: ['style-profile', projectId] })
                } catch {
                  messageApi.error('阈值保存失败')
                }
              }}
            >
              <Form.Item
                name="lexical_threshold"
                label="近似匹配阈值"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={1} step={0.01} />
              </Form.Item>
              <Form.Item
                name="semantic_score_threshold"
                label="向量相似度阈值"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={1} step={0.01} />
              </Form.Item>
              <Form.Item
                name="semantic_gap_threshold"
                label="向量分差阈值"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={1} step={0.01} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit">
                  保存阈值
                </Button>
              </Form.Item>
            </Form>
            <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
              近似匹配阈值：控制文字近似是否直接复用；向量相似度阈值：控制语义接近是否直接命中；向量分差阈值：控制第一名是否明显优于第二名。
            </Typography.Paragraph>
          </Card>
          <Descriptions bordered column={1}>
            <Descriptions.Item label="摘要来源">{data?.model_summary_source || 'none'}</Descriptions.Item>
            <Descriptions.Item label="统计">{JSON.stringify(data?.stats || {}, null, 2)}</Descriptions.Item>
            <Descriptions.Item label="缩写偏好">{JSON.stringify(data?.abbreviations || {}, null, 2)}</Descriptions.Item>
          </Descriptions>
        </Space>
      </Card>
    </>
  )
}
