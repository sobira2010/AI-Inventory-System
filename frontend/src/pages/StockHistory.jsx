import { useState, useEffect } from 'react'
import api from '../services/api.js'
import toast from 'react-hot-toast'
import { Plus, Minus, ChevronLeft, ChevronRight } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

function StockHistory() {
  const { user } = useAuth()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [showAdjust, setShowAdjust] = useState(false)
  const [products, setProducts] = useState([])
  const [adjustForm, setAdjustForm] = useState({
    product_id: '',
    quantity_change: '',
    reason: '',
    notes: '',
  })
  const [adjusting, setAdjusting] = useState(false)

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const response = await api.get('/stock/history', { params: { page, page_size: 10 } })
      setHistory(response.data.history)
      setTotalPages(response.data.total_pages)
    } catch (error) {
      toast.error('Failed to fetch stock history')
    } finally {
      setLoading(false)
    }
  }

  const fetchProducts = async () => {
    try {
      const response = await api.get('/products', { params: { page_size: 100 } })
      setProducts(response.data.products)
    } catch (error) {
      console.error('Failed to fetch products')
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [page])

  useEffect(() => {
    fetchProducts()
  }, [])

  const handleAdjust = async (e) => {
    e.preventDefault()
    setAdjusting(true)
    try {
      await api.post('/stock/adjust', {
        ...adjustForm,
        product_id: parseInt(adjustForm.product_id),
        quantity_change: parseInt(adjustForm.quantity_change),
      })
      toast.success('Stock adjusted successfully!')
      setShowAdjust(false)
      setAdjustForm({ product_id: '', quantity_change: '', reason: '', notes: '' })
      fetchHistory()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to adjust stock')
    } finally {
      setAdjusting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Stock History</h1>
        <button
          onClick={() => setShowAdjust(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Adjust Stock
        </button>
      </div>

      {/* Stock History Table */}
      <div className="card">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">Loading history...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No stock history found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Product</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Change</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Previous</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">New</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Reason</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">User</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm">
                      {entry.created_at ? new Date(entry.created_at).toLocaleString() : '-'}
                    </td>
                    <td className="py-3 px-4 text-sm font-medium">{entry.product_name}</td>
                    <td className="py-3 px-4">
                      <span className={`flex items-center gap-1 text-sm font-medium ${entry.quantity_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {entry.quantity_change > 0 ? <Plus className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                        {Math.abs(entry.quantity_change)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm">{entry.previous_quantity}</td>
                    <td className="py-3 px-4 text-sm font-medium">{entry.new_quantity}</td>
                    <td className="py-3 px-4 text-sm">{entry.reason || '-'}</td>
                    <td className="py-3 px-4 text-sm">{entry.user_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary flex items-center gap-1 disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-secondary flex items-center gap-1 disabled:opacity-50"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Adjust Stock Modal */}
      {showAdjust && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Adjust Stock</h3>
            <form onSubmit={handleAdjust} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product *</label>
                <select
                  value={adjustForm.product_id}
                  onChange={(e) => setAdjustForm({ ...adjustForm, product_id: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="">Select a product</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} (Stock: {p.quantity})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quantity Change * <span className="text-gray-400">(positive to add, negative to remove)</span>
                </label>
                <input
                  type="number"
                  value={adjustForm.quantity_change}
                  onChange={(e) => setAdjustForm({ ...adjustForm, quantity_change: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason *</label>
                <input
                  type="text"
                  value={adjustForm.reason}
                  onChange={(e) => setAdjustForm({ ...adjustForm, reason: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Restock, Damaged, etc."
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={adjustForm.notes}
                  onChange={(e) => setAdjustForm({ ...adjustForm, notes: e.target.value })}
                  className="input-field"
                  rows={2}
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowAdjust(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={adjusting}
                  className="btn-primary"
                >
                  {adjusting ? 'Adjusting...' : 'Adjust Stock'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default StockHistory
