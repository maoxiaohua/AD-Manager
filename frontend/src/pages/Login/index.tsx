import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Input, Button, Typography, message, Space } from 'antd';
import { LockOutlined, WindowsOutlined } from '@ant-design/icons';
import { login } from '../../services/auth';
import { useAuth } from '../../hooks/useAuth';

const { Title, Text } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setAuthenticated } = useAuth();

  const onFinish = async (values: { password: string }) => {
    setLoading(true);
    try {
      const token = await login(values.password);
      localStorage.setItem('access_token', token);
      setAuthenticated(true);
      message.success('Login successful');
      navigate('/');
    } catch (err: any) {
      if (err?.response?.status === 401) {
        message.error('Invalid password');
      } else if (err?.code === 'ERR_NETWORK' || !err?.response) {
        message.error('Cannot connect to server. Check your network.');
      } else {
        message.error('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      style={{
        width: 400,
        maxWidth: '90vw',
        borderRadius: 12,
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
      }}
      styles={{ body: { padding: '40px 32px' } }}
    >
      <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
        <div>
          <WindowsOutlined style={{ fontSize: 48, color: '#1677FF' }} />
          <Title level={3} style={{ marginTop: 16, marginBottom: 4 }}>
            AD Hostname Manager
          </Title>
          <Text type="secondary">Windows Domain Hostname Registration System</Text>
        </div>

        <Form onFinish={onFinish} layout="vertical" size="large">
          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please enter admin password' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Admin Password"
              style={{ height: 44 }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 44, fontSize: 16 }}
            >
              Sign In
            </Button>
          </Form.Item>
        </Form>
      </Space>
    </Card>
  );
}
