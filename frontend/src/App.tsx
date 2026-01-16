/**
 * Haupt-Applikation - ML Prediction Service
 * Moderne UI mit Gradient-Design und Drawer-Navigation
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  CssBaseline,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  IconButton,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  Add as TrainingIcon,
  Notifications as AlertsIcon,
  Menu as MenuIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// Provider
import { queryClient } from './services/queryClient';

// Components
import ErrorBoundary from './components/common/ErrorBoundary';
import LoadingSpinner from './components/common/LoadingSpinner';

// Pages (werden später implementiert)
const Overview = React.lazy(() => import('./pages/Overview'));
const ModelDetails = React.lazy(() => import('./pages/ModelDetails'));
const AlertConfig = React.lazy(() => import('./pages/AlertConfig'));
const AlertSystem = React.lazy(() => import('./pages/AlertSystem'));
const ModelImport = React.lazy(() => import('./pages/ModelImport'));
const AvailableModelDetails = React.lazy(() => import('./pages/AvailableModelDetails'));
const ModelLogs = React.lazy(() => import('./pages/ModelLogs'));
const CoinDetails = React.lazy(() => import('./pages/CoinDetails'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Info = React.lazy(() => import('./pages/Info'));

// Theme - Modernes Dark Design mit Gradient
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d4ff',
    },
    secondary: {
      main: '#ff4081',
    },
    background: {
      default: '#0f0f23',
      paper: 'rgba(255, 255, 255, 0.05)',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backdropFilter: 'blur(10px)',
        },
      },
    },
  },
});

// Navigation Items für ML Prediction Service
const navItems = [
  { path: '/overview', label: 'Übersicht', icon: <DashboardIcon /> },
  { path: '/model-import', label: 'Modell Import', icon: <TrainingIcon /> },
  { path: '/alert-system', label: 'Alert System', icon: <AlertsIcon /> },
  { path: '/settings', label: 'Einstellungen', icon: <SettingsIcon /> },
  { path: '/info', label: 'Info', icon: <InfoIcon /> },
];


// Layout Component
const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isMobile = useMediaQuery('(max-width:960px)');
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const drawerContent = (
    <Box sx={{ width: 250, pt: 2 }}>
      <Typography variant="h6" sx={{ px: 2, pb: 1, fontWeight: 'bold', color: '#00d4ff' }}>
        🤖 ML Prediction Service
      </Typography>
      <List>
        {navItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              onClick={() => isMobile && setDrawerOpen(false)}
              sx={{
                borderRadius: 2,
                mx: 1,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(0, 212, 255, 0.2)',
                  color: '#00d4ff',
                  border: '1px solid rgba(0, 212, 255, 0.3)',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 212, 255, 0.3)',
                  },
                  '& .MuiListItemIcon-root': {
                    color: '#00d4ff',
                  },
                },
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f0f23 100%)',
      color: 'white',
      overflow: 'auto'
    }}>
      {/* Mobile Drawer */}
      {isMobile ? (
        <Drawer
          variant="temporary"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: 250,
              background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
              borderRight: '1px solid rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        /* Desktop Drawer */
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: 250,
              background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
              borderRight: '1px solid rgba(255, 255, 255, 0.1)',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          width: { xs: '100%', md: 'calc(100% - 250px)' },
          ml: { xs: 0, md: '250px' },
        }}
      >
        {/* Top Bar */}
        <AppBar
          position="static"
          sx={{
            background: 'rgba(26, 26, 46, 0.8)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: 'none',
          }}
        >
          <Toolbar>
            {isMobile && (
              <IconButton
                color="inherit"
                edge="start"
                onClick={() => setDrawerOpen(true)}
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
            )}
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: '#00d4ff' }}>
              🤖 ML Prediction Service Management
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              v1.0.0
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Page Content */}
        <Box sx={{ py: { xs: 2, sm: 3, md: 4 } }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

// Main App Component
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <Router>
            <Layout>
              <React.Suspense fallback={<LoadingSpinner message="Seite wird geladen..." />}>
                <Routes>
                  {/* Redirect root to overview */}
                  <Route path="/" element={<Overview />} />

                  {/* Main routes */}
                  <Route path="/overview" element={<Overview />} />
                  <Route path="/model/:id" element={<ModelDetails />} />
                  <Route path="/model/:id/alert-config" element={<AlertConfig />} />
                  <Route path="/model/:modelId/logs" element={<ModelLogs />} />
                  <Route path="/model/:modelId/coin/:coinId" element={<CoinDetails />} />
                  <Route path="/alert-system" element={<AlertSystem />} />
                  <Route path="/model-import" element={<ModelImport />} />
                  <Route path="/model-import/:modelId" element={<AvailableModelDetails />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/info" element={<Info />} />

                  {/* Fallback für ungültige Routen */}
                  <Route path="*" element={<Overview />} />
                </Routes>
              </React.Suspense>
            </Layout>
          </Router>
        </QueryClientProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;