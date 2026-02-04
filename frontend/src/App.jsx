import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Recommendations from './components/Recommendations'
import JobsView from './components/JobsView'
import ClustersView from './components/ClustersView'
import ComputeView from './components/ComputeView'
import SummaryMetrics from './components/SummaryMetrics'
import Approvals from './components/Approvals'
import LogsView from './components/LogsView'
import CostAnalysis from './components/CostAnalysis'
import { Activity, TrendingDown, Database, Settings, Menu, X, Layers, BarChart3, CheckCircle, FileText, DollarSign } from 'lucide-react'

function NavLink({ to, icon: Icon, children }) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link
      to={to}
      className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${
        isActive
          ? 'bg-primary-50 text-primary-700 border-b-2 border-primary-600'
          : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
      }`}
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
      <div className="min-h-screen bg-gray-50">
        {/* Modern Navigation */}
        <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0 flex items-center">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
                      <TrendingDown className="h-5 w-5 text-white" />
                    </div>
                    <span className="ml-2 text-xl font-bold text-gray-900">ClusterIQ</span>
                  </div>
                </div>
                <div className="hidden md:ml-10 md:flex md:space-x-1">
                  <NavLink to="/" icon={Activity}>Dashboard</NavLink>
                  <NavLink to="/recommendations" icon={TrendingDown}>Recommendations</NavLink>
                  <NavLink to="/compute" icon={Layers}>All Compute</NavLink>
                  <NavLink to="/jobs" icon={Database}>Jobs</NavLink>
                  <NavLink to="/clusters" icon={Settings}>Clusters</NavLink>
                  <NavLink to="/cost" icon={DollarSign}>Cost Analysis</NavLink>
                  <NavLink to="/summary" icon={BarChart3}>Summary</NavLink>
                  <NavLink to="/approvals" icon={CheckCircle}>Approvals</NavLink>
                  <NavLink to="/logs" icon={FileText}>Logs</NavLink>
                </div>
              </div>
              <div className="flex items-center md:hidden">
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-primary-600 hover:bg-gray-100"
                >
                  {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                </button>
              </div>
            </div>
          </div>

          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-gray-200 bg-white">
              <div className="px-2 pt-2 pb-3 space-y-1">
                <NavLink to="/" icon={Activity}>Dashboard</NavLink>
                <NavLink to="/recommendations" icon={TrendingDown}>Recommendations</NavLink>
                <NavLink to="/compute" icon={Layers}>All Compute</NavLink>
                <NavLink to="/jobs" icon={Database}>Jobs</NavLink>
                <NavLink to="/clusters" icon={Settings}>Clusters</NavLink>
                <NavLink to="/cost" icon={DollarSign}>Cost Analysis</NavLink>
                <NavLink to="/summary" icon={BarChart3}>Summary</NavLink>
                <NavLink to="/approvals" icon={CheckCircle}>Approvals</NavLink>
                <NavLink to="/logs" icon={FileText}>Logs</NavLink>
              </div>
            </div>
          )}
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/compute" element={<ComputeView />} />
            <Route path="/jobs" element={<JobsView />} />
            <Route path="/clusters" element={<ClustersView />} />
            <Route path="/cost" element={<CostAnalysis />} />
            <Route path="/summary" element={<SummaryMetrics />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/logs" element={<LogsView />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-16">
          <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
            <div className="text-center text-sm text-gray-600">
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

