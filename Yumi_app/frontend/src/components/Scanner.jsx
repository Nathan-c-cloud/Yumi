import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Scan as ScanIcon, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { QrReader } from 'react-qr-reader';
import yumiLogo from '../assets/yumi_logo.png';

const Scanner = ({ userId }) => {
  const [barcode, setBarcode] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(false); // Nouvel état pour le chargement

  useEffect(() => {
    // Charger le profil utilisateur au montage du composant
    const fetchUserProfile = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5002/api/profile" );
        const data = await response.json();
        if (response.ok) {
          setUserProfile(data);
        } else {
          console.error('Failed to fetch user profile:', data.error);
        }
      } catch (err) {
        console.error('Error fetching user profile:', err);
      }
    };
    fetchUserProfile();
  }, []);

  const handleScan = async () => {
    setError(null);
    setScanResult(null);
    setIsLoading(true); // Démarrer le chargement

    if (!barcode) {
      setError('Veuillez entrer un code-barres.');
      setIsLoading(false);
      return;
    }

    if (!userProfile) {
      setError('Profil utilisateur non chargé. Veuillez configurer votre profil.');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:5002/api/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          barcode: barcode,
          user_profile: userProfile,
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

      // Lancer automatiquement l'analyse dès qu'un code-barres est détecté
      setError(null);
      setScanResult(null);
      setIsLoading(true);

      if (!userProfile) {
        setError('Profil utilisateur non chargé. Veuillez configurer votre profil.');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`http://127.0.0.1:5002/api/scan`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            barcode: data, // Utiliser directement le code-barres scanné
            user_profile: userProfile,
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
                    disabled={isLoading} // Désactiver pendant le chargement
                  />
                  <Button
                    onClick={() => setIsScanning(!isScanning)}
                    variant="outline"
                    size="lg"
                    disabled={isLoading} // Désactiver pendant le chargement
                  >
                    <ScanIcon className="h-6 w-6" />
                  </Button>
                </div>
              </div>

              {isScanning && (
                <div className="p-4 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50">
                  <p className="text-center text-gray-600 mb-4 font-medium">
                    Positionnez le code-barres dans le cadre ci-dessous
                  </p>
                  <div className="relative mx-auto" style={{ width: '300px', height: '250px' }}>
                    <QrReader
                      delay={300}
                      onError={handleError}
                      onScan={(result) => {
                        if (result) {
                          handleCameraScan(result);
                        }
                      }}
                      style={{
                        width: '100%',
                        height: '100%'
                      }}
                      facingMode="environment"
                    />
                    {/* Overlay pour aider au cadrage */}
                    <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                      <div className="w-48 h-16 border-2 border-orange-400 border-dashed rounded-md bg-transparent opacity-80">
                      </div>
                    </div>
                  </div>
                  <p className="text-center text-sm text-gray-500 mt-2">
                    Alignez le code-barres dans le cadre orange
                  </p>
                </div>
              )}

              <div className="space-y-4">
                <Button
                  onClick={handleScan}
                  disabled={isLoading} // Désactiver pendant le chargement
                  className="w-full bg-gradient-to-r from-orange-400 to-pink-500 text-white font-bold py-3 px-6 rounded-xl text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Scanner
                </Button>

                {/* Message de chargement */}
                {isLoading && (
                  <div className="flex items-center justify-center space-x-2 text-gray-600">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm font-medium">Analyse en cours...</span>
                  </div>
                )}
              </div>

              {error && (
                <div className="p-4 bg-red-100 text-red-700 rounded-xl text-center font-medium">
                  {error}
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

                  {scanResult.warnings && scanResult.warnings.length > 0 && (
                    <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-400">
                      <h4 className="font-semibold text-red-800 mb-2">⚠️ Attention:</h4>
                      {scanResult.warnings.map((warning, index) => (
                        <p key={index} className="text-red-700">{warning}</p>
                      ))}
                    </div>
                  )}

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
