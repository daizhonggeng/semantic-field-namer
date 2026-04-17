import { Button, Card, Form, Input, Typography, message } from 'antd'
import { Link, useNavigate } from 'react-router-dom'

import { authApi } from '../api/client'
import { useAuth } from '../app/AuthContext'

export function RegisterPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const navigate = useNavigate()
  const { setSession } = useAuth()

  return (
    <div className="auth-page">
      {contextHolder}
      <Card className="auth-card">
        <Typography.Title level={2}>注册</Typography.Title>
        <Form
          layout="vertical"
          onFinish={async (values) => {
            try {
              const payload = await authApi.register(values)
              setSession(payload)
              navigate('/projects')
            } catch (error) {
              void error
              messageApi.error('注册失败，用户名可能已存在')
            }
          }}
        >
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input placeholder="为项目共享准备一个唯一用户名" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            注册并进入
          </Button>
        </Form>
        <Typography.Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
          已有账号？<Link to="/login">去登录</Link>
        </Typography.Paragraph>
      </Card>
    </div>
  )
}
