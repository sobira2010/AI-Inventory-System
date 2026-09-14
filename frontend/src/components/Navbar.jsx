import { useAuth } from '../context/AuthContext.jsx'
import { LogOut, Menu } from 'lucide-react'

function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button className="lg:hidden text-gray-500 hover:text-gray-700">
          <Menu className="h-6 w-6" />
        </button>
        <div>
          <h2 className="text-lg font-semibold text-gray-800">
            Welcome back, {user?.name}
          </h2>
          <p className="text-sm text-gray-500">
            {user?.role === 'ADMIN' ? 'Administrator' : 'Staff Member'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:block text-right">
          <p className="text-sm font-medium text-gray-700">{user?.email}</p>
          <p className="text-xs text-gray-500">
            {user?.role === 'ADMIN' ? 'Admin' : 'Staff'}
          </p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  )
}

export default Navbar
