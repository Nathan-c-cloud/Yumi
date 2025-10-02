import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { BrowserMultiFormatReader, NotFoundException } from '@zxing/library';

const BarcodeScanner = ({ onScan, onError, isActive }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const codeReaderRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [scanningActive, setScanningActive] = useState(false);

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
      // Utiliser ZXing pour détecter les codes-barres en continu
      await codeReaderRef.current.decodeFromVideoDevice(
        undefined, // deviceId (undefined = utiliser l'appareil par défaut)
        videoRef.current,
        (result, err) => {
          if (result) {
            console.log('Code-barres détecté:', result.getText());
            onScan(result.getText());
            // Arrêter la détection après avoir trouvé un code
            stopBarcodeDetection();
          }

          if (err && !(err instanceof NotFoundException)) {
            console.error('Erreur de détection:', err);
            // Ne pas arrêter la détection pour les erreurs non critiques
          }
        }
      );
    } catch (err) {
      console.error('Erreur lors du démarrage de la détection:', err);
      setScanningActive(false);
    }
  }, [scanningActive, onScan, stopBarcodeDetection]);

  const startCamera = useCallback(async () => {
    try {
      setIsLoading(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setIsLoading(false);
          // Démarrer la détection de codes-barres avec ZXing
          startBarcodeDetection();
        };
      }
    } catch (err) {
      console.error('Erreur démarrage caméra:', err);
      onError(err);
      setIsLoading(false);
    }
  }, [onError, startBarcodeDetection]);

  useEffect(() => {
    // Initialiser le lecteur de codes-barres
    codeReaderRef.current = new BrowserMultiFormatReader();

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
    // Pour le moment, demander à l'utilisateur de saisir manuellement
    const barcode = prompt('Entrez le code-barres manuellement:');
    if (barcode) {
      onScan(barcode);
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
          {/* Overlay pour guider le scan */}
          <div className="border-2 border-white border-dashed w-64 h-32 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm bg-black bg-opacity-50 px-2 py-1 rounded">
              {scanningActive ? 'Recherche de code-barres...' : 'Placez le code-barres ici'}
            </span>
          </div>
        </div>
      )}

      {!isLoading && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
          {!scanningActive && (
            <Button
              onClick={handleRetryDetection}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
            >
              Relancer le scan
            </Button>
          )}
          <Button
            onClick={handleManualScan}
            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-md"
          >
            Saisir manuellement
          </Button>
        </div>
      )}
    </div>
  );
};

export default BarcodeScanner;
