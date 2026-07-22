import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { ProLayout, PageContainer } from '@ant-design/pro-layout';
import {
  DashboardOutlined,
  DesktopOutlined,
  UserOutlined,
  TeamOutlined,
  SyncOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { Dropdown, theme } from 'antd';
import { useAuth } from '../hooks/useAuth';

const menuData = [
  { path: '/', name: 'Dashboard', icon: <DashboardOutlined /> },
  { path: '/computers', name: 'Computers', icon: <DesktopOutlined /> },
  { path: '/users', name: 'Users', icon: <UserOutlined /> },
  { path: '/groups', name: 'Hostnames', icon: <TeamOutlined /> },
  { path: '/sync', name: 'Sync & Import', icon: <SyncOutlined /> },
  { path: '/settings', name: 'Settings', icon: <SettingOutlined /> },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();
  const { token } = theme.useToken();

  const getCurrentRoute = () => {
    const pathname = location.pathname;
    if (pathname === '/') return '/';
    for (const item of menuData) {
      if (item.path !== '/' && pathname.startsWith(item.path)) {
        return item.path;
      }
    }
    return '/';
  };

  const [pathname, setPathname] = useState(getCurrentRoute());

  useEffect(() => {
    setPathname(getCurrentRoute());
  }, [location.pathname]);

  const dropdownItems = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Logout',
        onClick: () => {
          logout();
          navigate('/login');
        },
      },
    ],
  };

  return (
    <ProLayout
      title="AD Hostname Manager"
      logo=""
      layout="mix"
      route={{ routes: menuData }}
      location={{ pathname }}
      token={{
        header: {
          colorBgHeader: token.colorBgContainer,
          colorHeaderTitle: token.colorText,
        },
        sider: {
          colorMenuBackground: '#001529',
          colorTextMenu: 'rgba(255,255,255,0.65)',
          colorTextMenuItemHover: '#fff',
          colorTextMenuSelected: '#fff',
          colorBgMenuItemHover: 'rgba(255,255,255,0.08)',
          colorBgMenuItemSelected: token.colorPrimary,
        },
        pageContainer: {
          paddingBlockPageContainerContent: 24,
          paddingInlinePageContainerContent: 24,
        },
      }}
      menuItemRender={(item, dom) => (
        <a onClick={() => {
          navigate(item.path || '/');
          setPathname(item.path || '/');
        }}>
          {dom}
        </a>
      )}
      avatarProps={{
        icon: <UserOutlined />,
        render: (_, dom) => (
          <Dropdown menu={dropdownItems} trigger={['click']}>
            {dom}
          </Dropdown>
        ),
      }}
      menuFooterRender={(props) => {
        if (props?.collapsed) return undefined;
        return (
          <div style={{ textAlign: 'center', padding: '12px 0', color: 'rgba(255,255,255,0.45)', fontSize: 12 }}>
            AD Manager v1.0
          </div>
        );
      }}
    >
      <PageContainer
        header={{ breadcrumb: {} }}
        style={{ minHeight: '100%' }}
      >
        <Outlet />
      </PageContainer>
    </ProLayout>
  );
}
