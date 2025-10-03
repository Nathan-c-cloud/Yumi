import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { BrowserMultiFormatReader, NotFoundException, BarcodeFormat } from '@zxing/library';

const BarcodeScanner = ({ onScan, onError, isActive }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const codeReaderRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [scanningActive, setScanningActive] = useState(false);
  const [detectionCount, setDetectionCount] = useState(0);

  const stopBarcodeDetection = useCallback(() => {
    if (codeReaderRef.current && scanningActive) {
      codeReaderRef.current.reset();
      setScanningActive(false);
    }
  }, [scanningActive]);

  const stopCamera = useCallback(() => {
    stopBarcodeDetection();

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, [stopBarcodeDetection]);

  const startBarcodeDetection = useCallback(async () => {
    if (!codeReaderRef.current || !videoRef.current || scanningActive) {
      return;
    }

    try {
      setScanningActive(true);
      setDetectionCount(0);

      // Configuration optimisée pour les codes-barres
      const hints = new Map();
      hints.set(2, [
        BarcodeFormat.EAN_13,
        BarcodeFormat.EAN_8,
        BarcodeFormat.CODE_128,
        BarcodeFormat.CODE_39,
        BarcodeFormat.UPC_A,
        BarcodeFormat.UPC_E,
        BarcodeFormat.ITF
      ]);

      codeReaderRef.current.hints = hints;

      // Utiliser ZXing pour détecter les codes-barres en continu avec une fréquence optimisée
      await codeReaderRef.current.decodeFromVideoDevice(
        undefined, // deviceId
        videoRef.current,
        (result, err) => {
          if (result) {
            const barcodeText = result.getText();
            console.log('Code-barres détecté:', barcodeText);

            // Valider que c'est un code-barres de produit (longueur appropriée)
            if (barcodeText && (barcodeText.length === 13 || barcodeText.length === 8 || barcodeText.length === 12)) {
              onScan(barcodeText);
              stopBarcodeDetection();
            } else {
              console.log('Code-barres non valide, continuez le scan...');
            }
          }

          if (err && !(err instanceof NotFoundException)) {
            console.error('Erreur de détection:', err);
          }

          // Compter les tentatives de détection
          setDetectionCount(prev => prev + 1);
        }
      );
    } catch (err) {
      console.error('Erreur lors du démarrage de la détection:', err);
      setScanningActive(false);
      onError(err);
    }
  }, [scanningActive, onScan, onError, stopBarcodeDetection]);

  const startCamera = useCallback(async () => {
    try {
      setIsLoading(true);

      // Configuration optimisée pour la lecture de codes-barres
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { exact: 'environment' }, // Forcer la caméra arrière
          width: { ideal: 1920, min: 640 },
          height: { ideal: 1080, min: 480 },
          frameRate: { ideal: 30, min: 15 },
          focusMode: 'continuous',
          exposureMode: 'continuous',
          whiteBalanceMode: 'continuous'
        }
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setIsLoading(false);
          // Attendre un peu avant de démarrer la détection pour laisser la caméra s'ajuster
          setTimeout(() => {
            startBarcodeDetection();
          }, 1000);
        };
      }
    } catch (err) {
      console.error('Erreur démarrage caméra:', err);

      // Fallback si la caméra arrière n'est pas disponible
      try {
        const fallbackStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'environment',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });

        streamRef.current = fallbackStream;
        if (videoRef.current) {
          videoRef.current.srcObject = fallbackStream;
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play();
            setIsLoading(false);
            setTimeout(() => {
              startBarcodeDetection();
            }, 1000);
          };
        }
      } catch (fallbackErr) {
        console.error('Erreur fallback caméra:', fallbackErr);
        onError(fallbackErr);
        setIsLoading(false);
      }
    }
  }, [onError, startBarcodeDetection]);

  useEffect(() => {
    // Initialiser le lecteur avec des paramètres optimisés
    codeReaderRef.current = new BrowserMultiFormatReader();

    // Configuration des hints pour améliorer la performance
    const hints = new Map();
    hints.set(2, [
      BarcodeFormat.EAN_13,
      BarcodeFormat.EAN_8,
      BarcodeFormat.CODE_128,
      BarcodeFormat.CODE_39,
      BarcodeFormat.UPC_A,
      BarcodeFormat.UPC_E
    ]);
    codeReaderRef.current.hints = hints;

    if (isActive) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [isActive, startCamera, stopCamera]);

  const handleManualScan = () => {
    const barcode = prompt('Entrez le code-barres manuellement:');
    if (barcode && barcode.trim()) {
      onScan(barcode.trim());
    }
  };

  const handleRetryDetection = () => {
    if (!scanningActive && !isLoading) {
      startBarcodeDetection();
    }
  };

  return (
    <div className="relative w-full h-64 bg-black rounded-md overflow-hidden">
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        playsInline
        muted
        autoPlay
      />
      <canvas
        ref={canvasRef}
        style={{ display: 'none' }}
      />

      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70 text-white">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
            <p>Activation de la caméra...</p>
          </div>
        </div>
      )}

      {!isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          {/* Overlay pour guider le scan avec des conseils */}
          <div className="border-2 border-white border-dashed w-64 h-32 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <span className="text-white text-sm bg-black bg-opacity-50 px-2 py-1 rounded block mb-1">
                {scanningActive ? `Scan en cours... (${detectionCount})` : 'Placez le code-barres ici'}
              </span>
              {scanningActive && (
                <span className="text-white text-xs bg-black bg-opacity-50 px-2 py-1 rounded">
                  Tenez fermement, bien éclairé
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {!isLoading && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
          {!scanningActive && (
            <Button
              onClick={handleRetryDetection}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm"
            >
              Relancer le scan
            </Button>
          )}
          <Button
            onClick={handleManualScan}
            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-md text-sm"
          >
            Saisir manuellement
          </Button>
        </div>
      )}
    </div>
  );
};

export default BarcodeScanner;
