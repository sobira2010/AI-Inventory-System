import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { Package, ShoppingCart, Brain, ArrowRight } from 'lucide-react'

function Home() {
  const { user } = useAuth()

  const features = [
    {
      icon: Package,
      title: 'Product Management',
      description: 'Add, edit, and organize your inventory with categories, pricing, and stock levels.',
    },
    {
      icon: ShoppingCart,
      title: 'Sales Tracking',
      description: 'Record sales in seconds and watch stock update automatically.',
    },
    {
      icon: Brain,
      title: 'AI Predictions',
      description: 'Forecast demand and get restock suggestions before you run out.',
    },
  ]

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gray-900 text-white">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <h1 className="text-lg font-bold text-primary-400">AI Inventory</h1>
          <nav className="flex items-center gap-3">
            {user ? (
              <Link to="/dashboard" className="btn-primary">
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" className="text-sm text-gray-300 hover:text-white">
                  Sign In
                </Link>
                <Link to="/register" className="btn-primary">
                  Get Started
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Hero */}
      <main className="max-w-6xl mx-auto px-6 py-20">
        <section className="text-center max-w-2xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-900 sm:text-5xl">
            Manage your inventory, smarter
          </h2>
          <p className="mt-4 text-lg text-gray-500">
            Track products, record sales, and let AI predict what to restock next — all in one place.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            {user ? (
              <Link to="/dashboard" className="btn-primary inline-flex items-center gap-2">
                Go to Dashboard <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link to="/register" className="btn-primary inline-flex items-center gap-2">
                  Get Started Free <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/login" className="btn-secondary">
                  Sign In
                </Link>
              </>
            )}
          </div>
        </section>

        {/* Features */}
        <section className="mt-20 grid gap-6 sm:grid-cols-3">
          {features.map((feature) => (
            <div key={feature.title} className="card">
              <feature.icon className="h-8 w-8 text-primary-600" />
              <h3 className="mt-4 font-semibold text-gray-900">{feature.title}</h3>
              <p className="mt-2 text-sm text-gray-500">{feature.description}</p>
            </div>
          ))}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-6 text-center text-sm text-gray-400">
          © {new Date().getFullYear()} AI Inventory Management System
        </div>
      </footer>
    </div>
  )
}

export default Home
