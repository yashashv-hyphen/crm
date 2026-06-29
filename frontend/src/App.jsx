import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import FosDashboard from './pages/FosDashboard'
import AdminDashboard from './pages/AdminDashboard'
import Activities from './pages/Activities'
import LeadTablePage from './pages/LeadTablePage'
import FollowUps from './pages/FollowUps'
import Search from './pages/Search'
import PerformanceReport from './pages/PerformanceReport'
import UserManagement from './pages/admin/UserManagement'
import ActivityManagement from './pages/admin/ActivityManagement'
import UploadLeads from './pages/admin/UploadLeads'
import UploadFinalStage from './pages/admin/UploadFinalStage'
import Layout from './components/Layout'

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex h-screen items-center justify-center text-gray-500">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && user.role !== 'admin') return <Navigate to="/" replace />
  return children
}

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'admin' ? '/admin/dashboard' : '/dashboard'} replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RootRedirect />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<FosDashboard />} />
            <Route path="/activities" element={<Activities />} />
            <Route path="/leads" element={<LeadTablePage />} />
            <Route path="/follow-ups" element={<FollowUps />} />
            <Route path="/search" element={<Search />} />
            <Route path="/reports" element={<PerformanceReport />} />
          </Route>
          <Route element={<ProtectedRoute adminOnly><Layout /></ProtectedRoute>}>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/users" element={<UserManagement />} />
            <Route path="/admin/activities" element={<ActivityManagement />} />
            <Route path="/admin/upload" element={<UploadLeads />} />
            <Route path="/admin/upload-final" element={<UploadFinalStage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
