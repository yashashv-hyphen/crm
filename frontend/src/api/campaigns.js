import api from './axios'

export const getCampaigns = () => api.get('/campaigns')

export const uploadCampaign = (name, file) => {
  const form = new FormData()
  form.append('name', name)
  form.append('file', file)
  return api.post('/campaigns/upload', form)
}

export const toggleCampaign = (id) => api.post(`/campaigns/${id}/toggle`)

export const getCampaignLeads = () => api.get('/campaigns/leads')
