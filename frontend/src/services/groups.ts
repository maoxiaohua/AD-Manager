import api from './api';

export interface ADGroup {
  id: number;
  name: string;
  display_name: string | null;
  distinguished_name: string;
  group_type: string;
  group_scope: string;
  description: string | null;
  email: string | null;
  member_count: number;
  end_user_email: string | null;
  jira_ticket: string | null;
  assigned_at: string | null;
  site: string | null;
  department: string | null;
  created_at: string;
  updated_at: string;
}

export interface GroupMember {
  id: number;
  member_dn: string;
  user_id: number | null;
  sam_account_name: string | null;
  display_name: string | null;
}

export interface GroupDetail extends ADGroup {
  members: GroupMember[];
}

export async function listGroups(params?: Record<string, unknown>) {
  const { data } = await api.get('/groups/', { params });
  return data;
}

export async function getGroup(id: number): Promise<ADGroup> {
  const { data } = await api.get(`/groups/${id}`);
  return data;
}

export async function getGroupDetail(id: number): Promise<GroupDetail> {
  const { data } = await api.get(`/groups/${id}/detail`);
  return data;
}

export async function createGroup(body: Partial<ADGroup>): Promise<ADGroup> {
  const { data } = await api.post('/groups/', body);
  return data;
}

export async function updateGroup(id: number, body: Partial<ADGroup>): Promise<ADGroup> {
  const { data } = await api.put(`/groups/${id}`, body);
  return data;
}

export async function deleteGroup(id: number): Promise<void> {
  await api.delete(`/groups/${id}`);
}

export interface GroupFilterOptions {
  departments: string[];
  sites: string[];
}

export async function getGroupFilterOptions(): Promise<GroupFilterOptions> {
  const { data } = await api.get('/groups/filter-options');
  return data;
}
