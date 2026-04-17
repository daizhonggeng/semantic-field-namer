import { Button, Card, Form, Select, Table, message } from 'antd'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { projectApi } from '../api/client'

export function MembersPage() {
  const { projectId = '' } = useParams()
  const queryClient = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const { data, isLoading } = useQuery({
    queryKey: ['members', projectId],
    queryFn: () => projectApi.members(projectId),
  })
  const { data: candidates } = useQuery({
    queryKey: ['share-candidates', projectId],
    queryFn: () => projectApi.shareCandidates(projectId),
  })

  return (
    <>
      {contextHolder}
      <Card title="项目共享">
        <Form
          layout="inline"
          onFinish={async (values) => {
            try {
              await projectApi.share(projectId, values)
              messageApi.success('共享成功')
              await queryClient.invalidateQueries({ queryKey: ['members', projectId] })
            } catch {
              messageApi.error('共享失败')
            }
          }}
        >
          <Form.Item name="username" rules={[{ required: true }]}>
            <Select
              style={{ width: 220 }}
              placeholder="选择用户"
              options={(candidates || []).map((item) => ({ value: item.username, label: item.username }))}
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item name="role" initialValue="viewer" rules={[{ required: true }]}>
            <Select
              style={{ width: 160 }}
              options={[
                { value: 'viewer', label: 'viewer' },
                { value: 'editor', label: 'editor' },
                { value: 'owner', label: 'owner' },
              ]}
            />
          </Form.Item>
          <Button type="primary" htmlType="submit">
            添加成员
          </Button>
        </Form>
        <Table
          style={{ marginTop: 24 }}
          loading={isLoading}
          rowKey={(record) => `${record.username}-${record.role}`}
          dataSource={data || []}
          pagination={false}
          columns={[
            { title: '用户名', dataIndex: 'username' },
            { title: '角色', dataIndex: 'role' },
            { title: '加入时间', dataIndex: 'created_at' },
          ]}
        />
      </Card>
    </>
  )
}
