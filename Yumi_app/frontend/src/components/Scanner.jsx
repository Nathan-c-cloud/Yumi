import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Scan as ScanIcon } from 'lucide-react';
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

  useEffect(() => {
    // Charger le profil utilisateur au montage du composant
    const fetchUserProfile = async () => {
      try {
        const response = await fetch('http://localhost:5002/api/profile');
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
    if (!barcode) {
      setError('Veuillez entrer un code-barres.');
      return;
    }

    if (!userProfile) {
      setError('Profil utilisateur non chargé. Veuillez configurer votre profil.');
      return;
    }

    try {
      const response = await fetch('http://localhost:5002/api/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          barcode: barcode,
          user_profile: userProfile, // Envoyer le profil utilisateur
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
    }
  };

  const handleCameraScan = (data) => {
    if (data) {
      setBarcode(data);
      setIsScanning(false);
      handleScan();
    }
  };

  const handleError = (err) => {
    console.error(err);
    setError('Erreur d\'accès à la caméra. Assurez-vous d\'avoir donné les permissions.');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-100 via-pink-100 to-blue-100 p-4 flex flex-col items-center">
      <div className="w-full max-w-md bg-white rounded-lg shadow-xl p-6 mt-8">
        <div className="flex justify-between items-center mb-6">
          <Link to="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <img src={yumiLogo} alt="Yumi Logo" className="h-8" />
        </div>

        <h2 className="text-3xl font-bold text-center mb-6" style={{ color: '#FF7043' }}>Scanner un Produit</h2>

        <div className="space-y-4">
          <div>
            <Label htmlFor="barcode">Code-barres</Label>
            <div className="flex space-x-2">
              <Input
                id="barcode"
                type="text"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                placeholder="Entrez le code-barres"
                className="flex-grow"
              />
              <Button onClick={() => setIsScanning(!isScanning)} variant="outline" size="icon">
                <ScanIcon className="h-5 w-5" />
              </Button>
            </div>
          </div>

          {isScanning && (
            <div className="mt-4 p-2 border rounded-md bg-gray-50">
              <p className="text-center text-sm text-gray-600 mb-2">Scannez un code-barres avec votre caméra</p>
              <QrReader
                delay={300}
                onError={handleError}
                onResult={(result, error) => {
                  if (!!result) {
                    handleCameraScan(result?.text);
                  }

                  if (!!error) {
                    handleError(error);
                  }
                }}
                style={{ width: '100%' }}
                constraints={{
                  facingMode: 'environment'
                }}
              />
            </div>
          )}

          <Button onClick={handleScan} className="w-full bg-gradient-to-r from-orange-400 to-pink-500 text-white font-bold py-2 px-4 rounded-md">
            Scanner
          </Button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md text-center">
            {error}
          </div>
        )}

        {scanResult && (
          <div className="mt-6 p-4 bg-green-50 rounded-md shadow-inner">
            <h3 className="text-xl font-semibold" style={{ color: scanResult.color === '🔴' ? '#EF4444' : scanResult.color === '🟠' ? '#F97316' : scanResult.color === '🟡' ? '#FACC15' : '#22C55E' }}>
              {scanResult.interpretation}
            </h3>
            <p className="text-gray-700 mt-2">Produit: <span className="font-medium">{scanResult.product_name}</span></p>
            <p className="text-gray-700">Marque: <span className="font-medium">{scanResult.brands}</span></p>
            <p className="text-gray-700">Score Yumi: <span className="font-medium">{scanResult.yumi_score}/100</span></p>
            {scanResult.nutriscore_grade && <p className="text-gray-700">Nutriscore: <span className="font-medium">{scanResult.nutriscore_grade.toUpperCase()}</span></p>}
            {scanResult.warnings && scanResult.warnings.length > 0 && (
              <div className="mt-2">
                {scanResult.warnings.map((warning, index) => (
                  <p key={index} className="text-red-600 text-sm">{warning}</p>
                ))}
              </div>
            )}
            {scanResult.recommendations && scanResult.recommendations.length > 0 && (
              <div className="mt-4">
                <h4 className="font-semibold text-gray-800">Recommandations:</h4>
                <ul className="list-disc list-inside text-gray-700">
                  {scanResult.recommendations.map((rec, index) => (
                    <li key={index}>{rec.product_name} ({rec.yumi_score}/100)</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Scanner;
