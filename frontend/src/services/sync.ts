import api from './api';

export interface SyncLog {
  id: number;
  sync_type: string;
  status: string;
  records_processed: number | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface SyncStatus {
  is_running: boolean;
  latest_sync: SyncLog | null;
}

export async function triggerLDAPSync(): Promise<SyncLog> {
  const { data } = await api.post('/sync/ldap');
  return data;
}

export async function triggerUserStatusSync(): Promise<SyncLog> {
  const { data } = await api.post('/sync/ldap/user-status');
  return data;
}

export async function getSyncLogs(params?: Record<string, unknown>) {
  const { data } = await api.get('/sync/logs', { params });
  return data;
}

export async function getSyncStatus(): Promise<SyncStatus> {
  const { data } = await api.get('/sync/status');
  return data;
}
