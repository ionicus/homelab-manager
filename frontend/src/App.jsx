import { BrowserRouter as Router, Routes, Route, Link, NavLink } from 'react-router-dom'
import { MantineProvider, createTheme } from '@mantine/core'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import { themes } from './theme'
import { components } from './theme/components'
import Dashboard from './pages/Dashboard'
import DeviceList from './pages/DeviceList'
import DeviceDetail from './pages/DeviceDetail'
import DeviceForm from './pages/DeviceForm'
import Services from './pages/Services'
import ServiceDetail from './pages/ServiceDetail'
import Automation from './pages/Automation'
import JobDetail from './pages/JobDetail'
import Settings from './pages/Settings'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

function AppContent() {
  const { currentTheme } = useTheme();

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
            <ul className="nav-menu">
              <li><NavLink to="/" end>Dashboard</NavLink></li>
              <li><NavLink to="/devices">Devices</NavLink></li>
              <li><NavLink to="/services">Services</NavLink></li>
              <li><NavLink to="/automation">Automation</NavLink></li>
              <li><NavLink to="/settings">Settings</NavLink></li>
            </ul>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/devices" element={<DeviceList />} />
            <Route path="/devices/new" element={<DeviceForm />} />
            <Route path="/devices/:id/edit" element={<DeviceForm />} />
            <Route path="/devices/:id" element={<DeviceDetail />} />
            <Route path="/services" element={<Services />} />
            <Route path="/services/:id" element={<ServiceDetail />} />
            <Route path="/automation" element={<Automation />} />
            <Route path="/automation/jobs/:id" element={<JobDetail />} />
            <Route path="/settings" element={<Settings />} />
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
        <ThemeProvider>
          <AppContent />
        </ThemeProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App
