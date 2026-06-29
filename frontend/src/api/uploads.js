import api from './axios'

export const uploadTemplate1 = (file, activityId) => {
  const form = new FormData()
  form.append('file', file)
  form.append('activity_id', activityId)
  return api.post('/uploads/template1', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadTemplate2 = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/uploads/template2', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getUploadStatus = (uploadId) => api.get(`/uploads/${uploadId}/status`)

export const getUploadErrors = (uploadId) => api.get(`/uploads/${uploadId}/errors`)
