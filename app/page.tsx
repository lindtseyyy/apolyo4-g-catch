'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, FileSearch, ShieldCheck, AlertTriangle } from 'lucide-react';

export default function Home() {
  const [image, setImage] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<'authentic' | 'forged' | null>(null);

  // Demo function to simulate the forensic analysis delay
  const handleScan = () => {
    setIsScanning(true);
    setResult(null);

    // Simulate a 3-second API call to the Python backend
    setTimeout(() => {
      setIsScanning(false);
      // For the demo, randomly assign a result to test both UI states
      setResult(Math.random() > 0.5 ? 'authentic' : 'forged');
    }, 3000);
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setImage(imageUrl);
      setResult(null); // Reset result on new upload
    }
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-white flex flex-col items-center justify-center p-6 font-sans">

      {/* Header */}
      <div className="text-center mb-10 max-w-lg">
        <h1 className="text-5xl font-extrabold mb-4 tracking-tight text-emerald-500">
          G-<span className="text-white">Catch</span>
        </h1>
        <p className="text-neutral-400">
          Forensic pixel analysis for GCash transaction verification. Upload a receipt to detect anomalies and protect your business.
        </p>
      </div>

      {/* Main Scanner Container */}
      <div className="w-full max-w-md bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden">

        {/* Upload Zone */}
        {!image && (
          <div className="border-2 border-dashed border-neutral-700 rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer hover:border-emerald-500 hover:bg-neutral-800/50 transition-colors relative">
            <input
              type="file"
              accept="image/*"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleImageUpload}
            />
            <UploadCloud className="w-12 h-12 text-neutral-500 mb-4" />
            <p className="text-sm text-neutral-300 font-medium">Tap or drop GCash receipt image</p>
          </div>
        )}

        {/* Image Preview & Scanning Animation */}
        {image && (
          <div className="relative rounded-xl overflow-hidden bg-black border border-neutral-800">
            <img src={image} alt="Uploaded Receipt" className={`w-full h-auto max-h-[400px] object-contain ${isScanning ? 'opacity-50 blur-sm' : ''} transition-all`} />

            {/* The Framer Motion Laser Line */}
            {isScanning && (
              <motion.div
                className="absolute left-0 right-0 h-1 bg-emerald-500 shadow-[0_0_20px_rgba(16,185,129,1)]"
                initial={{ top: '0%' }}
                animate={{ top: '100%' }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  repeatType: 'reverse',
                  ease: 'linear',
                }}
              />
            )}

            {/* Scanning Overlay Text */}
            {isScanning && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-emerald-400 font-mono text-sm font-bold bg-black/50 backdrop-blur-sm transition-all">
                <FileSearch className="w-10 h-10 mb-2 animate-pulse" />
                <p className="tracking-widest animate-pulse">RUNNING FORENSICS...</p>
              </div>
            )}
          </div>
        )}

        {/* Controls */}
        {image && !isScanning && !result && (
          <button
            onClick={handleScan}
            className="w-full mt-6 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg shadow-emerald-900/50 active:scale-[0.98]"
          >
            Run Deep Scan
          </button>
        )}

        {/* Result Dashboard */}
        {result && (
          <div className={`mt-6 p-5 rounded-xl border ${result === 'authentic' ? 'bg-emerald-950/40 border-emerald-800/50' : 'bg-red-950/40 border-red-800/50'} transition-all`}>
            <div className="flex items-center gap-3 mb-3">
              {result === 'authentic' ? (
                <ShieldCheck className="w-7 h-7 text-emerald-500" />
              ) : (
                <AlertTriangle className="w-7 h-7 text-red-500" />
              )}
              <h3 className={`text-lg font-bold ${result === 'authentic' ? 'text-emerald-400' : 'text-red-400'}`}>
                {result === 'authentic' ? '98.4% Authentic Match' : 'FORGERY DETECTED'}
              </h3>
            </div>
            <p className="text-sm leading-relaxed text-neutral-300">
              {result === 'authentic'
                ? 'Pixel density and OCR validation passed. No structural anomalies or ELA inconsistencies found.'
                : 'Error Level Analysis (ELA) detected pixel compression inconsistencies. Font spacing violates standard GCash UI matrix.'}
            </p>
            <button
              onClick={() => { setImage(null); setResult(null); }}
              className="mt-5 text-sm font-semibold text-neutral-400 hover:text-white underline underline-offset-4 transition-colors"
            >
              Scan another receipt
            </button>
          </div>
        )}

      </div>
    </main>
  );
}
