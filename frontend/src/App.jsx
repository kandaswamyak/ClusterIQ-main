import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Recommendations from './components/Recommendations'
import JobsView from './components/JobsView'
import ClustersView from './components/ClustersView'
import Approvals from './components/Approvals'
import CostAnalysis from './components/CostAnalysis'
import SelfHealing from './components/SelfHealing'
import { Activity, TrendingDown, Database, Settings, Menu, X, CheckCircle, DollarSign, Shield } from 'lucide-react'

function NavLink({ to, icon: Icon, children }) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link
      to={to}
      className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-md transition-all duration-300 ${
        isActive
          ? 'text-white'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
      }`}
      style={isActive ? {
        background: 'linear-gradient(to right, #9333ea, #a855f7)',
        boxShadow: '0 0 20px rgba(147, 51, 234, 0.3)'
      } : {}}
    >
      <Icon className="h-4 w-4 mr-2" />
      {children}
    </Link>
  )
}

function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <Router>
      <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)' }}>
        {/* DXC Modern Navigation */}
        <nav className="border-b border-gray-200 shadow-lg" style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(10px)', position: 'sticky', top: 0, zIndex: 50 }}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-18">
              <div className="flex items-center">
                <div className="flex-shrink-0 flex items-center py-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg" style={{ background: 'linear-gradient(135deg, #9333ea, #c026d3)', boxShadow: '0 0 25px rgba(147, 51, 234, 0.5)' }}>
                      <TrendingDown className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <span className="text-2xl font-extrabold" style={{ background: 'linear-gradient(to right, #9333ea, #c026d3)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>ClusterIQ</span>
                      <p className="text-xs text-gray-600 font-medium">AI-Powered Databricks Optimization</p>
                    </div>
                  </div>
                </div>
                <div className="hidden md:ml-12 md:flex md:space-x-2">
                  <NavLink to="/" icon={Activity}>Dashboard</NavLink>
                  <NavLink to="/recommendations" icon={TrendingDown}>Recommendations</NavLink>
                                    <NavLink to="/self-healing" icon={Shield}>Self-Healing</NavLink>
                  <NavLink to="/jobs" icon={Database}>Jobs</NavLink>
                  <NavLink to="/clusters" icon={Settings}>Clusters</NavLink>
                  <NavLink to="/cost" icon={DollarSign}>Cost</NavLink>
                  <NavLink to="/approvals" icon={CheckCircle}>Approvals</NavLink>
                </div>
              </div>
              <div className="flex items-center md:hidden">
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-all"
                >
                  {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                </button>
              </div>
            </div>
          </div>

          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-gray-200" style={{ backgroundColor: '#ffffff' }}>
              <div className="px-2 pt-2 pb-3 space-y-1">
                                <NavLink to="/self-healing" icon={Shield}>Self-Healing</NavLink>
                <NavLink to="/" icon={Activity}>Dashboard</NavLink>
                <NavLink to="/recommendations" icon={TrendingDown}>Recommendations</NavLink>
                <NavLink to="/jobs" icon={Database}>Jobs</NavLink>
                <NavLink to="/clusters" icon={Settings}>Clusters</NavLink>
                <NavLink to="/cost" icon={DollarSign}>Cost Analysis</NavLink>
                <NavLink to="/approvals" icon={CheckCircle}>Approvals</NavLink>
              </div>
            </div>
          )}
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/recommendations" element={<Recommendations />} />
                        <Route path="/self-healing" element={<SelfHealing />} />
            <Route path="/jobs" element={<JobsView />} />
            <Route path="/clusters" element={<ClustersView />} />
            <Route path="/cost" element={<CostAnalysis />} />
            <Route path="/approvals" element={<Approvals />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-700 mt-16" style={{ backgroundColor: '#1a1a1a' }}>
          <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
            <div className="text-center text-sm text-gray-400">
              <p>ClusterIQ - AI-driven Databricks optimization engine</p>
              <p className="mt-2">Turning metrics into decisions, and decisions into measurable cost savings.</p>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App

