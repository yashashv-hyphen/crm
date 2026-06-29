import api from './axios'

export const listUsers = () => api.get('/users')

export const createUser = (data) => api.post('/users', data)

export const updateUser = (id, data) => api.patch(`/users/${id}`, data)

export const deactivateUser = (id) => api.patch(`/users/${id}/deactivate`)

export const activateUser = (id) => api.patch(`/users/${id}/activate`)
