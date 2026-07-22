import dayjs from 'dayjs';

/**
 * Parse a backend datetime string as UTC.
 * Backend stores UTC but may serialize without timezone suffix.
 * Detect and append 'Z' if missing so dayjs treats it as UTC, not local time.
 */
function parseUTC(dateStr: string): dayjs.Dayjs {
  const hasTimezone = /[+-]\d{2}:\d{2}$/.test(dateStr) || dateStr.endsWith('Z');
  return hasTimezone ? dayjs(dateStr) : dayjs(dateStr + 'Z');
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'N/A';
  return parseUTC(dateStr).format('YYYY-MM-DD HH:mm:ss');
}

export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return 'Never';
  const d = parseUTC(dateStr);
  const now = dayjs();
  const hours = now.diff(d, 'hour');
  if (hours < 1) return 'Just now';
  if (hours < 24) return `${hours}h ago`;
  const days = now.diff(d, 'day');
  if (days < 7) return `${days}d ago`;
  return d.format('YYYY-MM-DD');
}

export function extractComputerName(dn: string): string {
  const match = dn.match(/CN=([^,]+)/);
  return match ? match[1] : dn;
}

export function extractOUDN(dn: string): string | null {
  const idx = dn.indexOf(',');
  return idx > 0 ? dn.substring(idx + 1).trim() : null;
}
