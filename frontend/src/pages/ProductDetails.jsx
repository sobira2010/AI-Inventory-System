import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../services/api.js'
import toast from 'react-hot-toast'
import { ArrowLeft, Edit } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

function ProductDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await api.get(`/products/${id}`)
        setProduct(response.data)
      } catch (error) {
        toast.error('Failed to load product')
        navigate('/products')
      } finally {
        setLoading(false)
      }
    }
    fetchProduct()
  }, [id, navigate])

  const getStockStatus = () => {
    if (product.quantity === 0) return { text: 'OUT OF STOCK', color: 'bg-red-100 text-red-800' }
    if (product.quantity <= product.minimum_stock) return { text: 'LOW STOCK', color: 'bg-yellow-100 text-yellow-800' }
    return { text: 'IN STOCK', color: 'bg-green-100 text-green-800' }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!product) return null

  const status = getStockStatus()

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/products')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
        </div>
        {isAdmin && (
          <button
            onClick={() => navigate(`/products/${id}/edit`)}
            className="btn-primary flex items-center gap-2"
          >
            <Edit className="h-4 w-4" />
            Edit
          </button>
        )}
      </div>

      <div className="card">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-gray-500">Category</label>
            <p className="font-medium">{product.category}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Status</label>
            <p><span className={`px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>{status.text}</span></p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Price</label>
            <p className="font-medium">${product.price.toFixed(2)}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Quantity</label>
            <p className="font-medium">{product.quantity}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Minimum Stock</label>
            <p className="font-medium">{product.minimum_stock}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Supplier</label>
            <p className="font-medium">{product.supplier || '-'}</p>
          </div>
          {product.description && (
            <div className="col-span-2">
              <label className="text-sm text-gray-500">Description</label>
              <p className="mt-1">{product.description}</p>
            </div>
          )}
          <div>
            <label className="text-sm text-gray-500">Created</label>
            <p className="font-medium">{product.created_at ? new Date(product.created_at).toLocaleDateString() : '-'}</p>
          </div>
          <div>
            <label className="text-sm text-gray-500">Last Updated</label>
            <p className="font-medium">{product.updated_at ? new Date(product.updated_at).toLocaleDateString() : '-'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProductDetails
