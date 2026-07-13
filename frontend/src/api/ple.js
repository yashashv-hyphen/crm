import api from './axios'

export const uploadPleLaunches = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/ple/upload/launches', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadPleMcidDetail = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/ple/upload/mcid-detail', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getPleAgentSummary = () => api.get('/ple/agent-summary')

export const getPleMcidDetail = (params) => api.get('/ple/mcid-detail', { params })

export const getPleMcidHistory = (mcid) => api.get(`/ple/mcid/${mcid}/history`)

export const updatePleMcid = (mcid, updates) => api.patch(`/ple/mcid/${mcid}`, updates)
