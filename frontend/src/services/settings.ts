import api from './api';

export async function getSettings(): Promise<Record<string, string>> {
  const { data } = await api.get('/settings/');
  return data;
}

export async function updateSettings(settings: Record<string, string>): Promise<void> {
  await api.put('/settings/', { settings });
}

export async function discoverAD(domain: string): Promise<{
  server_url: string;
  base_dn: string;
  domain: string;
}> {
  const { data } = await api.post('/settings/discover-ad', { domain });
  return data;
}

export async function testLDAPConnection(): Promise<{ status: string; message: string }> {
  const { data } = await api.post('/settings/test-connection');
  return data;
}

export interface LocationInfo {
  city: string;
  region: string;
  base_dn: string;
}

export async function discoverLocations(): Promise<{ locations: LocationInfo[] }> {
  const { data } = await api.post('/settings/discover-locations');
  return data;
}
