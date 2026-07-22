import api from './api';

export async function login(password: string): Promise<string> {
  const { data } = await api.post('/auth/login', { password });
  return data.access_token;
}

export async function verifyToken(): Promise<boolean> {
  try {
    const { data } = await api.get('/auth/verify');
    return data.valid;
  } catch {
    return false;
  }
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await api.post('/settings/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  });
}
