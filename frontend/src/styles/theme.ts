import type { ThemeConfig } from 'antd';

export const themeConfig: ThemeConfig = {
  token: {
    colorPrimary: '#1677FF',
    borderRadius: 6,
    colorBgContainer: '#FFFFFF',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    colorSuccess: '#52C41A',
    colorWarning: '#FAAD14',
    colorError: '#FF4D4F',
    colorInfo: '#1677FF',
  },
  components: {
    Table: {
      headerBg: '#FAFAFA',
      headerColor: '#262626',
      rowHoverBg: '#E6F4FF',
      borderRadius: 8,
    },
    Card: {
      borderRadiusLG: 8,
    },
    Button: {
      borderRadius: 6,
      controlHeight: 36,
      paddingContentHorizontal: 16,
    },
    Input: {
      controlHeight: 36,
      borderRadius: 6,
    },
    Select: {
      controlHeight: 36,
      borderRadius: 6,
    },
    Tree: {
      borderRadius: 6,
    },
    Modal: {
      borderRadiusLG: 8,
    },
    Drawer: {
      borderRadiusLG: 8,
    },
  },
};
