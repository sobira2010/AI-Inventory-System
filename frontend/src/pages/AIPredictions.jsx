import { useState, useEffect } from 'react'
import api from '../services/api.js'
import toast from 'react-hot-toast'
import { Brain, AlertTriangle, TrendingUp, ShoppingCart } from 'lucide-react'

function AIPredictions() {
  const [activeTab, setActiveTab] = useState('demand')
  const [demandData, setDemandData] = useState(null)
  const [lowStockData, setLowStockData] = useState(null)
  const [reorderData, setReorderData] = useState(null)
  const [loading, setLoading] = useState(false)

  const tabs = [
    { id: 'demand', label: 'Demand Prediction', icon: TrendingUp },
    { id: 'low_stock', label: 'Low Stock Prediction', icon: AlertTriangle },
    { id: 'reorder', label: 'Reorder Recommendations', icon: ShoppingCart },
  ]

  const fetchData = async (tab) => {
    setLoading(true)
    try {
      if (tab === 'demand' && !demandData) {
        const response = await api.get('/ai/demand-prediction')
        setDemandData(response.data)
      } else if (tab === 'low_stock' && !lowStockData) {
        const response = await api.get('/ai/low-stock-prediction')
        setLowStockData(response.data)
      } else if (tab === 'reorder' && !reorderData) {
        const response = await api.get('/ai/reorder-recommendations')
        setReorderData(response.data)
      }
    } catch (error) {
      toast.error('Failed to fetch predictions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(activeTab)
  }, [activeTab])

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'HIGH': return 'bg-red-100 text-red-800'
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-green-100 text-green-800'
    }
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Brain className="h-6 w-6 text-primary-600" />
        <h1 className="text-2xl font-bold text-gray-900">AI Predictions</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-500 mt-4">Analyzing data...</p>
        </div>
      ) : (
        <div className="card">
          {/* Demand Prediction */}
          {activeTab === 'demand' && demandData && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Demand Prediction (Next 7 Days)</h2>
              {demandData.predictions.length === 0 ? (
                <p className="text-gray-500">No products to analyze.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Product</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Current Stock</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Predicted Demand</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Risk Level</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      {demandData.predictions.map((pred) => (
                        <tr key={pred.product_id} className="border-b border-gray-100">
                          <td className="py-3 px-4 text-sm font-medium">{pred.product_name}</td>
                          <td className="py-3 px-4 text-sm">{pred.current_stock}</td>
                          <td className="py-3 px-4 text-sm">{pred.predicted_demand}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(pred.risk_level)}`}>
                              {pred.risk_level}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-500">{pred.message || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Low Stock Prediction */}
          {activeTab === 'low_stock' && lowStockData && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Low Stock Prediction</h2>
              {lowStockData.predictions.length === 0 ? (
                <p className="text-gray-500">No products to analyze.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Product</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Current Stock</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Min Stock</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Days Until Low</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Risk Level</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lowStockData.predictions.map((pred) => (
                        <tr key={pred.product_id} className="border-b border-gray-100">
                          <td className="py-3 px-4 text-sm font-medium">{pred.product_name}</td>
                          <td className="py-3 px-4 text-sm">{pred.current_stock}</td>
                          <td className="py-3 px-4 text-sm">{pred.minimum_stock}</td>
                          <td className="py-3 px-4 text-sm">
                            {pred.days_until_low_stock !== null ? `${pred.days_until_low_stock} days` : '-'}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(pred.risk_level)}`}>
                              {pred.risk_level}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-500">{pred.message || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Reorder Recommendations */}
          {activeTab === 'reorder' && reorderData && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Reorder Recommendations</h2>
              {reorderData.recommendations.length === 0 ? (
                <p className="text-gray-500">No products to analyze.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Product</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Current Stock</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Predicted Demand (30d)</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Recommended Reorder</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Risk Level</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reorderData.recommendations.map((rec) => (
                        <tr key={rec.product_id} className="border-b border-gray-100">
                          <td className="py-3 px-4 text-sm font-medium">{rec.product_name}</td>
                          <td className="py-3 px-4 text-sm">{rec.current_stock}</td>
                          <td className="py-3 px-4 text-sm">{rec.predicted_demand}</td>
                          <td className="py-3 px-4 text-sm font-medium text-primary-600">{rec.recommended_reorder}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(rec.risk_level)}`}>
                              {rec.risk_level}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-500">{rec.message || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AIPredictions
