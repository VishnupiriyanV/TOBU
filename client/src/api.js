import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// ── Unwrap envelope: { ok, data } → data ──
const unwrap = (res) => res.data.data;

// ── Search ──
export const searchHybrid = (payload) =>
  api.post('/search/hybrid', payload).then(unwrap);

export const searchSemantic = (query, limit = 20) =>
  api.post(`/search/semantic?query=${encodeURIComponent(query)}&limit=${limit}`).then(unwrap);

export const searchKeyword = (query) =>
  api.post(`/search/keyword?query=${encodeURIComponent(query)}`).then(unwrap);

// ── Jobs ──
export const getJobs = (status = null, limit = 100) => {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  params.set('limit', limit);
  return api.get(`/jobs/?${params}`).then(unwrap);
};

export const getJob = (id) =>
  api.get(`/jobs/${id}`).then(unwrap);

export const retryJob = (id) =>
  api.post(`/jobs/${id}/retry`).then(unwrap);

export const cancelJob = (id) =>
  api.post(`/jobs/${id}/cancel`).then(unwrap);

// ── Ingest ──
export const ingestFile = (filePath, sourceType = 'video', maxRetries = 3) =>
  api.post('/ingest/file', { file_path: filePath, source_type: sourceType, max_retries: maxRetries }).then(unwrap);

export const ingestFolder = (folderPath, recursive = true) =>
  api.post('/ingest/folder', { folder_path: folderPath, recursive }).then(unwrap);

export const reindexFile = (filePath) =>
  api.post('/ingest/reindex', { file_path: filePath }).then(unwrap);

export const deleteFile = (filePath) =>
  api.delete(`/ingest/file?file_path=${encodeURIComponent(filePath)}`).then(unwrap);

// ── Media ──
export const getMediaDetail = (id) =>
  api.get(`/media/${id}`).then(unwrap);

export const getMediaSegments = (id, limit = 200) =>
  api.get(`/media/${id}/segments?limit=${limit}`).then(unwrap);

export const getMediaServeUrl = (filePath) => 
  `/api/v1/media/serve?file_path=${encodeURIComponent(filePath)}`;

export const openMediaNative = (filePath) =>
  api.post('/media/open', { file_path: filePath }).then(unwrap);

// ── System ──
export const getHealth = () =>
  api.get('/health').then(unwrap);

export const getSystemStatus = () =>
  api.get('/system/status').then(unwrap);

export const getIntegrity = () =>
  api.get('/system/integrity').then(unwrap);

export const createBackup = (label = null) => {
  const params = label ? `?label=${encodeURIComponent(label)}` : '';
  return api.post(`/system/backup${params}`).then(unwrap);
};

export const browseFile = () =>
  api.get('/system/browse-file').then(unwrap);

export const browseFolder = () =>
  api.get('/system/browse-folder').then(unwrap);


export default api;
