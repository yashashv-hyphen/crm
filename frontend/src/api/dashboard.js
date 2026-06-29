import api from './axios'

export const getFosDashboard = () => api.get('/dashboard/fos')

export const getAdminDashboard = (params) => api.get('/dashboard/admin', { params })
