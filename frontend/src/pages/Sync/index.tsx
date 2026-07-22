import { useEffect, useState, useCallback, useRef } from 'react';
import {
  Card, Button, Table, Tag, Space, Alert, Typography, message,
  Skeleton, Empty, Upload, Select,
} from 'antd';
import {
  SyncOutlined, ReloadOutlined, UploadOutlined, HistoryOutlined,
  CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined, TeamOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { triggerLDAPSync, triggerUserStatusSync, getSyncLogs, getSyncStatus } from '../../services/sync';
import type { SyncLog, SyncStatus } from '../../services/sync';
import { importFile } from '../../services/importExport';
import { formatRelativeTime } from '../../utils/formatters';

export default function SyncPage() {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [logs, setLogs] = useState<SyncLog[]>([]);
  const [logTotal, setLogTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [userStatusSyncing, setUserStatusSyncing] = useState(false);
  const [logPage, setLogPage] = useState(1);
  const [logPageSize, setLogPageSize] = useState(20);
  const [importEntityType, setImportEntityType] = useState<string>('computers');
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const s = await getSyncStatus();
      setStatus(s);

      const l = await getSyncLogs({ page: logPage, page_size: logPageSize });
      setLogs(l.items);
      setLogTotal(l.total);
    } catch { /* ignore */ }
  }, [logPage, logPageSize]);

  useEffect(() => {
    setLoading(true);
    fetchStatus().finally(() => setLoading(false));
  }, [fetchStatus]);

  // Poll when syncing
  useEffect(() => {
    if (status?.is_running) {
      pollingRef.current = setInterval(fetchStatus, 3000);
    } else {
      if (pollingRef.current) clearInterval(pollingRef.current);
    }
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [status?.is_running, fetchStatus]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const log = await triggerLDAPSync();
      if (log.status === 'failed') {
        message.error(`Sync failed: ${log.error_message}`);
      } else {
        message.success('LDAP sync triggered successfully');
      }
      await fetchStatus();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleUserStatusSync = async () => {
    setUserStatusSyncing(true);
    try {
      const log = await triggerUserStatusSync();
      if (log.status === 'failed') {
        message.error(`User status sync failed: ${log.error_message}`);
      } else {
        message.success(`User status sync completed — ${log.records_processed ?? 0} users`);
      }
      await fetchStatus();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'User status sync failed');
    } finally {
      setUserStatusSyncing(false);
    }
  };

  const handleImport = async (file: File) => {
    try {
      await importFile(file, importEntityType);
      message.success('Import completed');
      fetchStatus();
    } catch { message.error('Import failed'); }
    return false;
  };

  const SYNC_TYPE_COLORS: Record<string, string> = {
    ldap: 'blue',
    ldap_user_status: 'purple',
  };

  const logColumns: ColumnsType<SyncLog> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: 'Type', dataIndex: 'sync_type', key: 'type', width: 80,
      render: (t: string) => <Tag color={SYNC_TYPE_COLORS[t] || 'default'}>{t.toUpperCase()}</Tag>,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 100,
      render: (s: string) => {
        const icon = s === 'success' ? <CheckCircleOutlined /> : s === 'failed' ? <CloseCircleOutlined /> : <LoadingOutlined />;
        const color = s === 'success' ? 'success' : s === 'failed' ? 'error' : 'processing';
        return <Tag color={color} icon={icon}>{s}</Tag>;
      },
    },
    { title: 'Records', dataIndex: 'records_processed', key: 'records', width: 100 },
    {
      title: 'Started', dataIndex: 'started_at', key: 'started', width: 160,
      render: (v: string | null) => formatRelativeTime(v),
    },
    {
      title: 'Duration',
      key: 'duration',
      width: 120,
      render: (_: unknown, r: SyncLog) => {
        if (!r.started_at || !r.completed_at) return '-';
        const start = new Date(r.started_at).getTime();
        const end = new Date(r.completed_at).getTime();
        const sec = Math.round((end - start) / 1000);
        return sec < 60 ? `${sec}s` : `${Math.floor(sec / 60)}m ${sec % 60}s`;
      },
    },
    {
      title: 'Error', dataIndex: 'error_message', key: 'error', width: 200,
      render: (v: string | null) => v ? <Typography.Text type="danger" ellipsis={{ tooltip: v }}>{v}</Typography.Text> : '-',
    },
  ];

  return (
    <>
      {/* Status Banner */}
      {status && (
        <Alert
          type={status.latest_sync?.status === 'success' ? 'success' : status.latest_sync?.status === 'failed' ? 'error' : 'info'}
          message={
            <Space>
              {status.is_running ? (
                <>
                  <LoadingOutlined spin />
                  <span>
                    {status.latest_sync?.sync_type === 'ldap_user_status'
                      ? 'User status sync' : 'LDAP sync'} is currently running...
                  </span>
                </>
              ) : status.latest_sync ? (
                <>
                  {status.latest_sync.status === 'success' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                  <span>
                    Last sync: {status.latest_sync.sync_type.toUpperCase()} - {status.latest_sync.status}
                    {' · '}
                    {formatRelativeTime(status.latest_sync.completed_at || status.latest_sync.started_at)}
                    {' · '}
                    {status.latest_sync.records_processed ?? 0} records
                  </span>
                </>
              ) : (
                <span>No sync performed yet. Configure LDAP settings and click Sync Now.</span>
              )}
            </Space>
          }
          style={{ marginBottom: 16, borderRadius: 8 }}
          showIcon
        />
      )}

      {/* Action Cards */}
      <Card style={{ borderRadius: 8, marginBottom: 16 }}>
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space wrap>
            <Button
              type="primary"
              size="large"
              icon={status?.is_running ? <LoadingOutlined spin /> : <SyncOutlined />}
              onClick={handleSync}
              loading={syncing}
              disabled={status?.is_running}
              style={{ height: 44, minWidth: 140 }}
            >
              {status?.is_running ? 'Syncing...' : 'Sync Now'}
            </Button>
            <Button
              size="large"
              icon={<TeamOutlined />}
              onClick={handleUserStatusSync}
              loading={userStatusSyncing}
              disabled={status?.is_running}
              style={{ height: 44 }}
            >
              Sync User Status
            </Button>
            <Select
              value={importEntityType}
              onChange={setImportEntityType}
              style={{ width: 130 }}
              options={[
                { label: 'Computers', value: 'computers' },
                { label: 'Users', value: 'users' },
                { label: 'Groups', value: 'groups' },
              ]}
            />
            <Upload accept=".csv,.xlsx" showUploadList={false} beforeUpload={handleImport}>
              <Button size="large" icon={<UploadOutlined />} style={{ height: 44 }}>
                Import CSV/Excel
              </Button>
            </Upload>
          </Space>
          <Button icon={<ReloadOutlined />} onClick={fetchStatus}>Refresh</Button>
        </Space>
      </Card>

      {/* Sync History */}
      <Card
        title={<Space><HistoryOutlined /><span>Sync History</span></Space>}
        style={{ borderRadius: 8 }}
      >
        {loading ? <Skeleton active paragraph={{ rows: 6 }} /> : logs.length === 0 ? (
          <Empty description="No sync history yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Table
            columns={logColumns}
            dataSource={logs}
            rowKey="id"
            pagination={{ total: logTotal, showSizeChanger: true, showTotal: (t) => `Total ${t} sync logs`,
              onChange: (p, ps) => { setLogPage(p); setLogPageSize(ps); },
            }}
            scroll={{ x: 900 }}
            size="middle"
          />
        )}
      </Card>
    </>
  );
}
