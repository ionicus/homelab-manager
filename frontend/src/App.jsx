import { BrowserRouter as Router, Routes, Route, Link, NavLink } from 'react-router-dom'
import { MantineProvider, createTheme, Button, Group } from '@mantine/core'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import { themes } from './theme'
import { components } from './theme/components'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import DeviceList from './pages/DeviceList'
import DeviceDetail from './pages/DeviceDetail'
import DeviceForm from './pages/DeviceForm'
import Services from './pages/Services'
import ServiceDetail from './pages/ServiceDetail'
import Automation from './pages/Automation'
import JobDetail from './pages/JobDetail'
import Settings from './pages/Settings'
import Login from './pages/Login'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

function AppContent() {
  const { currentTheme } = useTheme();
  const { user, logout } = useAuth();

  const theme = createTheme({
    ...themes[currentTheme],
    components,
  });

  return (
    <MantineProvider theme={theme}>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-brand">Homelab Manager</Link>
            {user && (
              <>
                <ul className="nav-menu">
                  <li><NavLink to="/" end>Dashboard</NavLink></li>
                  <li><NavLink to="/devices">Devices</NavLink></li>
                  <li><NavLink to="/services">Services</NavLink></li>
                  <li><NavLink to="/automation">Automation</NavLink></li>
                  <li><NavLink to="/settings">Settings</NavLink></li>
                </ul>
                <Group className="nav-user">
                  <span className="nav-username">{user.display_name || user.username}</span>
                  <Button size="xs" variant="subtle" onClick={logout}>Logout</Button>
                </Group>
              </>
            )}
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/devices" element={<ProtectedRoute><DeviceList /></ProtectedRoute>} />
            <Route path="/devices/new" element={<ProtectedRoute><DeviceForm /></ProtectedRoute>} />
            <Route path="/devices/:id/edit" element={<ProtectedRoute><DeviceForm /></ProtectedRoute>} />
            <Route path="/devices/:id" element={<ProtectedRoute><DeviceDetail /></ProtectedRoute>} />
            <Route path="/services" element={<ProtectedRoute><Services /></ProtectedRoute>} />
            <Route path="/services/:id" element={<ProtectedRoute><ServiceDetail /></ProtectedRoute>} />
            <Route path="/automation" element={<ProtectedRoute><Automation /></ProtectedRoute>} />
            <Route path="/automation/jobs/:id" element={<ProtectedRoute><JobDetail /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
    </MantineProvider>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <ThemeProvider>
            <AppContent />
          </ThemeProvider>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App
