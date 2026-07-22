import api from './api';

export interface DashboardStats {
  total_computers: number;
  active_computers: number;
  disabled_computers: number;
  total_users: number;
  total_groups: number;
  last_sync_at: string | null;
  last_sync_status: string | null;
  os_distribution: { name: string; count: number }[];
}

export interface RecentActivity {
  id: number;
  activity_type: string;
  description: string;
  detail: string;
  timestamp: string;
  status: string | null;
}

export async function getStats(): Promise<DashboardStats> {
  const { data } = await api.get('/dashboard/stats');
  return data;
}

export async function getRecentActivities(limit = 10): Promise<RecentActivity[]> {
  const { data } = await api.get('/dashboard/recent-activities', { params: { limit } });
  return data;
}
