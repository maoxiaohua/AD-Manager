import { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Button, Input, Space, Drawer, Form, Popconfirm, Switch,
  Tag, message, Tooltip, Dropdown, Empty, Skeleton, Result, Upload,
  Select, Descriptions,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined,
  UploadOutlined, DownloadOutlined, ReloadOutlined, ExportOutlined,
  TeamOutlined, UserOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { listGroups, createGroup, updateGroup, deleteGroup, getGroupDetail, getGroupFilterOptions } from '../../services/groups';
import type { ADGroup, GroupDetail, GroupMember, GroupFilterOptions } from '../../services/groups';
import { importFile, exportFile } from '../../services/importExport';
import { formatRelativeTime } from '../../utils/formatters';
export default function GroupsPage() {
  const [data, setData] = useState<ADGroup[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState<string | undefined>();
  const [showAll, setShowAll] = useState(false);  // default: unassigned only
  const [filterOptions, setFilterOptions] = useState<GroupFilterOptions>({ departments: [], sites: [] });
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<ADGroup | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailGroup, setDetailGroup] = useState<GroupDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (search) params.search = search;
      if (departmentFilter) params.department = departmentFilter;
      if (!showAll) params.has_members = false;
      const result = await listGroups(params);
      setData(result.items);
      setTotal(result.total);
    } catch {
      setError('Failed to load groups');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, departmentFilter, showAll]);

  useEffect(() => {
    fetchData();
    getGroupFilterOptions().then(setFilterOptions).catch(() => {});
  }, [fetchData]);

  const openCreateDrawer = () => {
    setEditingGroup(null);
    form.resetFields();
    setDrawerOpen(true);
  };

  const openEditDrawer = (group: ADGroup) => {
    setEditingGroup(group);
    form.setFieldsValue(group);
    setDrawerOpen(true);
  };

  const openDetailDrawer = async (group: ADGroup) => {
    setDetailGroup(null);
    setDetailLoading(true);
    setDetailOpen(true);
    try {
      const detail = await getGroupDetail(group.id);
      setDetailGroup(detail);
    } catch {
      message.error('Failed to load group detail');
    } finally {
      setDetailLoading(false);
    }
  };

  const onDrawerSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editingGroup) {
        await updateGroup(editingGroup.id, values);
        message.success('Group updated');
      } else {
        await createGroup(values);
        message.success('Group created');
      }
      setDrawerOpen(false);
      fetchData();
    } catch {
      message.error('Operation failed');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteGroup(id);
      message.success('Group deleted');
      fetchData();
    } catch {
      message.error('Failed to delete');
    }
  };

  const handleInlineSave = async (group: ADGroup, field: string, value: string) => {
    try {
      await updateGroup(group.id, { [field]: value || null });
      message.success('Saved');
      setEditingCell(null);
      fetchData();
    } catch {
      message.error('Save failed');
    }
  };

  const handleImport = async (file: File) => {
    try {
      await importFile(file, 'groups');
      message.success('Import completed');
      fetchData();
    } catch {
      message.error('Import failed');
    }
    return false;
  };

  const columns: ColumnsType<ADGroup> = [
    {
      title: 'Hostname', dataIndex: 'name', key: 'name', width: 260,
      render: (v: string, record) => (
        <a onClick={() => openDetailDrawer(record)}>{v}</a>
      ),
    },
    { title: 'Site', dataIndex: 'site', key: 'site', width: 120, render: (v: string | null) => v ? <Tag color="blue">{v}</Tag> : '-' },
    { title: 'OU', dataIndex: 'department', key: 'dept', width: 160, render: (v: string | null) => v || '-' },
    { title: 'Display Name', dataIndex: 'display_name', key: 'display', width: 180, render: (v: string | null) => v || '-' },
    {
      title: 'End User Email', dataIndex: 'end_user_email', key: 'email', width: 240,
      render: (v: string | null, record) => {
        const key = `${record.id}-email`;
        const assigned = record.assigned_at ? ` · assigned ${formatRelativeTime(record.assigned_at)}` : '';
        return editingCell === key ? (
          <Input autoFocus size="small" defaultValue={v || ''}
            onPressEnter={(e) => handleInlineSave(record, 'end_user_email', (e.target as HTMLInputElement).value)}
            onBlur={(e) => handleInlineSave(record, 'end_user_email', e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape') setEditingCell(null); }} />
        ) : (
          <div onClick={() => setEditingCell(key)} style={{ cursor: 'pointer', minHeight: 22, padding: '2px 4px', color: v ? undefined : '#bbb' }}>
            {v || 'Click to add...'}
            {v && <span style={{ fontSize: 11, color: '#999' }}>{assigned}</span>}
          </div>
        );
      },
    },
    {
      title: 'Jira Ticket', dataIndex: 'jira_ticket', key: 'jira', width: 140,
      render: (v: string | null, record) => {
        const key = `${record.id}-jira`;
        return editingCell === key ? (
          <Input autoFocus size="small" defaultValue={v || ''}
            onPressEnter={(e) => handleInlineSave(record, 'jira_ticket', (e.target as HTMLInputElement).value)}
            onBlur={(e) => handleInlineSave(record, 'jira_ticket', e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape') setEditingCell(null); }} />
        ) : (
          <div onClick={() => setEditingCell(key)} style={{ cursor: 'pointer', minHeight: 22, padding: '2px 4px', color: v ? undefined : '#bbb' }}>
            {v || 'Click to add...'}
          </div>
        );
      },
    },
    {
      title: 'Members', dataIndex: 'member_count', key: 'members', width: 100,
      render: (v: number, record) => (
        <a onClick={() => openDetailDrawer(record)}>
          <Tag color={v > 0 ? 'blue' : 'default'} icon={<TeamOutlined />}>{v}</Tag>
        </a>
      ),
    },
    {
      title: 'Created', dataIndex: 'created_at', key: 'created', width: 140,
      render: (v: string) => formatRelativeTime(v),
    },
    {
      title: 'Actions', key: 'actions', width: 140, fixed: 'right' as const,
      render: (_, record) => (
        <Space>
          <Tooltip title="Edit"><Button size="small" icon={<EditOutlined />} onClick={() => openEditDrawer(record)} /></Tooltip>
          <Popconfirm title="Delete?" onConfirm={() => handleDelete(record.id)}>
            <Tooltip title="Delete"><Button size="small" danger icon={<DeleteOutlined />} /></Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const memberColumns: ColumnsType<GroupMember> = [
    { title: 'SAM Account', dataIndex: 'sam_account_name', key: 'sam', width: 160, render: (v: string | null) => v || '-' },
    { title: 'Display Name', dataIndex: 'display_name', key: 'name', width: 200, render: (v: string | null) => v || '-' },
    {
      title: 'Status', key: 'status', width: 120,
      render: (_, record) => record.user_id
        ? <Tag color="green" icon={<UserOutlined />}>Synced</Tag>
        : <Tag color="orange">Unresolved DN</Tag>,
    },
    { title: 'DN', dataIndex: 'member_dn', key: 'dn', ellipsis: true, render: (v: string) => <Tooltip title={v}><span style={{ fontSize: 12 }}>{v}</span></Tooltip> },
  ];

  if (error) return <Result status="error" title="Error" subTitle={error} extra={<Button type="primary" icon={<ReloadOutlined />} onClick={fetchData}>Retry</Button>} />;

  return (
    <>
      <Card style={{ borderRadius: 8, marginBottom: 16 }}>
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space wrap>
            <Input
              prefix={<SearchOutlined />}
              placeholder="Search name, display name..."
              allowClear
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              style={{ width: 280 }}
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
            <Space>
              <Switch checked={showAll} onChange={setShowAll} />
              <span style={{ fontSize: 13, color: '#666' }}>
                {showAll ? 'All Hostnames' : 'Unassigned Only'}
              </span>
            </Space>
          </Space>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>Add Group</Button>
            <Upload accept=".csv,.xlsx" showUploadList={false} beforeUpload={handleImport}>
              <Button icon={<UploadOutlined />}>Import</Button>
            </Upload>
            <Dropdown menu={{
              items: [
                { key: 'csv', label: 'Export CSV', icon: <DownloadOutlined />, onClick: () => exportFile('groups', 'csv', 'groups.csv') },
                { key: 'xlsx', label: 'Export Excel', icon: <DownloadOutlined />, onClick: () => exportFile('groups', 'xlsx', 'groups.xlsx') },
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
          <Empty description="No groups found. Run an LDAP sync to import groups." image={Empty.PRESENTED_IMAGE_SIMPLE}>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>Add First Group</Button>
          </Empty>
        ) : (
          <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
            pagination={{ current: page, pageSize, total, showSizeChanger: true,
              showTotal: (t) => `Total ${t} groups`,
              onChange: (p, ps) => { setPage(p); setPageSize(ps); },
            }}
            scroll={{ x: 1200 }} size="middle"
          />
        )}
      </Card>

      {/* CRUD Drawer */}
      <Drawer
        title={editingGroup ? 'Edit Group' : 'Add Group'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={520}
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button type="primary" onClick={onDrawerSubmit}>Save</Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="SAM Account Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Domain Admins" />
          </Form.Item>
          <Form.Item name="distinguished_name" label="Distinguished Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. CN=Domain Admins,CN=Users,DC=example,DC=com" disabled={!!editingGroup} />
          </Form.Item>
          <Form.Item name="display_name" label="Display Name">
            <Input placeholder="e.g. Domain Admins" />
          </Form.Item>
          <Form.Item name="end_user_email" label="End User Email">
            <Input placeholder="e.g. user@company.com" />
          </Form.Item>
          <Form.Item name="jira_ticket" label="Jira Ticket">
            <Input placeholder="e.g. PROJ-1234" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="Group description..." />
          </Form.Item>
        </Form>
      </Drawer>

      {/* Detail Drawer */}
      <Drawer
        title={detailGroup ? `Group: ${detailGroup.name}` : 'Group Details'}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        width={700}
      >
        {detailLoading ? <Skeleton active /> : detailGroup ? (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 24 }}>
              <Descriptions.Item label="Name">{detailGroup.name}</Descriptions.Item>
              <Descriptions.Item label="Display Name">{detailGroup.display_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="Type"><Tag color={detailGroup.group_type === 'security' ? 'blue' : 'green'}>{detailGroup.group_type}</Tag></Descriptions.Item>
              <Descriptions.Item label="Scope"><Tag>{detailGroup.group_scope?.replace('_', ' ')}</Tag></Descriptions.Item>
              <Descriptions.Item label="Email">{detailGroup.email || '-'}</Descriptions.Item>
              <Descriptions.Item label="DN" span={2}>{detailGroup.distinguished_name}</Descriptions.Item>
              <Descriptions.Item label="Description" span={2}>{detailGroup.description || '-'}</Descriptions.Item>
            </Descriptions>
            <Card title={`Members (${detailGroup.members.length})`} size="small">
              <Table
                dataSource={detailGroup.members}
                columns={memberColumns}
                rowKey="id"
                pagination={detailGroup.members.length > 20 ? { pageSize: 20 } : false}
                size="small"
                scroll={{ x: 600 }}
              />
            </Card>
          </>
        ) : <Empty description="Failed to load group details" />}
      </Drawer>
    </>
  );
}
