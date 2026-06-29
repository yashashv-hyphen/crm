import api from './axios'

export const getPerformanceReport = (params) =>
  api.get('/reports/performance', { params })

export const downloadPerformanceReport = (params) =>
  api.get('/reports/performance/download', { params, responseType: 'blob' })
