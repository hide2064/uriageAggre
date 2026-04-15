import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getSummary  = ()            => api.get('/summary')
export const getData     = (page = 1, pageSize = 100) =>
  api.get('/data', { params: { page, page_size: pageSize } })

export const importFiles = (files) => {
  const form = new FormData()
  for (const f of files) form.append('files', f)
  return api.post('/import', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

export const getConfig    = (type)          => api.get(`/config/${type}`)
export const updateConfig = (type, content) => api.put(`/config/${type}`, { content })

export const triggerExport  = ()  => api.post('/export')
export const downloadExport = ()  => window.open('/api/export/download', '_blank')
