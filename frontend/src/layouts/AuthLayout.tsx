import { Outlet } from 'react-router-dom';
import { Flex } from 'antd';

export default function AuthLayout() {
  return (
    <Flex
      justify="center"
      align="center"
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: 24,
      }}
    >
      <Outlet />
    </Flex>
  );
}
