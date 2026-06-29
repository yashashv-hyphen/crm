import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { logout as logoutApi } from '../api/auth'
import { useEventSource } from '../hooks/useEventSource'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  useEventSource('/api/events/stream', (event) => {
    if (event.type !== 'upload_complete') return
    queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['fos-dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['leads'] })
    if (user?.role === 'fos' && event.fos_ids?.includes(String(user.id))) {
      toast.success(`${event.success_count} new lead${event.success_count !== 1 ? 's' : ''} assigned to you`)
    }
  })

  const handleLogout = async () => {
    await logoutApi()
    logout()
    navigate('/login')
  }

  const isAdmin = user?.role === 'admin'

  const navClass = ({ isActive }) =>
    `px-3 py-2 rounded text-sm font-medium transition-colors ${
      isActive ? 'bg-blue-700 text-white' : 'text-blue-100 hover:bg-blue-700 hover:text-white'
    }`

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-blue-800 text-white shadow">
        <div className="max-w-screen-xl mx-auto px-4 flex items-center justify-between h-14">
          <div className="flex items-center gap-1">
            <span className="font-bold text-lg mr-4">Global Sales CRM</span>
            {isAdmin ? (
              <>
                <NavLink to="/admin/dashboard" className={navClass}>Dashboard</NavLink>
                <NavLink to="/admin/users" className={navClass}>Users</NavLink>
                <NavLink to="/admin/activities" className={navClass}>Activities</NavLink>
                <NavLink to="/admin/upload" className={navClass}>Upload Leads</NavLink>
                <NavLink to="/admin/upload-final" className={navClass}>Upload Final Stage</NavLink>
                <NavLink to="/reports" className={navClass}>Reports</NavLink>
                <NavLink to="/search" className={navClass}>Search</NavLink>
              </>
            ) : (
              <>
                <NavLink to="/dashboard" className={navClass}>Dashboard</NavLink>
                <NavLink to="/activities" className={navClass}>My Activities</NavLink>
                <NavLink to="/follow-ups" className={navClass}>Follow-ups</NavLink>
                <NavLink to="/search" className={navClass}>Search</NavLink>
                <NavLink to="/reports" className={navClass}>Reports</NavLink>
              </>
            )}
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-blue-200">{user?.full_name}</span>
            <span className="bg-blue-600 px-2 py-0.5 rounded text-xs uppercase">{user?.role}</span>
            <button onClick={handleLogout} className="bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-sm">
              Logout
            </button>
          </div>
        </div>
      </nav>
      <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
