import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Scan, ShoppingCart, User, History } from 'lucide-react'
import yumiLogo from '../assets/yumi_logo.png'

function Home({ userId }) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-md p-4 sticky top-0 z-10">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <img src={yumiLogo} alt="Yumi" className="h-12" />
          </div>
          <nav className="flex gap-4 items-center">
            <Link to="/scanner">
              <Button variant="ghost" className="flex items-center gap-2">
                <Scan className="h-5 w-5" />
                Scanner
              </Button>
            </Link>
            <Link to="/history">
              <Button variant="ghost" className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Historique
              </Button>
            </Link>
            <Link to="/cart">
              <Button variant="ghost" className="flex items-center gap-2">
                <ShoppingCart className="h-5 w-5" />
                Panier
              </Button>
            </Link>
            <Link to="/profile">
              <Button variant="ghost" className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Profil
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 container mx-auto px-4 py-16">
        <div className="text-center max-w-3xl mx-auto">
          <img src={yumiLogo} alt="Yumi" className="h-32 mx-auto mb-8" />
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500 bg-clip-text text-transparent">
            Votre Assistant Nutritionnel Personnalisé
          </h1>
          <p className="text-xl text-gray-700 mb-8">
            Scannez, analysez et choisissez les meilleurs produits adaptés à vos besoins avec un scoring personnalisé par intelligence artificielle.
          </p>

          <div className="flex gap-4 justify-center mb-12">
            <Link to="/scanner">
              <Button size="lg" className="text-lg px-8 py-6 bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500">
                Commencer à scanner
              </Button>
            </Link>
            <Link to="/profile">
              <Button size="lg" variant="outline" className="text-lg px-8 py-6">
                Configurer mon profil
              </Button>
            </Link>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-4 gap-8 mt-16">
            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
              <div className="bg-gradient-to-br from-orange-400 to-orange-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Scan className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Scan Intelligent</h3>
              <p className="text-gray-600">
                Scannez les codes-barres pour obtenir un score personnalisé basé sur vos préférences et restrictions alimentaires.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
              <div className="bg-gradient-to-br from-purple-400 to-purple-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <History className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Historique</h3>
              <p className="text-gray-600">
                Consultez l'historique de tous vos scans précédents et suivez vos choix alimentaires dans le temps.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
              <div className="bg-gradient-to-br from-pink-400 to-pink-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Profil Personnalisé</h3>
              <p className="text-gray-600">
                Configurez votre profil avec vos objectifs de santé, restrictions alimentaires et allergies pour un scoring adapté.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
              <div className="bg-gradient-to-br from-blue-400 to-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShoppingCart className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Panier Intelligent</h3>
              <p className="text-gray-600">
                Ajoutez vos produits au panier et recevez des recommandations pour améliorer vos choix nutritionnels.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-sm p-6 mt-16">
        <div className="container mx-auto text-center text-gray-600">
          <p>&copy; 2025 Yumi. Tous droits réservés.</p>
        </div>
      </footer>
    </div>
  )
}

export default Home
