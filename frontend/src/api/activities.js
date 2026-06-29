import api from './axios'

export const listActivities = () => api.get('/activities')

export const createActivity = (data) => api.post('/activities', data)

export const reorderActivities = (items) => api.post('/activities/reorder', { items })

export const updateActivity = (id, data) => api.patch(`/activities/${id}`, data)

export const deleteActivity = (id) => api.delete(`/activities/${id}`)

export const getSubDispositions = (activityId) =>
  api.get(`/activities/${activityId}/sub-dispositions`)

export const createSubDisposition = (activityId, data) =>
  api.post(`/activities/${activityId}/sub-dispositions`, data)

export const deleteSubDisposition = (sdId) =>
  api.delete(`/activities/sub-dispositions/${sdId}`)
