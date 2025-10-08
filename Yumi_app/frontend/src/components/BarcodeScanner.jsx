import React, { useRef, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { BrowserMultiFormatReader } from '@zxing/library';

const BarcodeScanner = ({ onScan, onError, isActive }) => {
  const videoRef = useRef(null);
  const readerRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isActive) {
      startScanner();
    } else {
      stopScanner();
    }

    return () => stopScanner();
  }, [isActive]);

  const startScanner = async () => {
    try {
      setIsLoading(true);

      readerRef.current = new BrowserMultiFormatReader();

      await readerRef.current.decodeFromVideoDevice(
        undefined,
        videoRef.current,
        (result) => {
          if (result) {
            const barcode = result.getText();
            if (barcode && /^[0-9]{8,13}$/.test(barcode)) {
              onScan(barcode);
              stopScanner();
            }
          }
        }
      );

      setIsLoading(false);
    } catch (error) {
      setIsLoading(false);
      onError(error);
    }
  };

  const stopScanner = () => {
    if (readerRef.current) {
      readerRef.current.reset();
    }
  };

  const handleManualInput = () => {
    const barcode = prompt('Entrez le code-barres:');
    if (barcode && /^[0-9]{8,13}$/.test(barcode.trim())) {
      onScan(barcode.trim());
    } else if (barcode) {
      alert('Code-barres invalide. Utilisez 8 à 13 chiffres.');
    }
  };

  return (
    <div className="relative w-full h-64 bg-black rounded-md overflow-hidden">
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        autoPlay
        muted
        playsInline
      />

      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70 text-white">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
            <p>Activation de la caméra...</p>
          </div>
        </div>
      )}

      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="border-2 border-white border-dashed w-64 h-32 rounded-lg flex items-center justify-center">
          <span className="text-white text-sm bg-black bg-opacity-50 px-2 py-1 rounded">
            Placez le code-barres ici
          </span>
        </div>
      </div>

      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
        <Button onClick={handleManualInput} className="bg-orange-500 hover:bg-orange-600 text-white">
          Saisie manuelle
        </Button>
      </div>
    </div>
  );
};

export default BarcodeScanner;
