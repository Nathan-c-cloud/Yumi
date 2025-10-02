import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { ArrowLeft, ShoppingCart, Trash2, Plus, Minus } from 'lucide-react'
import yumiLogo from '../assets/yumi_logo.png'

function Cart({ userId }) {
  const [cart, setCart] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchCart()
  }, [])

  const fetchCart = async () => {
    try {
      const response = await fetch('http://localhost:5002/api/cart', {
        headers: {
          'X-User-ID': userId
        }
      } )

      const data = await response.json()
      if (data.success) {
        setCart(data.cart)
      }
    } catch (err) {
      setMessage('Erreur de connexion au serveur')
    } finally {
      setLoading(false)
    }
  }

  const removeFromCart = async (barcode) => {
    try {
      const response = await fetch('http://localhost:5002/api/cart/remove', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ barcode } )
      })

      if (response.ok) {
        fetchCart()
      }
    } catch (err) {
      setMessage('Erreur lors de la suppression')
    }
  }

  const updateQuantity = async (barcode, newQuantity) => {
    try {
      const response = await fetch('http://localhost:5002/api/cart/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ barcode, quantity: newQuantity } )
      })

      if (response.ok) {
        fetchCart()
      }
    } catch (err) {
      setMessage('Erreur lors de la mise à jour')
    }
  }

  const handleCheckout = async () => {
    setMessage('')

    try {
      const response = await fetch('http://localhost:5002/api/cart/checkout', {
        method: 'POST',
        headers: {
          'X-User-ID': userId
        }
      } )

      const data = await response.json()

      if (data.success) {
        setMessage('Commande passée avec succès ! (Simulation)')
        setCart([])
      } else {
        setMessage(data.error || 'Erreur lors de la commande')
      }
    } catch (err) {
      setMessage('Erreur de connexion au serveur')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl">Chargement du panier...</p>
      </div>
    )
  }

  const isEmpty = cart.length === 0

  return (
    <div className="min-h-screen p-4">
      <div className="container mx-auto max-w-4xl">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-2xl p-8">
          <div className="flex items-center justify-between mb-6">
            <Link to="/">
              <Button variant="ghost" className="flex items-center gap-2">
                <ArrowLeft className="h-5 w-5" />
                Retour
              </Button>
            </Link>
            <img src={yumiLogo} alt="Yumi" className="h-12" />
          </div>

          <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500 bg-clip-text text-transparent flex items-center gap-3">
            <ShoppingCart className="h-8 w-8" />
            Mon Panier
          </h2>

          {message && (
            <div className={`px-4 py-3 rounded mb-4 ${message.includes('succès') ? 'bg-green-100 border border-green-400 text-green-700' : 'bg-red-100 border border-red-400 text-red-700'}`}>
              {message}
            </div>
          )}

          {isEmpty ? (
            <div className="text-center py-12">
              <ShoppingCart className="h-24 w-24 mx-auto text-gray-300 mb-4" />
              <p className="text-xl text-gray-600 mb-4">Votre panier est vide</p>
              <Link to="/scanner">
                <Button className="bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500">Scanner un produit</Button>
              </Link>
            </div>
          ) : (
            <>
              <div className="space-y-4 mb-6">
                {cart.map((item) => (
                  <div key={item.barcode} className="bg-gradient-to-br from-orange-50 to-pink-50 rounded-lg p-4 flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-semibold text-lg">{item.product_name}</p>
                      <p className="text-gray-600">{item.brands}</p>
                      <p className="text-sm text-blue-600">Score Yumi: {item.yumi_score}/100</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => updateQuantity(item.barcode, item.quantity - 1)}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        <span className="font-semibold w-8 text-center">{item.quantity}</span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => updateQuantity(item.barcode, item.quantity + 1)}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => removeFromCart(item.barcode)}
                        className="flex items-center gap-2"
                      >
                        <Trash2 className="h-4 w-4" />
                        Retirer
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t pt-6">
                <div className="flex justify-between items-center mb-4">
                  <p className="text-xl font-semibold">Total d'articles</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500 bg-clip-text text-transparent">
                    {cart.reduce((sum, item) => sum + item.quantity, 0)}
                  </p>
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Note: L'intégration avec les services de drive (Auchan, Carrefour, Leclerc) nécessite un partenariat commercial.
                  Cette fonctionnalité est actuellement simulée.
                </p>
                <Button
                  onClick={handleCheckout}
                  className="w-full text-lg py-6 bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500"
                >
                  Passer la commande (Simulation)
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default Cart
