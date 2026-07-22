import api from './api';

export interface User {
  id: number;
  sam_account_name: string;
  display_name: string | null;
  email: string | null;
  department: string | null;
  distinguished_name: string;
  group_count: number;
  site: string | null;
  status: string | null;
  uac_flags: string | null;
  lockout_time: string | null;
  bad_pwd_count: number | null;
  created_at: string;
  updated_at: string;
}

export interface UserFilterOptions {
  departments: string[];
  sites: string[];
}

export interface UserGroupInfo {
  group_id: number;
  group_name: string;
  group_type: string;
  description: string | null;
}

export async function getUserFilterOptions(): Promise<UserFilterOptions> {
  const { data } = await api.get('/users/filter-options');
  return data;
}

export async function listUsers(params?: Record<string, unknown>) {
  const { data } = await api.get('/users/', { params });
  return data;
}

export async function getUser(id: number): Promise<User> {
  const { data } = await api.get(`/users/${id}`);
  return data;
}

export async function createUser(body: Partial<User>): Promise<User> {
  const { data } = await api.post('/users/', body);
  return data;
}

export async function updateUser(id: number, body: Partial<User>): Promise<User> {
  const { data } = await api.put(`/users/${id}`, body);
  return data;
}

export async function deleteUser(id: number): Promise<void> {
  await api.delete(`/users/${id}`);
}

export async function getUserGroups(id: number): Promise<UserGroupInfo[]> {
  const { data } = await api.get(`/users/${id}/groups`);
  return data;
}

export async function unlockUser(id: number): Promise<User> {
  const { data } = await api.post(`/users/${id}/unlock`);
  return data;
}
