import api from './api';

export interface Computer {
  id: number;
  name: string;
  distinguished_name: string;
  ip_address: string | null;
  operating_system: string | null;
  os_version: string | null;
  description: string | null;
  status: 'active' | 'disabled';
  site: string | null;
  department: string | null;
  days_since_logon: number | null;
  last_logon_timestamp: string | null;
  created_at: string;
  updated_at: string;
}

export async function listComputers(params?: Record<string, unknown>) {
  const { data } = await api.get('/computers/', { params });
  return data;
}

export async function getComputer(id: number): Promise<Computer> {
  const { data } = await api.get(`/computers/${id}`);
  return data;
}

export async function createComputer(body: Partial<Computer>): Promise<Computer> {
  const { data } = await api.post('/computers/', body);
  return data;
}

export async function updateComputer(id: number, body: Partial<Computer>): Promise<Computer> {
  const { data } = await api.put(`/computers/${id}`, body);
  return data;
}

export async function deleteComputer(id: number): Promise<void> {
  await api.delete(`/computers/${id}`);
}

export interface ComputerFilterOptions {
  operating_systems: string[];
  departments: string[];
  sites: string[];
}

export async function getComputerFilterOptions(): Promise<ComputerFilterOptions> {
  const { data } = await api.get('/computers/filter-options');
  return data;
}
