import api from './axios'

export const getLeads = (params) => api.get('/leads', { params })

export const updateLead = (id, data) => api.patch(`/leads/${id}`, data)

export const bulkUpdateLeads = (data) => api.post('/leads/bulk-update', data)

export const getFollowUps = () => api.get('/leads/follow-ups')

export const searchLeads = (q) => api.get('/leads/search', { params: { q } })

export const downloadLeads = (params) =>
  api.get('/leads/download', { params, responseType: 'blob' })

export const getLead = (id) => api.get(`/leads/${id}`)

export const getLeadHistory = (leadId) => api.get(`/leads/${leadId}/history`)
