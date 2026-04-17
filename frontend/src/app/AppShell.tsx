import { ArrowLeftOutlined, DatabaseOutlined, EditOutlined, HistoryOutlined, NodeIndexOutlined, TeamOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { Layout, Menu, Typography } from 'antd'
import { Link, Outlet, useLocation, useParams } from 'react-router-dom'

import { useAuth } from './AuthContext'
import { AIStatusBadge } from '../components/AIStatusBadge'

const { Content, Sider } = Layout

export function AppShell() {
  const { pathname } = useLocation()
  const params = useParams()
  const { user, logout } = useAuth()
  const isProjectsHome = pathname === '/projects'
  const shouldShowBackToProjects = Boolean(params.projectId) || pathname.startsWith('/settings/')

  const rootItems = shouldShowBackToProjects
    ? [{ key: '/projects', icon: <ArrowLeftOutlined />, label: <Link to="/projects">返回项目列表</Link> }]
    : []
  const projectItems = params.projectId
    ? [
        {
          key: `/projects/${params.projectId}/import`,
          icon: <NodeIndexOutlined />,
          label: <Link to={`/projects/${params.projectId}/import`}>导入结构</Link>,
        },
        {
          key: `/projects/${params.projectId}/schema-fields`,
          icon: <EditOutlined />,
          label: <Link to={`/projects/${params.projectId}/schema-fields`}>结构编辑</Link>,
        },
        {
          key: `/projects/${params.projectId}/style`,
          icon: <ThunderboltOutlined />,
          label: <Link to={`/projects/${params.projectId}/style`}>风格分析</Link>,
        },
        {
          key: `/projects/${params.projectId}/generate`,
          icon: <DatabaseOutlined />,
          label: <Link to={`/projects/${params.projectId}/generate`}>字段生成</Link>,
        },
        {
          key: `/projects/${params.projectId}/members`,
          icon: <TeamOutlined />,
          label: <Link to={`/projects/${params.projectId}/members`}>成员管理</Link>,
        },
        {
          key: `/projects/${params.projectId}/history`,
          icon: <HistoryOutlined />,
          label: <Link to={`/projects/${params.projectId}/history`}>生成历史</Link>,
        },
      ]
    : []

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {!isProjectsHome ? (
        <Sider width={252} theme="light" breakpoint="lg" collapsedWidth="0" className="app-sider">
          <div className="brand-panel">
            <Typography.Title level={4} style={{ margin: 0 }}>
              Semantic Field Namer
            </Typography.Title>
            <Typography.Text type="secondary">字段命名生成器</Typography.Text>
          </div>
          <div className="sider-menu-wrap">
            <Menu mode="inline" selectedKeys={[pathname]} items={[...rootItems, ...projectItems]} />
          </div>
          <div className="sider-footer">
            <AIStatusBadge />
            <div className="sider-userbox">
              <Typography.Text strong>{user?.username}</Typography.Text>
              <Typography.Link onClick={logout}>退出</Typography.Link>
            </div>
          </div>
        </Sider>
      ) : null}
      <Layout>
        <Content style={{ padding: isProjectsHome ? '24px 24px 24px 0' : '20px 24px 24px 0' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
