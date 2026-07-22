import { useEffect, useState } from 'react';
import { Row, Col, Table, Card, Tag, Typography, Skeleton, Empty, Result, Button, Statistic } from 'antd';
import {
  DesktopOutlined,
  UserOutlined,
  TeamOutlined,
  SyncOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { getStats, getRecentActivities } from '../../services/dashboard';
import type { DashboardStats as Stats, RecentActivity } from '../../services/dashboard';
import StatCard from '../../components/StatCard';
import { formatRelativeTime } from '../../utils/formatters';

const { Title } = Typography;

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, a] = await Promise.all([getStats(), getRecentActivities(10)]);
      setStats(s);
      setActivities(a);
    } catch {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error) {
    return (
      <Result
        status="error"
        title="Failed to load"
        subTitle={error}
        extra={<Button type="primary" icon={<ReloadOutlined />} onClick={fetchData}>Retry</Button>}
      />
    );
  }

  const activityColumns = [
    {
      title: 'Type',
      dataIndex: 'activity_type',
      key: 'type',
      width: 80,
      render: (t: string) => (
        <Tag color={t === 'sync' ? 'blue' : 'green'}>{t.toUpperCase()}</Tag>
      ),
    },
    { title: 'Description', dataIndex: 'description', key: 'desc' },
    { title: 'Detail', dataIndex: 'detail', key: 'detail' },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'time',
      width: 140,
      render: (t: string) => formatRelativeTime(t),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (s: string | null) => {
        if (!s) return null;
        const color = s === 'success' ? 'success' : s === 'failed' ? 'error' : 'processing';
        return <Tag color={color}>{s}</Tag>;
      },
    },
  ];

  return (
    <>
      {loading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title="Computers"
                value={stats?.total_computers || 0}
                icon={<DesktopOutlined />}
                color="#52C41A"
                suffix={
                  <div style={{ fontSize: 12, marginTop: 4 }}>
                    <span style={{ color: '#52C41A' }}>{stats?.active_computers || 0} active</span>
                    {' · '}
                    <span style={{ color: '#FF4D4F' }}>{stats?.disabled_computers || 0} disabled</span>
                  </div>
                }
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <StatCard title="Users" value={stats?.total_users || 0} icon={<UserOutlined />} color="#FAAD14" />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <StatCard title="Groups" value={stats?.total_groups || 0} icon={<TeamOutlined />} color="#13C2C2" />
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} lg={12}>
              <Card
                title={<Title level={5} style={{ margin: 0 }}>Recent Activity</Title>}
                style={{ borderRadius: 8 }}
              >
                {activities.length === 0 ? (
                  <Empty description="No recent activity" />
                ) : (
                  <Table
                    dataSource={activities}
                    columns={activityColumns}
                    rowKey="id"
                    pagination={false}
                    size="middle"
                    scroll={{ x: 'max-content' }}
                  />
                )}
              </Card>
            </Col>

            {stats?.os_distribution && stats.os_distribution.length > 0 && (
              <Col xs={24} lg={12}>
                <Card title={<Title level={5} style={{ margin: 0 }}>OS Distribution</Title>} style={{ borderRadius: 8 }}>
                  {stats.os_distribution.slice(0, 10).map((os: { name: string; count: number }) => {
                    const maxCount = stats.os_distribution[0]?.count || 1;
                    const pct = Math.round((os.count / maxCount) * 100);
                    return (
                      <div key={os.name} style={{ marginBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                          <span>{os.name || 'Unknown'}</span>
                          <span style={{ fontWeight: 600 }}>{os.count}</span>
                        </div>
                        <div style={{ background: '#f0f0f0', borderRadius: 3, height: 6 }}>
                          <div style={{ background: '#1677FF', height: '100%', width: `${pct}%`, borderRadius: 3 }} />
                        </div>
                      </div>
                    );
                  })}
                </Card>
              </Col>
            )}
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} lg={8}>
              <Card title={<Title level={5} style={{ margin: 0 }}>Sync Status</Title>} style={{ borderRadius: 8 }}>
                {stats?.last_sync_at ? (
                  <>
                    <Statistic
                      title="Last Sync"
                      value={formatRelativeTime(stats.last_sync_at)}
                      valueStyle={{ fontSize: 18 }}
                      prefix={<SyncOutlined />}
                    />
                    {stats.last_sync_status && (
                      <Tag
                        color={stats.last_sync_status === 'success' ? 'success' : 'error'}
                        style={{ marginTop: 8 }}
                      >
                        {stats.last_sync_status}
                      </Tag>
                    )}
                  </>
                ) : (
                  <Empty description="No sync data yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </Card>
            </Col>
          </Row>
        </>
      )}
    </>
  );
}
