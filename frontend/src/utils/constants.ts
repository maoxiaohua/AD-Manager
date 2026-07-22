const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const API = `${API_BASE_URL}/api`;

export const STATUS_OPTIONS = [
  { label: 'Active', value: 'active' },
  { label: 'Disabled', value: 'disabled' },
  { label: 'Locked', value: 'locked' },
];

export const GROUP_TYPE_OPTIONS = [
  { label: 'Security', value: 'security' },
  { label: 'Distribution', value: 'distribution' },
];

export const GROUP_SCOPE_OPTIONS = [
  { label: 'Domain Local', value: 'domain_local' },
  { label: 'Global', value: 'global' },
  { label: 'Universal', value: 'universal' },
];

export const SYNC_SCHEDULE_PRESETS = [
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every 6 hours', value: '0 */6 * * *' },
  { label: 'Daily at 2:00 AM', value: '0 2 * * *' },
  { label: 'Daily at 6:00 AM', value: '0 6 * * *' },
  { label: 'Weekly (Mon 2 AM)', value: '0 2 * * 1' },
  { label: 'Disabled', value: 'disabled' },
];
