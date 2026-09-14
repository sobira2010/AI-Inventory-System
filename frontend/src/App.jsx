import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuth } from './context/AuthContext.jsx'
import ProtectedRoute from './routes/ProtectedRoute.jsx'

// Pages
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Products from './pages/Products.jsx'
import AddProduct from './pages/AddProduct.jsx'
import EditProduct from './pages/EditProduct.jsx'
import ProductDetails from './pages/ProductDetails.jsx'
import Sales from './pages/Sales.jsx'
import StockHistory from './pages/StockHistory.jsx'
import AIPredictions from './pages/AIPredictions.jsx'

// Layout
import Sidebar from './components/Sidebar.jsx'
import Navbar from './components/Navbar.jsx'
import AIChatbot from './components/AIChatbot.jsx'

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={!user ? <Login /> : <Navigate to="/dashboard" />} />
        <Route path="/register" element={!user ? <Register /> : <Navigate to="/dashboard" />} />

        {/* Protected routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <div className="flex h-screen">
                <Sidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                  <Navbar />
                  <div className="flex-1 flex overflow-hidden">
                    <main className="flex-1 overflow-y-auto p-6">
                      <Routes>
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/products" element={<Products />} />
                        <Route path="/products/add" element={<AddProduct />} />
                        <Route path="/products/:id" element={<ProductDetails />} />
                        <Route path="/products/:id/edit" element={<EditProduct />} />
                        <Route path="/sales" element={<Sales />} />
                        <Route path="/stock" element={<StockHistory />} />
                        <Route path="/ai" element={<AIPredictions />} />
                        <Route path="*" element={<Navigate to="/dashboard" />} />
                      </Routes>
                    </main>
                    <AIChatbot />
                  </div>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  )
}

export default App
