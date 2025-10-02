import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { ArrowLeft, Lightbulb } from 'lucide-react'
import yumiLogo from '../assets/yumi_logo.png'

function Recommendations() {
  // Cette page pourrait afficher des recommandations générales ou basées sur l'historique
  // Pour l'instant, elle est simple.
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
            <Lightbulb className="h-8 w-8" />
            Mes Recommandations
          </h2>

          <div className="text-center py-12">
            <Lightbulb className="h-24 w-24 mx-auto text-gray-300 mb-4" />
            <p className="text-xl text-gray-600 mb-4">Explorez des produits adaptés à votre profil et vos objectifs.</p>
            <p className="text-gray-500 mb-6">Les recommandations personnalisées apparaissent après le scan d'un produit ou peuvent être générées ici en fonction de votre historique.</p>
            <Link to="/scanner">
              <Button className="bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500">Scanner un produit pour des recommandations</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Recommendations
