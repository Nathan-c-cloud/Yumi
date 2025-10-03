import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { ArrowLeft, ShoppingCart, Brain, CheckCircle, Star, Target } from 'lucide-react'
import yumiLogo from '../assets/yumi_logo.png'
import { API_ENDPOINTS } from '../config/api'

function SmartBaskets({ userId }) {
  const [intelligentCart, setIntelligentCart] = useState([])
  const [selectedProducts, setSelectedProducts] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [transferring, setTransferring] = useState(false)

  useEffect(() => {
    generateIntelligentCart()
  }, [])

  const generateIntelligentCart = async () => {
    setLoading(true)
    setMessage('')

    try {
      const response = await fetch('http://localhost:5002/api/cart/intelligent', {
        headers: {
          'X-User-ID': userId
        }
      })

      const data = await response.json()
      if (data.success) {
        setIntelligentCart(data.intelligent_cart || [])
        setMessage(data.message)
        // Sélectionner automatiquement les 6 meilleurs produits
        if (data.intelligent_cart && data.intelligent_cart.length > 0) {
          const topProducts = data.intelligent_cart.slice(0, 6).map(p => p.barcode)
          setSelectedProducts(new Set(topProducts))
        }
      } else {
        setMessage(data.error || 'Erreur lors de la génération du panier intelligent')
      }
    } catch (err) {
      setMessage('Erreur de connexion au serveur')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const toggleProductSelection = (barcode) => {
    const newSelected = new Set(selectedProducts)
    if (newSelected.has(barcode)) {
      newSelected.delete(barcode)
    } else {
      newSelected.add(barcode)
    }
    setSelectedProducts(newSelected)
  }

  const transferToCart = async () => {
    if (selectedProducts.size === 0) {
      setMessage('Veuillez sélectionner au moins un produit')
      return
    }

    setTransferring(true)
    setMessage('')

    try {
      const response = await fetch('http://localhost:5002/api/cart/intelligent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          selected_products: Array.from(selectedProducts)
        })
      })

      const data = await response.json()
      if (data.success) {
        setMessage(`✅ ${data.message}`)
        // Optionnel: rediriger vers le panier après quelques secondes
        setTimeout(() => {
          window.location.href = '/cart'
        }, 2000)
      } else {
        setMessage(data.error || 'Erreur lors du transfert')
      }
    } catch (err) {
      setMessage('Erreur de connexion au serveur')
      console.error('Error:', err)
    } finally {
      setTransferring(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-50 border-green-200'
    if (score >= 60) return 'bg-yellow-50 border-yellow-200'
    return 'bg-red-50 border-red-200'
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-100 via-pink-100 to-blue-100">
        <div className="text-center">
          <Brain className="h-16 w-16 mx-auto mb-4 text-orange-500 animate-pulse" />
          <p className="text-xl font-semibold">Génération de votre panier intelligent...</p>
          <p className="text-gray-600 mt-2">Analyse de votre profil et de vos préférences</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-100 via-pink-100 to-blue-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-md p-4 sticky top-0 z-10">
        <div className="container mx-auto flex justify-between items-center">
          <Link to="/">
            <Button variant="ghost" className="flex items-center gap-2">
              <ArrowLeft className="h-5 w-5" />
              Retour
            </Button>
          </Link>
          <img src={yumiLogo} alt="Yumi" className="h-12" />
          <div className="w-20"></div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-2xl p-8">

          {/* Title */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Brain className="h-12 w-12 text-orange-500" />
              <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500 bg-clip-text text-transparent">
                Panier Intelligent
              </h1>
            </div>
            <p className="text-xl text-gray-700">
              Sélection automatique basée sur votre profil nutritionnel
            </p>
          </div>

          {/* Message */}
          {message && (
            <div className={`mb-6 p-4 rounded-lg ${message.includes('✅') ? 'bg-green-100 text-green-700' : message.includes('Erreur') ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
              {message}
            </div>
          )}

          {intelligentCart.length === 0 ? (
            <div className="text-center py-12">
              <Target className="h-24 w-24 mx-auto text-gray-300 mb-4" />
              <p className="text-xl text-gray-600 mb-4">
                Aucun produit adapté à votre profil trouvé
              </p>
              <p className="text-gray-500 mb-6">
                Scannez plus de produits pour enrichir vos recommandations
              </p>
              <Link to="/scanner">
                <Button className="bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500">
                  Scanner des produits
                </Button>
              </Link>
            </div>
          ) : (
            <>
              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-4 text-center">
                  <h3 className="text-2xl font-bold text-orange-600">{intelligentCart.length}</h3>
                  <p className="text-orange-700">Produits recommandés</p>
                </div>
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 text-center">
                  <h3 className="text-2xl font-bold text-green-600">{selectedProducts.size}</h3>
                  <p className="text-green-700">Sélectionnés</p>
                </div>
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 text-center">
                  <h3 className="text-2xl font-bold text-blue-600">
                    {intelligentCart.length > 0 ? Math.round(intelligentCart.reduce((sum, p) => sum + (p.suitability_score || 0), 0) / intelligentCart.length) : 0}
                  </h3>
                  <p className="text-blue-700">Score moyen d'adéquation</p>
                </div>
              </div>

              {/* Products Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {intelligentCart.map((product, index) => (
                  <div
                    key={product.barcode || index}
                    className={`relative rounded-xl p-6 cursor-pointer transition-all duration-300 border-2 ${
                      selectedProducts.has(product.barcode)
                        ? 'border-orange-400 bg-gradient-to-br from-orange-50 to-pink-50 shadow-lg'
                        : 'border-gray-200 bg-white hover:border-orange-200 hover:shadow-md'
                    }`}
                    onClick={() => toggleProductSelection(product.barcode)}
                  >

                    {/* Selection indicator */}
                    <div className="absolute top-3 right-3">
                      {selectedProducts.has(product.barcode) ? (
                        <CheckCircle className="h-6 w-6 text-orange-500" />
                      ) : (
                        <div className="h-6 w-6 border-2 border-gray-300 rounded-full"></div>
                      )}
                    </div>

                    {/* Product info */}
                    <div className="mb-4">
                      <h3 className="font-bold text-lg mb-2 pr-8">
                        {product.product_name || 'Produit inconnu'}
                      </h3>
                      <p className="text-gray-600 text-sm mb-3">
                        {product.brands || 'Marque inconnue'}
                      </p>
                    </div>

                    {/* Scores */}
                    <div className="space-y-3">
                      <div className={`flex justify-between items-center p-3 rounded-lg border ${getScoreBg(product.yumi_score || 0)}`}>
                        <span className="font-semibold">Score Yumi</span>
                        <span className={`font-bold text-lg ${getScoreColor(product.yumi_score || 0)}`}>
                          {product.yumi_score || 0}/100
                        </span>
                      </div>

                      <div className={`flex justify-between items-center p-3 rounded-lg border ${getScoreBg(product.suitability_score || 0)}`}>
                        <span className="font-semibold flex items-center gap-1">
                          <Target className="h-4 w-4" />
                          Adéquation
                        </span>
                        <span className={`font-bold text-lg ${getScoreColor(product.suitability_score || 0)}`}>
                          {product.suitability_score || 0}/100
                        </span>
                      </div>
                    </div>

                    {/* Selection reason */}
                    {product.selection_reason && (
                      <div className="mt-3 text-xs text-gray-600 bg-gray-50 p-2 rounded">
                        💡 {product.selection_reason}
                      </div>
                    )}

                    {/* Auto-selected badge */}
                    {selectedProducts.has(product.barcode) && (
                      <div className="mt-3 flex items-center gap-1 text-xs text-orange-600">
                        <Star className="h-3 w-3 fill-current" />
                        Recommandé pour vous
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  onClick={generateIntelligentCart}
                  variant="outline"
                  className="px-8 py-3"
                >
                  Régénérer les recommandations
                </Button>

                <Button
                  onClick={transferToCart}
                  disabled={selectedProducts.size === 0 || transferring}
                  className="px-8 py-3 bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500 text-white"
                >
                  <ShoppingCart className="h-5 w-5 mr-2" />
                  {transferring
                    ? 'Ajout en cours...'
                    : `Ajouter au panier (${selectedProducts.size})`
                  }
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default SmartBaskets
