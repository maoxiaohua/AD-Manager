import { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Button, Input, Select, Space, Drawer, Form, Popconfirm,
  Tag, message, Tooltip, Dropdown, Empty, Skeleton, Result, Upload,
} from 'antd';
import {
  PlusOutlined, EditOutlined, SearchOutlined,
  UploadOutlined, DownloadOutlined, ReloadOutlined, ExportOutlined,
  TeamOutlined, UnlockOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { listUsers, createUser, updateUser, getUserGroups, getUserFilterOptions, unlockUser } from '../../services/users';
import type { User, UserGroupInfo, UserFilterOptions } from '../../services/users';
import { importFile, exportFile } from '../../services/importExport';
import { formatRelativeTime } from '../../utils/formatters';
import { STATUS_OPTIONS } from '../../utils/constants';

export default function UsersPage() {
  const [data, setData] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [siteFilter, setSiteFilter] = useState<string | undefined>();
  const [departmentFilter, setDepartmentFilter] = useState<string | undefined>();
  const [filterOptions, setFilterOptions] = useState<UserFilterOptions>({ departments: [], sites: [] });
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [groupDrawerOpen, setGroupDrawerOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userGroups, setUserGroups] = useState<UserGroupInfo[]>([]);
  const [groupLoading, setGroupLoading] = useState(false);
  const [unlockingId, setUnlockingId] = useState<number | null>(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (search) params.search = search;
      if (statusFilter) params.status_filter = statusFilter;
      if (siteFilter) params.site = siteFilter;
      if (departmentFilter) params.department = departmentFilter;
      const result = await listUsers(params);
      setData(result.items);
      setTotal(result.total);
    } catch {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, statusFilter, siteFilter, departmentFilter]);

  useEffect(() => {
    fetchData();
    getUserFilterOptions().then(setFilterOptions).catch(() => {});
  }, [fetchData]);

  const openCreateDrawer = () => {
    setEditingUser(null);
    form.resetFields();
    setDrawerOpen(true);
  };

  const openEditDrawer = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue(user);
    setDrawerOpen(true);
  };

  const onDrawerSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editingUser) {
        await updateUser(editingUser.id, values);
        message.success('User updated');
      } else {
        await createUser(values);
        message.success('User created');
      }
      setDrawerOpen(false);
      fetchData();
    } catch {
      message.error('Operation failed');
    }
  };

  const handleUnlock = async (id: number) => {
    setUnlockingId(id);
    try {
      await unlockUser(id);
      message.success('Account unlocked');
      fetchData();
    } catch {
      message.error('Unlock failed');
    } finally {
      setUnlockingId(null);
    }
  };

  const handleImport = async (file: File) => {
    try {
      await importFile(file, 'users');
      message.success('Import completed');
      fetchData();
    } catch {
      message.error('Import failed');
    }
    return false;
  };

  const openUserGroupsDrawer = async (user: User) => {
    setSelectedUser(user);
    setGroupDrawerOpen(true);
    setGroupLoading(true);
    try {
      const groups = await getUserGroups(user.id);
      setUserGroups(groups);
    } catch {
      message.error('Failed to load groups');
    } finally {
      setGroupLoading(false);
    }
  };

  const columns: ColumnsType<User> = [
    { title: 'Username', dataIndex: 'sam_account_name', key: 'sam', width: 160 },
    { title: 'Display Name', dataIndex: 'display_name', key: 'name', width: 200, render: (v: string | null) => v || '-' },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 180,
      render: (v: string | null, record) => {
        if (!v) return '-';
        const colors: Record<string, string> = { active: 'green', disabled: 'red', locked: 'orange' };
        const suffix = record.lockout_time ? ` · locked ${formatRelativeTime(record.lockout_time)}` : '';
        const badPwd = record.bad_pwd_count != null && record.bad_pwd_count > 0
          ? ` · badPwd: ${record.bad_pwd_count}` : '';
        const flags = record.uac_flags ? <div style={{ fontSize: 10, color: '#999' }}>{record.uac_flags}</div> : null;
        return <span><Tag color={colors[v] || 'default'}>{v}</Tag>{suffix}{badPwd}{flags}</span>;
      },
    },
    { title: 'Site', dataIndex: 'site', key: 'site', width: 120, render: (v: string | null) => v ? <Tag color="blue">{v}</Tag> : '-' },
    { title: 'Email', dataIndex: 'email', key: 'email', width: 220, render: (v: string | null) => v || '-' },
    { title: 'Department', dataIndex: 'department', key: 'dept', width: 160, render: (v: string | null) => v || '-' },
    {
      title: 'Hostnames', dataIndex: 'group_count', key: 'hostnames', width: 110,
      render: (v: number, record) => (
        <a onClick={() => openUserGroupsDrawer(record)}>
          <Tag color={v > 0 ? 'blue' : 'default'} icon={<TeamOutlined />}>{v}</Tag>
        </a>
      ),
    },
    {
      title: 'Created', dataIndex: 'created_at', key: 'created', width: 140,
      render: (v: string) => formatRelativeTime(v),
    },
    {
      title: 'Actions', key: 'actions', width: 200, fixed: 'right' as const,
      render: (_, record) => (
        <Space>
          {record.status === 'locked' && (
            <Popconfirm
              title={`Unlock account "${record.sam_account_name}"?`}
              onConfirm={() => handleUnlock(record.id)}
              okText="Unlock"
              cancelText="Cancel"
              disabled={unlockingId !== null}
            >
              <Tooltip title="Unlock">
                <Button
                  size="small"
                  type="primary"
                  ghost
                  icon={<UnlockOutlined />}
                  loading={unlockingId === record.id}
                  disabled={unlockingId !== null && unlockingId !== record.id}
                  aria-label={`Unlock ${record.sam_account_name}`}
                />
              </Tooltip>
            </Popconfirm>
          )}
          <Tooltip title="Edit">
            <Button size="small" icon={<EditOutlined />} onClick={() => openEditDrawer(record)}
              aria-label={`Edit ${record.sam_account_name}`} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (error) return <Result status="error" title="Error" subTitle={error} extra={<Button type="primary" icon={<ReloadOutlined />} onClick={fetchData}>Retry</Button>} />;

  return (
    <>
      <Card style={{ borderRadius: 8, marginBottom: 16 }}>
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space wrap>
            <Input
              prefix={<SearchOutlined />}
              placeholder="Search username, name, email..."
              allowClear
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              style={{ width: 280 }}
            />
            <Select
              placeholder="Status"
              allowClear
              value={statusFilter}
              onChange={(v) => { setStatusFilter(v); setPage(1); }}
              options={STATUS_OPTIONS}
              style={{ width: 130 }}
            />
            <Select
              placeholder="Site"
              allowClear
              showSearch
              value={siteFilter}
              onChange={(v) => { setSiteFilter(v); setPage(1); }}
              options={filterOptions.sites.map(s => ({ label: s, value: s }))}
              style={{ width: 150 }}
            />
            <Select
              placeholder="Department (OU)"
              allowClear
              showSearch
              value={departmentFilter}
              onChange={(v) => { setDepartmentFilter(v); setPage(1); }}
              options={filterOptions.departments.map(d => ({ label: d, value: d }))}
              style={{ width: 180 }}
            />
          </Space>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>Add User</Button>
            <Upload accept=".csv,.xlsx" showUploadList={false} beforeUpload={handleImport}>
              <Button icon={<UploadOutlined />}>Import</Button>
            </Upload>
            <Dropdown menu={{
              items: [
                { key: 'csv', label: 'Export CSV', icon: <DownloadOutlined />, onClick: () => exportFile('users', 'csv', 'users.csv') },
                { key: 'xlsx', label: 'Export Excel', icon: <DownloadOutlined />, onClick: () => exportFile('users', 'xlsx', 'users.xlsx') },
                { type: 'divider' },
                { key: 'bindings-csv', label: 'Export Bindings CSV', icon: <DownloadOutlined />, onClick: () => exportFile('user-bindings', 'csv', 'user_bindings.csv') },
                { key: 'bindings-xlsx', label: 'Export Bindings Excel', icon: <DownloadOutlined />, onClick: () => exportFile('user-bindings', 'xlsx', 'user_bindings.xlsx') },
              ],
            }}>
              <Button icon={<ExportOutlined />}>Export</Button>
            </Dropdown>
            <Button icon={<ReloadOutlined />} onClick={fetchData} />
          </Space>
        </Space>
      </Card>

      <Card style={{ borderRadius: 8 }}>
        {loading ? <Skeleton active paragraph={{ rows: 8 }} /> : data.length === 0 && !search ? (
          <Empty description="No users found. Run an LDAP sync to import from AD." image={Empty.PRESENTED_IMAGE_SIMPLE}>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>Add First User</Button>
          </Empty>
        ) : (
          <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
            pagination={{ current: page, pageSize, total, showSizeChanger: true,
              showTotal: (t) => `Total ${t} users`,
              onChange: (p, ps) => { setPage(p); setPageSize(ps); },
            }}
            scroll={{ x: 1000 }} size="middle"
          />
        )}
      </Card>

      <Drawer
        title={editingUser ? 'Edit User' : 'Add User'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button type="primary" onClick={onDrawerSubmit}>Save</Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="sam_account_name" label="SAM Account Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. jdoe" />
          </Form.Item>
          <Form.Item name="distinguished_name" label="Distinguished Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. CN=John Doe,CN=Users,DC=example,DC=com" disabled={!!editingUser} />
          </Form.Item>
          <Form.Item name="display_name" label="Display Name">
            <Input placeholder="e.g. John Doe" />
          </Form.Item>
          <Form.Item name="email" label="Email">
            <Input placeholder="e.g. jdoe@example.com" />
          </Form.Item>
          <Form.Item name="department" label="Department">
            <Input placeholder="e.g. Engineering" />
          </Form.Item>
        </Form>
      </Drawer>

      {/* User Groups Drawer */}
      <Drawer
        title={selectedUser ? `Hostnames for ${selectedUser.sam_account_name}` : 'User Hostnames'}
        open={groupDrawerOpen}
        onClose={() => setGroupDrawerOpen(false)}
        width={560}
      >
        {groupLoading ? <Skeleton active /> : userGroups.length === 0 ? (
          <Empty description="No hostnames found for this user" />
        ) : (
          <Table
            dataSource={userGroups}
            rowKey="group_id"
            columns={[
              { title: 'Hostname (Group)', dataIndex: 'group_name', key: 'name', width: 300 },
              { title: 'Type', dataIndex: 'group_type', key: 'type', width: 100, render: (v: string) => <Tag color={v === 'security' ? 'blue' : 'green'}>{v}</Tag> },
              { title: 'Description', dataIndex: 'description', key: 'desc', render: (v: string | null) => v || '-' },
            ]}
            pagination={userGroups.length > 20 ? { pageSize: 20 } : false}
            size="small"
          />
        )}
      </Drawer>
    </>
  );
}
