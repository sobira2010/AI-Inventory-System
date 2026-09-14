import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  History,
  Brain,
  Plus,
} from 'lucide-react'

function Sidebar() {
  const { user } = useAuth()

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/products', label: 'Products', icon: Package },
    { to: '/products/add', label: 'Add Product', icon: Plus },
    { to: '/sales', label: 'Sales', icon: ShoppingCart },
    { to: '/stock', label: 'Stock', icon: History },
    { to: '/ai', label: 'AI Predictions', icon: Brain },
  ]

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-6">
        <h1 className="text-xl font-bold text-primary-400">AI Inventory</h1>
        <p className="text-xs text-gray-400 mt-1">Management System</p>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200 ${
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-500">
          Logged in as
        </div>
        <div className="text-sm font-medium text-gray-300 truncate">
          {user?.name}
        </div>
        <div className="text-xs text-primary-400 mt-0.5">
          {user?.role}
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
