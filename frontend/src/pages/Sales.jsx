import { useState, useEffect } from 'react'
import api from '../services/api.js'
import toast from 'react-hot-toast'
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react'

function Sales() {
  const [sales, setSales] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [products, setProducts] = useState([])
  const [createForm, setCreateForm] = useState({
    product_id: '',
    quantity: '',
  })
  const [creating, setCreating] = useState(false)

  const fetchSales = async () => {
    setLoading(true)
    try {
      const response = await api.get('/sales', { params: { page, page_size: 10 } })
      setSales(response.data.sales)
      setTotalPages(response.data.total_pages)
    } catch (error) {
      toast.error('Failed to fetch sales')
    } finally {
      setLoading(false)
    }
  }

  const fetchProducts = async () => {
    try {
      const response = await api.get('/products', { params: { page_size: 100 } })
      setProducts(response.data.products.filter(p => p.quantity > 0))
    } catch (error) {
      console.error('Failed to fetch products')
    }
  }

  useEffect(() => {
    fetchSales()
  }, [page])

  useEffect(() => {
    fetchProducts()
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await api.post('/sales', {
        product_id: parseInt(createForm.product_id),
        quantity: parseInt(createForm.quantity),
      })
      toast.success('Sale created successfully!')
      setShowCreate(false)
      setCreateForm({ product_id: '', quantity: '' })
      fetchSales()
      fetchProducts()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create sale')
    } finally {
      setCreating(false)
    }
  }

  const getSelectedProduct = () => {
    return products.find(p => p.id === parseInt(createForm.product_id))
  }

  const calculateTotal = () => {
    const product = getSelectedProduct()
    if (product && createForm.quantity) {
      return (product.price * parseInt(createForm.quantity)).toFixed(2)
    }
    return '0.00'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sales</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          New Sale
        </button>
      </div>

      {/* Sales Table */}
      <div className="card">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">Loading sales...</p>
          </div>
        ) : sales.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No sales found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">ID</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Product</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Quantity</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Unit Price</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Total</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Sold By</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Date</th>
                </tr>
              </thead>
              <tbody>
                {sales.map((sale) => (
                  <tr key={sale.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm">#{sale.id}</td>
                    <td className="py-3 px-4 text-sm font-medium">{sale.product_name}</td>
                    <td className="py-3 px-4 text-sm">{sale.quantity}</td>
                    <td className="py-3 px-4 text-sm">${sale.unit_price.toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm font-medium text-green-600">${sale.total_price.toFixed(2)}</td>
                    <td className="py-3 px-4 text-sm">{sale.seller_name}</td>
                    <td className="py-3 px-4 text-sm">
                      {sale.sale_date ? new Date(sale.sale_date).toLocaleString() : '-'}
                    </td>
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

      {/* Create Sale Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">New Sale</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product *</label>
                <select
                  value={createForm.product_id}
                  onChange={(e) => setCreateForm({ ...createForm, product_id: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="">Select a product</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} (In stock: {p.quantity}, ${p.price.toFixed(2)})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
                <input
                  type="number"
                  value={createForm.quantity}
                  onChange={(e) => setCreateForm({ ...createForm, quantity: e.target.value })}
                  className="input-field"
                  min="1"
                  max={getSelectedProduct()?.quantity || undefined}
                  required
                />
              </div>

              {/* Total preview */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Unit Price:</span>
                  <span>${getSelectedProduct()?.price?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-600">Quantity:</span>
                  <span>{createForm.quantity || 0}</span>
                </div>
                <div className="flex justify-between text-sm font-semibold mt-2 pt-2 border-t border-gray-200">
                  <span>Total:</span>
                  <span className="text-green-600">${calculateTotal()}</span>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="btn-primary"
                >
                  {creating ? 'Creating...' : 'Create Sale'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Sales
