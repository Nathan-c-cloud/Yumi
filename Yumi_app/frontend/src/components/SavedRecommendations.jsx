import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Bookmark, Trash2, Clock, Loader2, X, ShoppingCart, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_ENDPOINTS } from '../config/api';
import yumiLogo from '../assets/yumi_logo.png';

const SavedRecommendations = ({ userId }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingBarcode, setDeletingBarcode] = useState(null);
  const [addingToCart, setAddingToCart] = useState(null);

  // Charger les recommandations sauvegardées au montage du composant
  useEffect(() => {
    fetchSavedRecommendations();
  }, [userId]);

  const fetchSavedRecommendations = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/saved-recommendations`, {
        headers: {
          'X-User-ID': userId
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setRecommendations(data.recommendations || []);
      } else {
        setError(data.error || 'Erreur lors du chargement des recommandations');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur');
      console.error('Fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const clearAllRecommendations = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir effacer toutes les recommandations sauvegardées ?')) {
      return;
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/saved-recommendations`, {
        method: 'DELETE',
        headers: {
          'X-User-ID': userId
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setRecommendations([]);
      } else {
        setError(data.error || 'Erreur lors de la suppression des recommandations');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur');
      console.error('Delete error:', err);
    }
  };

  const deleteRecommendation = async (barcode) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette recommandation ?')) {
      return;
    }

    setDeletingBarcode(barcode);

    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/saved-recommendations/${barcode}`, {
        method: 'DELETE',
        headers: {
          'X-User-ID': userId
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setRecommendations(prev => prev.filter(item => item.barcode !== barcode));
      } else {
        setError(data.error || 'Erreur lors de la suppression de la recommandation');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur');
      console.error('Delete error:', err);
    } finally {
      setDeletingBarcode(null);
    }
  };

  const moveToCart = async (barcode) => {
    setAddingToCart(barcode);

    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/saved-recommendations/${barcode}/move-to-cart`, {
        method: 'POST',
        headers: {
          'X-User-ID': userId
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        alert('Produit ajouté au panier avec succès !');
        // Optionnellement, supprimer de la liste locale
        // setRecommendations(prev => prev.filter(item => item.barcode !== barcode));
      } else {
        setError(data.error || 'Erreur lors de l\'ajout au panier');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur');
      console.error('Add to cart error:', err);
    } finally {
      setAddingToCart(null);
    }
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#22C55E'; // Vert
    if (score >= 60) return '#FACC15'; // Jaune
    if (score >= 40) return '#F97316'; // Orange
    return '#EF4444'; // Rouge
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-100 via-pink-100 to-blue-100">
      {/* Header */}
      <div className="w-full bg-white/80 backdrop-blur-sm shadow-sm p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <Link to="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <img src={yumiLogo} alt="Yumi Logo" className="h-8" />
          <div className="w-10"></div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-4xl font-bold" style={{ color: '#FF7043' }}>
            Mes Recommandations
          </h2>
          {recommendations.length > 0 && (
            <Button
              onClick={clearAllRecommendations}
              variant="destructive"
              className="flex items-center space-x-2"
            >
              <Trash2 className="h-4 w-4" />
              <span>Tout effacer</span>
            </Button>
          )}
        </div>

        {error && (
          <div className="p-4 bg-red-100 text-red-700 rounded-xl text-center font-medium mb-6">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="animate-spin h-8 w-8 mr-3 text-blue-600" />
            <span className="text-blue-600 font-medium text-lg">Chargement des recommandations...</span>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="bg-white rounded-xl shadow-xl p-12">
            <div className="text-center text-gray-500">
              <Bookmark className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-xl font-medium mb-2">Aucune recommandation sauvegardée</h3>
              <p className="text-lg">Scannez des produits et sauvegardez les recommandations qui vous intéressent</p>
              <Link to="/scanner" className="inline-block mt-4">
                <Button className="bg-gradient-to-r from-orange-400 to-pink-500 text-white">
                  Scanner un produit
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((item, index) => (
              <div key={index} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-grow">
                    <div className="flex items-center space-x-3 mb-3">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-600 text-sm">
                        Sauvegardé le {formatDate(item.saved_at)}
                      </span>
                      <Star className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                        {item.source === 'recommendation' ? 'Recommandé' : 'Manuel'}
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-gray-800 mb-1">
                      {item.product_name}
                    </h3>

                    <p className="text-gray-600 mb-3">
                      <span className="font-medium">Marque:</span> {item.brands}
                    </p>

                    <p className="text-sm text-gray-500 mb-3">
                      <span className="font-medium">Code-barres:</span> {item.barcode}
                    </p>

                    <div className="flex items-center space-x-4 mb-4">
                      <div className="bg-gradient-to-r from-orange-50 to-pink-50 px-4 py-2 rounded-lg">
                        <span
                          className="text-lg font-bold"
                          style={{ color: getScoreColor(item.yumi_score) }}
                        >
                          Score Yumi: {item.yumi_score}/100
                        </span>
                      </div>

                      {item.nutriscore_grade && (
                        <div className="bg-gray-100 px-3 py-2 rounded-lg">
                          <span className="text-sm font-medium text-gray-700">
                            Nutriscore: {item.nutriscore_grade.toUpperCase()}
                          </span>
                        </div>
                      )}
                    </div>

                    {item.interpretation && (
                      <div className="mb-4">
                        <span
                          className="inline-block px-3 py-1 rounded-full text-sm font-medium"
                          style={{
                            backgroundColor: item.color === '🔴' ? '#FEE2E2' :
                                           item.color === '🟠' ? '#FED7AA' :
                                           item.color === '🟡' ? '#FEF3C7' : '#D1FAE5',
                            color: item.color === '🔴' ? '#DC2626' :
                                   item.color === '🟠' ? '#EA580C' :
                                   item.color === '🟡' ? '#D97706' : '#059669'
                          }}
                        >
                          {item.interpretation}
                        </span>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center space-x-3">
                      <Button
                        onClick={() => moveToCart(item.barcode)}
                        className="bg-green-500 hover:bg-green-600 text-white flex items-center space-x-2"
                        disabled={addingToCart === item.barcode}
                      >
                        {addingToCart === item.barcode ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <ShoppingCart className="h-4 w-4" />
                        )}
                        <span>Ajouter au panier</span>
                      </Button>
                    </div>
                  </div>

                  {/* Bouton de suppression */}
                  <div className="ml-4">
                    <Button
                      onClick={() => deleteRecommendation(item.barcode)}
                      variant="ghost"
                      size="icon"
                      className="text-gray-400 hover:text-red-500 hover:bg-red-50"
                      disabled={deletingBarcode === item.barcode}
                    >
                      {deletingBarcode === item.barcode ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <X className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SavedRecommendations;
