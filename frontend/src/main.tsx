import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider, App as AntApp } from 'antd';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { themeConfig } from './styles/theme';
import App from './App';
import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider theme={themeConfig}>
      <AntApp>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>
);
