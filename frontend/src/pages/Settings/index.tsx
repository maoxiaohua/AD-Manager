import { useEffect, useState } from 'react';
import {
  Card, Tabs, Form, Input, Switch, Button, Space, message, Select,
  Typography, Skeleton, Divider, Tag, Alert,
} from 'antd';
import {
  SettingOutlined, KeyOutlined, ScheduleOutlined, CloudServerOutlined,
  SaveOutlined, ApiOutlined, ReloadOutlined, SearchOutlined,
} from '@ant-design/icons';
import { getSettings, updateSettings, discoverAD, testLDAPConnection, discoverLocations } from '../../services/settings';
import type { LocationInfo } from '../../services/settings';
import { changePassword } from '../../services/auth';
import { SYNC_SCHEDULE_PRESETS } from '../../utils/constants';

const { Title } = Typography;

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [discoveringLoc, setDiscoveringLoc] = useState(false);
  const [locations, setLocations] = useState<LocationInfo[]>([]);
  const [domainInput, setDomainInput] = useState('');
  const [ldapForm] = Form.useForm();
  const [scheduleForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const settings = await getSettings();
      ldapForm.setFieldsValue({
        ldap_server_url: settings.ldap_server_url || '',
        ldap_domain: settings.ldap_domain || '',
        ldap_admin_username: settings.ldap_admin_username || '',
        ldap_admin_password: '',
        ldap_base_dn: settings.ldap_base_dn || '',
        ldap_use_ssl: settings.ldap_use_ssl !== 'false',
        sync_location: settings.sync_location || '',
      });
      scheduleForm.setFieldsValue({
        sync_schedule: settings.sync_schedule || '0 2 * * *',
        scheduler_timezone: settings.scheduler_timezone || 'Asia/Shanghai',
      });
    } catch {
      message.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const saveLDAP = async () => {
    const values = await ldapForm.validateFields();
    setSaving(true);
    try {
      const payload: Record<string, string> = {
        ldap_server_url: values.ldap_server_url || '',
        ldap_domain: values.ldap_domain || '',
        ldap_admin_username: values.ldap_admin_username || '',
        ldap_base_dn: values.ldap_base_dn || '',
        ldap_use_ssl: values.ldap_use_ssl ? 'true' : 'false',
        sync_location: values.sync_location || '',
      };
      if (values.ldap_admin_password) {
        payload.ldap_admin_password = values.ldap_admin_password;
      }
      await updateSettings(payload);
      message.success('LDAP settings saved');
      ldapForm.setFieldValue('ldap_admin_password', '');
    } catch {
      message.error('Failed to save LDAP settings');
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      // Validate form first, then warn user to save if form is dirty
      await ldapForm.validateFields();
      if (ldapForm.isFieldsTouched()) {
        message.warning('Please save LDAP config before testing the connection');
        setTesting(false);
        return;
      }
      const result = await testLDAPConnection();
      message.success(result.message);
    } catch (err: any) {
      // Distinguish form validation errors from connection errors
      if (err?.errorFields) {
        // Ant Design validation error — form already shows inline messages
        return;
      }
      message.error(err?.response?.data?.detail || 'Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  const handleDiscover = async () => {
    if (!domainInput.trim()) {
      message.warning('Please enter a domain name');
      return;
    }
    setDiscovering(true);
    try {
      const result = await discoverAD(domainInput.trim());
      ldapForm.setFieldsValue({
        ldap_server_url: result.server_url,
        ldap_domain: result.domain,
        ldap_base_dn: result.base_dn,
      });
      message.success(`Discovered: ${result.server_url} | Base DN: ${result.base_dn}`);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Discovery failed. Please enter settings manually.');
    } finally {
      setDiscovering(false);
    }
  };

  const handleDiscoverLocations = async () => {
    setDiscoveringLoc(true);
    try {
      const result = await discoverLocations();
      setLocations(result.locations);
      message.success(`Found ${result.locations.length} locations`);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Location discovery failed. Check LDAP settings first.');
    } finally {
      setDiscoveringLoc(false);
    }
  };

  const saveSchedule = async () => {
    const values = await scheduleForm.validateFields();
    setSaving(true);
    try {
      await updateSettings({
        sync_schedule: values.sync_schedule,
        scheduler_timezone: values.scheduler_timezone || 'Asia/Shanghai',
      });
      message.success('Schedule saved — timezone change requires backend restart');
    } catch {
      message.error('Failed to save schedule');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (values: { current_password: string; new_password: string; confirm_password: string }) => {
    if (values.new_password !== values.confirm_password) {
      message.error('New passwords do not match');
      return;
    }
    try {
      await changePassword(values.current_password, values.new_password);
      message.success('Password changed successfully');
      passwordForm.resetFields();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Failed to change password');
    }
  };

  const tabItems = [
    {
      key: 'ldap',
      label: <span><CloudServerOutlined /> LDAP Config</span>,
      children: loading ? <Skeleton active paragraph={{ rows: 6 }} /> : (
        <Form form={ldapForm} layout="vertical" style={{ maxWidth: 600 }}>
          <Alert
            message="LDAP Configuration"
            description="Configure Active Directory connection settings. The system will use these credentials to pull data from your domain controller."
            type="info"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
          />
          <Alert
            message="Smart Setup — Auto Discover"
            description="Just enter your AD domain name (e.g. your-domain.com) and we'll find the domain controller and Base DN automatically."
            type="success"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
          />
          <Space style={{ marginBottom: 24 }}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="e.g. your-domain.com"
              value={domainInput}
              onChange={(e) => setDomainInput(e.target.value)}
              onPressEnter={handleDiscover}
              style={{ width: 280 }}
            />
            <Button
              type="primary"
              icon={<ApiOutlined />}
              onClick={handleDiscover}
              loading={discovering}
            >
              Auto Discover
            </Button>
          </Space>
          <Form.Item name="ldap_server_url" label="Server URL" rules={[{ required: true }]}>
            <Input placeholder="ldaps://dc.example.com:636" />
          </Form.Item>
          <Form.Item name="ldap_domain" label="Domain" rules={[{ required: true }]}>
            <Input placeholder="EXAMPLE" />
          </Form.Item>
          <Form.Item name="ldap_admin_username" label="Admin Username" rules={[{ required: true }]}>
            <Input placeholder="administrator" />
          </Form.Item>
          <Form.Item name="ldap_admin_password" label="Admin Password" extra="Leave empty to keep current password. Note: Password is stored locally — restrict filesystem access to the database file.">
            <Input.Password placeholder="Enter LDAP admin password" />
          </Form.Item>
          <Form.Item name="ldap_base_dn" label="Base DN" rules={[{ required: true }]}>
            <Input placeholder="DC=example,DC=com" />
          </Form.Item>
          <Form.Item name="ldap_use_ssl" label="Use SSL" valuePropName="checked">
            <Switch checkedChildren="SSL" unCheckedChildren="Plain" />
          </Form.Item>
          <Form.Item label="Sync Location" name="sync_location">
            <Select
              placeholder="All locations (no filter)"
              allowClear
              options={locations.map(l => ({
                label: `${l.city} (${l.region})`,
                value: l.base_dn,
              }))}
              notFoundContent={
                locations.length === 0 ? 'Click "Discover" to load locations' : 'No locations found'
              }
            />
          </Form.Item>
          <Button
            icon={<SearchOutlined />}
            onClick={handleDiscoverLocations}
            loading={discoveringLoc}
            style={{ marginBottom: 24 }}
          >
            Discover Locations
          </Button>
          <Divider />
          <Space>
            <Button type="primary" icon={<SaveOutlined />} onClick={saveLDAP} loading={saving}>Save LDAP Config</Button>
            <Button icon={<ApiOutlined />} onClick={testConnection} loading={testing}>Test Connection</Button>
            <Button icon={<ReloadOutlined />} onClick={loadSettings}>Reset</Button>
          </Space>
        </Form>
      ),
    },
    {
      key: 'schedule',
      label: <span><ScheduleOutlined /> Sync Schedule</span>,
      children: loading ? <Skeleton active paragraph={{ rows: 3 }} /> : (
        <Form form={scheduleForm} layout="vertical" style={{ maxWidth: 600 }}>
          <Alert
            message="Sync Schedule"
            description="Configure how often the system automatically syncs with Active Directory. Use a cron expression for custom scheduling."
            type="info"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
          />
          <Form.Item name="sync_schedule" label="Sync Schedule (Cron)" rules={[{ required: true }]}>
            <Input placeholder="0 2 * * *" />
          </Form.Item>
          <Form.Item name="scheduler_timezone" label="Timezone" extra="Requires backend restart to take effect">
            <Select
              showSearch
              placeholder="Select timezone"
              options={[
                { label: 'Asia/Shanghai (UTC+8)', value: 'Asia/Shanghai' },
                { label: 'Asia/Singapore (UTC+8)', value: 'Asia/Singapore' },
                { label: 'Asia/Tokyo (UTC+9)', value: 'Asia/Tokyo' },
                { label: 'Asia/Seoul (UTC+9)', value: 'Asia/Seoul' },
                { label: 'Asia/Kolkata (UTC+5:30)', value: 'Asia/Kolkata' },
                { label: 'Asia/Dubai (UTC+4)', value: 'Asia/Dubai' },
                { label: 'Europe/London (UTC+0)', value: 'Europe/London' },
                { label: 'Europe/Berlin (UTC+1)', value: 'Europe/Berlin' },
                { label: 'America/New_York (UTC-5)', value: 'America/New_York' },
                { label: 'America/Chicago (UTC-6)', value: 'America/Chicago' },
                { label: 'America/Los_Angeles (UTC-8)', value: 'America/Los_Angeles' },
                { label: 'UTC', value: 'UTC' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Presets">
            <Space wrap>
              {SYNC_SCHEDULE_PRESETS.map(preset => (
                <Tag
                  key={preset.value}
                  color="blue"
                  style={{ cursor: 'pointer' }}
                  onClick={() => scheduleForm.setFieldValue('sync_schedule', preset.value)}
                >
                  {preset.label}
                </Tag>
              ))}
            </Space>
          </Form.Item>
          <Divider />
          <Button type="primary" icon={<SaveOutlined />} onClick={saveSchedule} loading={saving}>Save Schedule</Button>
        </Form>
      ),
    },
    {
      key: 'password',
      label: <span><KeyOutlined /> Admin Password</span>,
      children: (
        <Form form={passwordForm} layout="vertical" onFinish={handleChangePassword} style={{ maxWidth: 400 }}>
          <Alert
            message="Change Admin Password"
            description="This password is used to log into the AD Hostname Manager web interface."
            type="warning"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
          />
          <Form.Item name="current_password" label="Current Password" rules={[{ required: true }]}>
            <Input.Password placeholder="Enter current password" />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="New Password"
            rules={[
              { required: true },
              { min: 8, message: 'Password must be at least 8 characters' },
              {
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
                message: 'Must include uppercase, lowercase, and a number',
              },
            ]}
          >
            <Input.Password placeholder="At least 8 chars, mixed case + number" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="Confirm New Password"
            dependencies={['new_password']}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) return Promise.resolve();
                  return Promise.reject(new Error('Passwords do not match'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="Confirm new password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<KeyOutlined />}>Change Password</Button>
        </Form>
      ),
    },
  ];

  return (
    <Card style={{ borderRadius: 8 }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        <SettingOutlined style={{ marginRight: 8 }} />
        System Settings
      </Title>
      <Tabs items={tabItems} tabPosition="left" style={{ minHeight: 400 }} />
    </Card>
  );
}
