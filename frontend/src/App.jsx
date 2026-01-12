import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import DeviceList from './pages/DeviceList'
import DeviceDetail from './pages/DeviceDetail'
import DeviceForm from './pages/DeviceForm'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-brand">Homelab Manager</Link>
            <ul className="nav-menu">
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/devices">Devices</Link></li>
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
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
