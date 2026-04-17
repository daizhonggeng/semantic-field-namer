import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './app/AppShell'
import { AuthProvider } from './app/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AISettingsPage } from './pages/AISettingsPage'
import { HistoryPage } from './pages/HistoryPage'
import { ImportPage } from './pages/ImportPage'
import { ImportedFieldsPage } from './pages/ImportedFieldsPage'
import { LoginPage } from './pages/LoginPage'
import { MembersPage } from './pages/MembersPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { RegisterPage } from './pages/RegisterPage'
import { StylePage } from './pages/StylePage'
import { GeneratePage } from './pages/GeneratePage'

const queryClient = new QueryClient()

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#0f766e', borderRadius: 14 } }}>
      <AntApp>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route element={<ProtectedRoute />}>
                  <Route element={<AppShell />}>
                    <Route path="/" element={<Navigate to="/projects" replace />} />
                    <Route path="/projects" element={<ProjectsPage />} />
                    <Route path="/settings/ai" element={<AISettingsPage />} />
                    <Route path="/projects/:projectId/import" element={<ImportPage />} />
                    <Route path="/projects/:projectId/schema-fields" element={<ImportedFieldsPage />} />
                    <Route path="/projects/:projectId/style" element={<StylePage />} />
                    <Route path="/projects/:projectId/generate" element={<GeneratePage />} />
                    <Route path="/projects/:projectId/members" element={<MembersPage />} />
                    <Route path="/projects/:projectId/history" element={<HistoryPage />} />
                  </Route>
                </Route>
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </QueryClientProvider>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
