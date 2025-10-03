import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Scan as ScanIcon, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { API_ENDPOINTS } from '../config/api';
import BarcodeScanner from './BarcodeScanner';
import ScoreExplanation from './ScoreExplanation';
import yumiLogo from '../assets/yumi_logo.png';

const Scanner = ({ userId }) => {
  const [barcode, setBarcode] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [cameraPermission, setCameraPermission] = useState(null); // null, 'granted', 'denied'
  const [isLoading, setIsLoading] = useState(false); // Ajout de l'état de chargement

  useEffect(() => {
    // Charger le profil utilisateur au montage du composant
    const fetchUserProfile = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.PROFILE, {
          headers: {
            'X-User-ID': userId
          }
        });
        const data = await response.json();
        if (response.ok && data.success) {
          setUserProfile(data.profile);
        } else {
          console.error('Failed to fetch user profile:', data.error);
        }
      } catch (err) {
        console.error('Error fetching user profile:', err);
      }
    };
    fetchUserProfile();
  }, [userId]);

  // Fonction pour vérifier les permissions de caméra
  const checkCameraPermission = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setCameraPermission('not-supported');
        setError('Votre navigateur ne supporte pas l\'accès à la caméra.');
        return false;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment' // Caméra arrière pour scanner
        }
      });

      // Si on arrive ici, la permission est accordée
      stream.getTracks().forEach(track => track.stop()); // Arrêter le stream de test
      setCameraPermission('granted');
      setError(null);
      return true;
    } catch (err) {
      console.error('Erreur permission caméra:', err);
      if (err.name === 'NotAllowedError') {
        setCameraPermission('denied');
        setError('Permission d\'accès à la caméra refusée. Veuillez autoriser l\'accès dans les paramètres de votre navigateur.');
      } else if (err.name === 'NotFoundError') {
        setCameraPermission('no-camera');
        setError('Aucune caméra trouvée sur cet appareil.');
      } else {
        setCameraPermission('error');
        setError('Erreur d\'accès à la caméra: ' + err.message);
      }
      return false;
    }
  };

  const handleScan = async () => {
    setError(null);
    setScanResult(null);
    setIsLoading(true); // Démarrer le chargement

    if (!barcode) {
      setError('Veuillez entrer un code-barres.');
      setIsLoading(false);
      return;
    }

    // Afficher un avertissement si pas de profil mais permettre quand même le scan
    if (!userProfile) {
      console.warn('Aucun profil utilisateur trouvé - utilisation du profil par défaut');
    }

    try {
      const response = await fetch(API_ENDPOINTS.SCAN, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId // Envoyer l'ID utilisateur dans l'en-tête
        },
        body: JSON.stringify({
          barcode: barcode
        }),
      });
      const data = await response.json();

      if (data.success) {
        setScanResult(data);
      } else {
        setError(data.error || 'Erreur lors du scan du produit.');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur. Veuillez vérifier que le backend est lancé.');
      console.error('Fetch error:', err);
    } finally {
      setIsLoading(false); // Arrêter le chargement dans tous les cas
    }
  };

  const handleCameraScan = async (data) => {
    if (data) {
      setBarcode(data);
      setIsScanning(false);

      // Lancer automatiquement l'analyse avec le chargement
      setError(null);
      setScanResult(null);
      setIsLoading(true);

      if (!userProfile) {
        console.warn('Aucun profil utilisateur trouvé - utilisation du profil par défaut');
      }

      try {
        const response = await fetch(API_ENDPOINTS.SCAN, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': userId
          },
          body: JSON.stringify({
            barcode: data
          }),
        });
        const responseData = await response.json();

        if (responseData.success) {
          setScanResult(responseData);
        } else {
          setError(responseData.error || 'Erreur lors du scan du produit.');
        }
      } catch (err) {
        setError('Erreur de connexion au serveur. Veuillez vérifier que le backend est lancé.');
        console.error('Fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleError = (err) => {
    console.error(err);
    setError('Erreur d\'accès à la caméra. Assurez-vous d\'avoir donné les permissions.');
  };

  // Fonction pour démarrer le scan avec vérification des permissions
  const startCameraScanning = async () => {
    if (cameraPermission === 'granted') {
      setIsScanning(true);
      return;
    }

    const hasPermission = await checkCameraPermission();
    if (hasPermission) {
      setIsScanning(true);
    }
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
          <div className="w-10"></div> {/* Spacer for centering logo */}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-6">
        <h2 className="text-4xl font-bold text-center mb-8" style={{ color: '#FF7043' }}>
          Scanner un Produit
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Scanner Section */}
          <div className="bg-white rounded-xl shadow-xl p-6">
            <div className="space-y-6">
              <div>
                <Label htmlFor="barcode" className="text-lg font-medium">Code-barres</Label>
                <div className="flex space-x-2 mt-2">
                  <Input
                    id="barcode"
                    type="text"
                    value={barcode}
                    onChange={(e) => setBarcode(e.target.value)}
                    placeholder="Entrez le code-barres"
                    className="flex-grow text-lg p-3"
                  />
                  <Button onClick={startCameraScanning} variant="outline" size="lg">
                    <ScanIcon className="h-6 w-6" />
                  </Button>
                </div>
              </div>

              {isScanning && (
                <div className="p-4 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50">
                  <p className="text-center text-gray-600 mb-4 font-medium">
                    Caméra activée - Pointez vers un code-barres
                  </p>
                  <BarcodeScanner
                    onScan={handleCameraScan}
                    onError={handleError}
                    isActive={isScanning}
                  />
                  <Button
                    onClick={() => setIsScanning(false)}
                    variant="outline"
                    className="w-full mt-4"
                  >
                    Arrêter le scan
                  </Button>
                </div>
              )}

              <Button
                onClick={handleScan}
                className="w-full bg-gradient-to-r from-orange-400 to-pink-500 text-white font-bold py-3 px-6 rounded-xl text-lg"
              >
                Scanner
              </Button>

              {error && (
                <div className="p-4 bg-red-100 text-red-700 rounded-xl text-center font-medium">
                  {error}
                </div>
              )}

              {isLoading && (
                <div className="flex items-center justify-center p-4 bg-blue-50 rounded-xl">
                  <Loader2 className="animate-spin h-5 w-5 mr-2 text-blue-600" />
                  <span className="text-blue-600 font-medium">Analyse en cours...</span>
                </div>
              )}
            </div>
          </div>

          {/* Results Section */}
          <div className="bg-white rounded-xl shadow-xl p-6">
            {scanResult ? (
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-2xl font-bold mb-2" style={{
                    color: scanResult.color === '🔴' ? '#EF4444' :
                           scanResult.color === '🟠' ? '#F97316' :
                           scanResult.color === '🟡' ? '#FACC15' : '#22C55E'
                  }}>
                    {scanResult.interpretation}
                  </h3>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-gray-700 text-lg">
                      <span className="font-semibold">Produit:</span> {scanResult.product_name}
                    </p>
                    <p className="text-gray-700 text-lg">
                      <span className="font-semibold">Marque:</span> {scanResult.brands}
                    </p>
                  </div>

                  <div className="bg-gradient-to-r from-orange-50 to-pink-50 p-4 rounded-lg">
                    <p className="text-gray-800 text-xl font-bold">
                      Score Yumi: {scanResult.yumi_score}/100
                    </p>
                    {scanResult.nutriscore_grade && (
                      <p className="text-gray-700 text-lg mt-2">
                        <span className="font-semibold">Nutriscore:</span> {scanResult.nutriscore_grade.toUpperCase()}
                      </p>
                    )}
                  </div>

                  {/* Composant d'explication des scores */}
                  <ScoreExplanation
                    yumiScore={scanResult.yumi_score}
                    color={scanResult.color}
                    warnings={scanResult.warnings || []}
                  />

                  {scanResult.recommendations && scanResult.recommendations.length > 0 && (
                    <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-400">
                      <h4 className="font-semibold text-green-800 mb-3">💡 Recommandations:</h4>
                      <ul className="space-y-2">
                        {scanResult.recommendations.map((rec, index) => (
                          <li key={index} className="flex justify-between items-center bg-white p-2 rounded">
                            <span className="text-gray-700">{rec.product_name}</span>
                            <span className="font-semibold text-green-600">({rec.yumi_score}/100)</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full min-h-[300px]">
                <div className="text-center text-gray-500">
                  <ScanIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">Scannez un produit pour voir les résultats ici</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Scanner;
