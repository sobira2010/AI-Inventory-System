import { useState, useEffect } from 'react'
import api from '../services/api.js'
import toast from 'react-hot-toast'
import {
  Package,
  ShoppingCart,
  DollarSign,
  AlertTriangle,
  BarChart3,
  TrendingUp,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get('/dashboard')
        setData(response.data)
      } catch (error) {
        toast.error('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="text-gray-500 ml-4">Loading dashboard...</p>
      </div>
    )
  }

  if (!data) return null

  const statCards = [
    { label: 'Total Products', value: data.total_products, icon: Package, color: 'bg-blue-500' },
    { label: 'Total Stock', value: data.total_stock, icon: BarChart3, color: 'bg-green-500' },
    { label: 'Total Sales', value: data.total_sales, icon: ShoppingCart, color: 'bg-purple-500' },
    { label: 'Total Revenue', value: `$${data.total_revenue.toFixed(2)}`, icon: DollarSign, color: 'bg-yellow-500' },
    { label: 'Low Stock', value: data.low_stock_count, icon: AlertTriangle, color: 'bg-orange-500' },
    { label: 'Out of Stock', value: data.out_of_stock_count, icon: AlertTriangle, color: 'bg-red-500' },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        {statCards.map((card, index) => (
          <div key={index} className="card">
            <div className="flex items-center gap-3">
              <div className={`${card.color} p-2 rounded-lg`}>          <card.icon className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-xl font-bold">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Sales Over Time */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Sales Over Time</h3>
          {data.sales_over_time.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.sales_over_time}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} name="Revenue" />
                <Line type="monotone" dataKey="sales_count" stroke="#10b981" strokeWidth={2} name="Sales" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-400">
              No sales data available
            </div>
          )}
        </div>

        {/* Top Selling Products */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Top Selling Products</h3>
          {data.top_selling_products.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.top_selling_products} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" fontSize={12} />
                <YAxis dataKey="name" type="category" width={100} fontSize={12} />
                <Tooltip />
                <Bar dataKey="total_sold" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-400">
              No sales data available
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stock by Category */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Stock by Category</h3>
          {data.stock_by_category.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.stock_by_category}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="total_stock"
                  nameKey="category"
                  label={({ category, percent }) => `${category} (${(percent * 100).toFixed(0)}%)`}
                >
                  {data.stock_by_category.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-400">
              No products available
            </div>
          )}
        </div>

        {/* Low Stock Products */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Low Stock Products</h3>
          {data.low_stock_products.length > 0 ? (
            <div className="space-y-3">
              {data.low_stock_products.map((product) => (
                <div key={product.id} className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{product.name}</p>
                    <p className="text-xs text-gray-500">Min: {product.minimum_stock}</p>
                  </div>
                  <span className="px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-sm font-medium">
                    {product.quantity} left
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-400">
              No low stock products
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
