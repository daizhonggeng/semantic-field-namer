import { Button, Card, Form, Input, Typography, message } from 'antd'
import { Link, useNavigate } from 'react-router-dom'

import { authApi } from '../api/client'
import { useAuth } from '../app/AuthContext'

export function LoginPage() {
  const [messageApi, contextHolder] = message.useMessage()
  const navigate = useNavigate()
  const { setSession } = useAuth()

  return (
    <div className="auth-page">
      {contextHolder}
      <Card className="auth-card">
        <Typography.Title level={2}>登录</Typography.Title>
        <Form
          layout="vertical"
          onFinish={async (values) => {
            try {
              const payload = await authApi.login(values)
              setSession(payload)
              navigate('/projects')
            } catch (error) {
              void error
              messageApi.error('登录失败，请检查用户名和密码')
            }
          }}
        >
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input placeholder="例如：admin" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            登录
          </Button>
        </Form>
        <Typography.Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
          没有账号？<Link to="/register">去注册</Link>
        </Typography.Paragraph>
      </Card>
    </div>
  )
}
