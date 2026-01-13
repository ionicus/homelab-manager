import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import DeviceList from './pages/DeviceList'
import DeviceDetail from './pages/DeviceDetail'
import DeviceForm from './pages/DeviceForm'
import Services from './pages/Services'
import ServiceDetail from './pages/ServiceDetail'
import Automation from './pages/Automation'
import JobDetail from './pages/JobDetail'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="app">
          <nav className="navbar">
            <div className="nav-container">
              <Link to="/" className="nav-brand">Homelab Manager</Link>
              <ul className="nav-menu">
                <li><Link to="/">Dashboard</Link></li>
                <li><Link to="/devices">Devices</Link></li>
                <li><Link to="/services">Services</Link></li>
                <li><Link to="/automation">Automation</Link></li>
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
            </Routes>
          </main>
        </div>
      </Router>
    </ErrorBoundary>
  )
}

export default App
