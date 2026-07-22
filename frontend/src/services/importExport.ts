import api from './api';

export async function importFile(file: File, entityType: string) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('entity_type', entityType);
  const { data } = await api.post('/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function exportFile(entityType: string, format: string, filename: string) {
  const response = await api.get(`/export/${entityType}`, {
    params: { format },
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
