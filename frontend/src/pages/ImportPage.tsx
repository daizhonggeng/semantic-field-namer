import { useState } from 'react'
import { Button, Card, Col, Form, Input, Row, Space, Typography, Upload, message } from 'antd'
import type { UploadFile } from 'antd/es/upload/interface'
import { useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { importApi } from '../api/client'

export function ImportPage() {
  const { projectId = '' } = useParams()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [excelFiles, setExcelFiles] = useState<UploadFile[]>([])

  return (
    <>
      {contextHolder}
      <div className="import-page">
        <Row gutter={[16, 16]} align="stretch">
          <Col xs={24} xl={12}>
            <Card title="导入 SQL" className="import-card">
            <div className="import-card-note">
              <a href="/templates/import_template.sql" download>
                下载模板
              </a>
            </div>
            <Form
              className="compact-form"
              layout="vertical"
              onFinish={async (values) => {
                try {
                  const result = await importApi.sql(projectId, values)
                  messageApi.success(
                    `SQL 导入成功，共 ${result.imported_count} 个字段，提取注释 ${result.comment_count} 个，建立映射 ${result.mapped_count} 个`,
                  )
                  await queryClient.invalidateQueries({ queryKey: ['imported-fields', projectId] })
                } catch {
                  messageApi.error('SQL 导入失败')
                }
              }}
            >
              <Form.Item name="source_name" label="来源名称">
                <Input />
              </Form.Item>
              <Form.Item name="sql" label="建表 SQL" rules={[{ required: true }]}>
                <Input.TextArea rows={10} placeholder="粘贴 CREATE TABLE 语句" />
              </Form.Item>
              <Button type="primary" htmlType="submit">
                导入 SQL
              </Button>
            </Form>
          </Card>
        </Col>
        <Col xs={24} xl={12}>
          <Card title="导入 JSON" className="import-card">
            <div className="import-card-note">
              <a href="/templates/import_template.json" download>
                下载模板
              </a>
            </div>
            <Form
              className="compact-form"
              layout="vertical"
              onFinish={async (values) => {
                try {
                  const fields = JSON.parse(values.json)
                  const result = await importApi.json(projectId, { source_name: values.source_name, fields })
                  messageApi.success(
                    `JSON 导入成功，共 ${result.imported_count} 个字段，提取注释 ${result.comment_count} 个，建立映射 ${result.mapped_count} 个`,
                  )
                  await queryClient.invalidateQueries({ queryKey: ['imported-fields', projectId] })
                } catch {
                  messageApi.error('JSON 导入失败，请检查 JSON 格式')
                }
              }}
            >
              <Form.Item name="source_name" label="来源名称">
                <Input />
              </Form.Item>
              <Form.Item name="json" label="字段 JSON" rules={[{ required: true }]}>
                <Input.TextArea rows={10} />
              </Form.Item>
              <Button type="primary" htmlType="submit">
                导入 JSON
              </Button>
            </Form>
          </Card>
        </Col>
        <Col xs={24} xl={12}>
          <Card title="导入 Excel" className="import-card">
            <div className="import-card-note">
              <Space size={12}>
                <a href="/templates/import_template.xlsx" download>
                  下载模板
                </a>
                <Typography.Text type="secondary">支持标准列头和左右对照模板</Typography.Text>
              </Space>
            </div>
            <Form
              className="compact-form"
              layout="vertical"
              onFinish={async (values) => {
                const file = excelFiles[0]?.originFileObj
                if (!(file instanceof File)) {
                  messageApi.error('请先选择 Excel 文件')
                  return
                }
                try {
                  const result = await importApi.excel(projectId, { source_name: values.source_name, file })
                  messageApi.success(
                    `Excel 导入成功，共 ${result.imported_count} 个字段，提取注释 ${result.comment_count} 个，建立映射 ${result.mapped_count} 个`,
                  )
                  setExcelFiles([])
                  await queryClient.invalidateQueries({ queryKey: ['imported-fields', projectId] })
                } catch {
                  messageApi.error('Excel 导入失败，请检查文件结构')
                }
              }}
            >
              <Form.Item name="source_name" label="来源名称">
                <Input placeholder="留空时默认使用文件名" />
              </Form.Item>
              <Form.Item label="Excel 文件" required>
                <Upload
                  accept=".xlsx,.xlsm"
                  beforeUpload={() => false}
                  maxCount={1}
                  fileList={excelFiles}
                  onChange={({ fileList }) => setExcelFiles(fileList.slice(-1))}
                >
                  <Button>选择 Excel 文件</Button>
                </Upload>
              </Form.Item>
              <Button type="primary" htmlType="submit">
                导入 Excel
              </Button>
            </Form>
          </Card>
        </Col>
        <Col xs={24} xl={12}>
          <Card title="导入 TXT" className="import-card">
            <div className="import-card-note">
              <Space size={12}>
                <a href="/templates/import_template.txt" download>
                  下载模板
                </a>
                <Typography.Text type="secondary">使用 `|` 分隔：tablename|columnname|中文注释|datatype</Typography.Text>
              </Space>
            </div>
            <Form
              className="compact-form"
              layout="vertical"
              onFinish={async (values) => {
                try {
                  const result = await importApi.txt(projectId, {
                    source_name: values.source_name,
                    content: values.content,
                  })
                  messageApi.success(
                    `TXT 导入成功，共 ${result.imported_count} 个字段，提取注释 ${result.comment_count} 个，建立映射 ${result.mapped_count} 个`,
                  )
                  await queryClient.invalidateQueries({ queryKey: ['imported-fields', projectId] })
                } catch {
                  messageApi.error('TXT 导入失败，请检查内容格式')
                }
              }}
            >
              <Form.Item name="source_name" label="来源名称">
                <Input />
              </Form.Item>
              <Form.Item
                name="content"
                label="TXT 内容"
                rules={[{ required: true }]}
                extra="示例：tablename|columnname|中文注释|datatype"
              >
                <Input.TextArea rows={10} />
              </Form.Item>
              <Button type="primary" htmlType="submit">
                导入 TXT
              </Button>
            </Form>
          </Card>
          </Col>
        </Row>
      </div>
    </>
  )
}
