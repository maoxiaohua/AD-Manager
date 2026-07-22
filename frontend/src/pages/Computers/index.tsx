import { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Button, Input, Select, Space, Drawer, Form, Popconfirm,
  Tag, message, Upload, Dropdown, Tooltip, Empty, Skeleton, Result,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined,
  UploadOutlined, DownloadOutlined, ReloadOutlined, ExportOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  listComputers, createComputer, updateComputer, deleteComputer, getComputerFilterOptions,
} from '../../services/computers';
import type { Computer, ComputerFilterOptions } from '../../services/computers';
import { importFile, exportFile } from '../../services/importExport';
import { formatRelativeTime } from '../../utils/formatters';
import { STATUS_OPTIONS } from '../../utils/constants';

export default function ComputersPage() {
  const [data, setData] = useState<Computer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [departmentFilter, setDepartmentFilter] = useState<string | undefined>();
  const [osFilter, setOsFilter] = useState<string | undefined>();
  const [staleFilter, setStaleFilter] = useState<boolean | undefined>();
  const [filterOptions, setFilterOptions] = useState<ComputerFilterOptions>({ operating_systems: [], departments: [], sites: [] });
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingComputer, setEditingComputer] = useState<Computer | null>(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (search) params.search = search;
      if (statusFilter) params.status_filter = statusFilter;
      if (departmentFilter) params.department = departmentFilter;
      if (osFilter) params.operating_system = osFilter;
      if (staleFilter) params.stale = true;

      const result = await listComputers(params);
      setData(result.items);
      setTotal(result.total);
    } catch {
      setError('Failed to load computers');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, statusFilter, departmentFilter, osFilter, staleFilter]);

  useEffect(() => {
    fetchData();
    getComputerFilterOptions().then(setFilterOptions).catch(() => {});
  }, [fetchData]);

  const openCreateDrawer = () => {
    setEditingComputer(null);
    form.resetFields();
    form.setFieldsValue({ status: 'active' });
    setDrawerOpen(true);
  };

  const openEditDrawer = (computer: Computer) => {
    setEditingComputer(computer);
    form.setFieldsValue(computer);
    setDrawerOpen(true);
  };

  const onDrawerSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editingComputer) {
        await updateComputer(editingComputer.id, values);
        message.success('Computer updated');
      } else {
        await createComputer(values);
        message.success('Computer created');
      }
      setDrawerOpen(false);
      fetchData();
    } catch {
      message.error('Operation failed');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteComputer(id);
      message.success('Computer deleted');
      fetchData();
    } catch {
      message.error('Failed to delete');
    }
  };

  const handleImport = async (file: File) => {
    try {
      await importFile(file, 'computers');
      message.success('Import completed');
      fetchData();
    } catch {
      message.error('Import failed');
    }
    return false;
  };

  const columns: ColumnsType<Computer> = [
    { title: 'Hostname', dataIndex: 'name', key: 'name', width: 180 },
    {
      title: 'Last Seen', dataIndex: 'days_since_logon', key: 'stale', width: 110,
      render: (v: number | null) => {
        if (v === null || v === undefined) return <Tag color="default">Never</Tag>;
        if (v > 90) return <Tag color="red">{v}d ago</Tag>;
        if (v > 30) return <Tag color="orange">{v}d ago</Tag>;
        return <Tag color="green">{v}d ago</Tag>;
      },
    },
    { title: 'Site', dataIndex: 'site', key: 'site', width: 120, render: (v: string | null) => v ? <Tag color="blue">{v}</Tag> : '-' },
    { title: 'OU', dataIndex: 'department', key: 'dept', width: 160, render: (v: string | null) => v || '-' },
    { title: 'IP Address', dataIndex: 'ip_address', key: 'ip', width: 150, render: (v: string | null) => v || '-' },
    { title: 'OS', dataIndex: 'operating_system', key: 'os', width: 180, render: (v: string | null) => v || '-' },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 100,
      render: (s: string) => <Tag color={s === 'active' ? 'success' : 'error'}>{s}</Tag>,
    },
    {
      title: 'Last Logon', dataIndex: 'last_logon_timestamp', key: 'last_logon', width: 140,
      render: (v: string | null) => formatRelativeTime(v),
    },
    {
      title: 'Actions', key: 'actions', width: 140, fixed: 'right' as const,
      render: (_, record) => (
        <Space>
          <Tooltip title="Edit">
            <Button size="small" icon={<EditOutlined />} onClick={() => openEditDrawer(record)} />
          </Tooltip>
          <Popconfirm title="Delete?" onConfirm={() => handleDelete(record.id)}>
            <Tooltip title="Delete"><Button size="small" danger icon={<DeleteOutlined />} /></Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (error) {
    return <Result status="error" title="Error" subTitle={error} extra={
      <Button type="primary" icon={<ReloadOutlined />} onClick={fetchData}>Retry</Button>
    } />;
  }

  return (
    <>
      <Card style={{ borderRadius: 8, marginBottom: 16 }}>
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space wrap>
            <Input
              prefix={<SearchOutlined />}
              placeholder="Search hostname, IP, DN..."
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
              placeholder="Department (OU)"
              allowClear
              showSearch
              value={departmentFilter}
              onChange={(v) => { setDepartmentFilter(v); setPage(1); }}
              options={filterOptions.departments.map(d => ({ label: d, value: d }))}
              style={{ width: 180 }}
            />
            <Select
              placeholder="OS"
              allowClear
              showSearch
              value={osFilter}
              onChange={(v) => { setOsFilter(v); setPage(1); }}
              options={filterOptions.operating_systems.map(o => ({ label: o, value: o }))}
              style={{ width: 200 }}
            />
            <Select placeholder="Stale" allowClear value={staleFilter ? 'yes' : undefined}
              onChange={(v) => setStaleFilter(v === 'yes' ? true : undefined)}
              options={[{ label: 'Stale (>90d)', value: 'yes' }]} style={{ width: 140 }} />
          </Space>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>
              Add Computer
            </Button>
            <Upload accept=".csv,.xlsx" showUploadList={false} beforeUpload={handleImport}>
              <Button icon={<UploadOutlined />}>Import</Button>
            </Upload>
            <Dropdown menu={{
              items: [
                { key: 'csv', label: 'Export CSV', icon: <DownloadOutlined />, onClick: () => exportFile('computers', 'csv', 'computers.csv') },
                { key: 'xlsx', label: 'Export Excel', icon: <DownloadOutlined />, onClick: () => exportFile('computers', 'xlsx', 'computers.xlsx') },
              ],
            }}>
              <Button icon={<ExportOutlined />}>Export</Button>
            </Dropdown>
            <Button icon={<ReloadOutlined />} onClick={fetchData} />
          </Space>
        </Space>
      </Card>

      <Card style={{ borderRadius: 8 }}>
        {loading ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : data.length === 0 && !search && !statusFilter ? (
          <Empty
            description="No computers found. Run an LDAP sync to import from AD."
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>Add First Computer</Button>
          </Empty>
        ) : (
          <Table
            columns={columns}
            dataSource={data}
            rowKey="id"
            loading={loading}
            pagination={{
              current: page,
              pageSize,
              total,
              showSizeChanger: true,
              showTotal: (t) => `Total ${t} computers`,
              onChange: (p, ps) => { setPage(p); setPageSize(ps); },
            }}
            scroll={{ x: 900 }}
            size="middle"
          />
        )}
      </Card>

      <Drawer
        title={editingComputer ? 'Edit Computer' : 'Add Computer'}
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
          <Form.Item name="name" label="Hostname" rules={[{ required: true }]}>
            <Input placeholder="e.g. PC-WORK-001" />
          </Form.Item>
          <Form.Item name="distinguished_name" label="Distinguished Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. CN=PC01,OU=Workstations,DC=example,DC=com" disabled={!!editingComputer} />
          </Form.Item>
          <Form.Item name="ip_address" label="IP Address">
            <Input placeholder="e.g. 192.168.1.100" />
          </Form.Item>
          <Form.Item name="operating_system" label="Operating System">
            <Input placeholder="e.g. Windows 11 Pro" />
          </Form.Item>
          <Form.Item name="os_version" label="OS Version">
            <Input placeholder="e.g. 10.0.22621" />
          </Form.Item>
          <Form.Item name="status" label="Status">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Drawer>
    </>
  );
}
