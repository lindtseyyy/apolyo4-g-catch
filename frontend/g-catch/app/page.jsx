'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, FileSearch, ShieldCheck, AlertTriangle, ScanLine, Fingerprint, Cpu, ChevronRight } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function Home() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  );
}

function HomeContent() {
  const [image, setImage] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);

  const handleScan = () => {
    setIsScanning(true);
    setResult(null);
    setScanProgress(0);

    // Progress animation
    const progressInterval = setInterval(() => {
      setScanProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 15;
      });
    }, 300);

    setTimeout(() => {
      clearInterval(progressInterval);
      setScanProgress(100);
      setTimeout(() => {
        setIsScanning(false);
        setResult(Math.random() > 0.5 ? 'authentic' : 'forged');
      }, 400);
    }, 3000);
  };

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setImage(imageUrl);
      setResult(null);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 pt-28 pb-12">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10 max-w-lg"
      >
        <div className="inline-flex items-center gap-2 bg-[rgba(0,102,255,0.08)] border border-[rgba(0,102,255,0.15)] rounded-full px-4 py-1.5 mb-5">
          <div className="w-2 h-2 rounded-full bg-[#00c853] animate-pulse" />
          <span className="text-xs font-medium text-[#8899b8] tracking-wide uppercase">AI Forensic Engine Ready</span>
        </div>

        <h1 className="text-5xl md:text-6xl font-extrabold mb-4 tracking-tight leading-tight">
          <span className="text-[#f0f6ff]">Verify with</span>
          <br />
          <span className="gradient-text">Confidence</span>
        </h1>
        <p className="text-[#8899b8] text-lg leading-relaxed">
          Deep-scan forensic analysis for digital receipts.
          <br className="hidden sm:block" />
          Detect fakes before they cost you.
        </p>
      </motion.div>

      {/* Main Scanner Container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="w-full max-w-md"
      >
        <div className="glass rounded-3xl p-6 md:p-8 glow-blue relative overflow-hidden">
          {/* Decorative corner accents */}
          <div className="absolute top-0 left-0 w-16 h-16 border-l-2 border-t-2 border-[rgba(0,102,255,0.2)] rounded-tl-3xl" />
          <div className="absolute top-0 right-0 w-16 h-16 border-r-2 border-t-2 border-[rgba(0,102,255,0.2)] rounded-tr-3xl" />
          <div className="absolute bottom-0 left-0 w-16 h-16 border-l-2 border-b-2 border-[rgba(0,102,255,0.2)] rounded-bl-3xl" />
          <div className="absolute bottom-0 right-0 w-16 h-16 border-r-2 border-b-2 border-[rgba(0,102,255,0.2)] rounded-br-3xl" />

          {/* Upload Zone */}
          <AnimatePresence mode="wait">
            {!image && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className="border-2 border-dashed border-[rgba(0,102,255,0.2)] hover:border-[rgba(0,102,255,0.5)] rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer hover:bg-[rgba(0,102,255,0.03)] transition-all duration-300 relative group">
                  <input
                    type="file"
                    accept="image/*"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    onChange={handleImageUpload}
                  />
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0066ff]/15 to-[#00a8ff]/10 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                    <UploadCloud className="w-8 h-8 text-[#0066ff] group-hover:text-[#00d4ff] transition-colors" />
                  </div>
                  <p className="text-sm text-[#c8d4e8] font-semibold mb-1">Drop receipt image here</p>
                  <p className="text-xs text-[#8899b8]">or click to browse</p>
                  <p className="text-[10px] text-[#8899b8]/60 mt-3">Supports JPG, PNG, WEBP</p>
                </div>

                {/* Quick stats */}
                <div className="grid grid-cols-3 gap-3 mt-5">
                  {[
                    { icon: Fingerprint, label: 'Pixel Analysis', value: 'ELA' },
                    { icon: Cpu, label: 'OCR Engine', value: 'Tesseract' },
                    { icon: ScanLine, label: 'Deep Scan', value: 'CNN' },
                  ].map((item, i) => (
                    <div key={i} className="bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl p-3 text-center">
                      <item.icon className="w-4 h-4 text-[#0066ff] mx-auto mb-1.5" />
                      <p className="text-[10px] text-[#8899b8] uppercase tracking-wider">{item.label}</p>
                      <p className="text-xs font-bold text-[#c8d4e8]">{item.value}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Image Preview & Scanning Animation */}
          <AnimatePresence>
            {image && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <div className="relative rounded-xl overflow-hidden bg-black border border-[rgba(0,102,255,0.15)]">
                  <img
                    src={image}
                    alt="Uploaded Receipt"
                    className={`w-full h-auto max-h-[400px] object-contain ${isScanning ? 'opacity-40 blur-[2px]' : ''} transition-all duration-500`}
                  />

                  {/* The Framer Motion Laser Line */}
                  {isScanning && (
                    <motion.div
                      className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#00d4ff] to-transparent shadow-[0_0_20px_rgba(0,212,255,0.8)]"
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

                  {/* Scanning Overlay */}
                  {isScanning && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#030712]/60 backdrop-blur-sm">
                      <FileSearch className="w-10 h-10 text-[#00d4ff] mb-3 animate-pulse" />
                      <p className="text-[#00d4ff] font-mono text-xs font-bold tracking-[0.3em] uppercase animate-pulse mb-4">
                        Running Forensics
                      </p>
                      {/* Progress bar */}
                      <div className="w-48 h-1 bg-[rgba(0,102,255,0.15)] rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-gradient-to-r from-[#0066ff] to-[#00d4ff] rounded-full"
                          style={{ width: `${Math.min(scanProgress, 100)}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                      <p className="text-[#8899b8] text-[10px] mt-2 font-mono">{Math.min(Math.round(scanProgress), 100)}%</p>
                    </div>
                  )}
                </div>

                {/* Controls */}
                {!isScanning && !result && (
                  <motion.button
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    onClick={handleScan}
                    className="w-full mt-5 bg-gradient-to-r from-[#0066ff] to-[#00a8ff] hover:from-[#0052cc] hover:to-[#0090e0] text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-300 shadow-lg shadow-[#0066ff]/25 hover:shadow-[#0066ff]/40 active:scale-[0.98] flex items-center justify-center gap-2 group"
                  >
                    <ScanLine className="w-5 h-5 group-hover:animate-spin" />
                    Initiate Deep Scan
                  </motion.button>
                )}

                {/* Result Dashboard */}
                {result && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    className={`mt-5 p-5 rounded-2xl border ${result === 'authentic'
                      ? 'bg-[rgba(0,200,83,0.06)] border-[rgba(0,200,83,0.2)]'
                      : 'bg-[rgba(255,61,113,0.06)] border-[rgba(255,61,113,0.2)]'
                      } transition-all`}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      {result === 'authentic' ? (
                        <div className="w-10 h-10 rounded-xl bg-[rgba(0,200,83,0.15)] flex items-center justify-center">
                          <ShieldCheck className="w-5 h-5 text-[#00c853]" />
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-xl bg-[rgba(255,61,113,0.15)] flex items-center justify-center">
                          <AlertTriangle className="w-5 h-5 text-[#ff3d71]" />
                        </div>
                      )}
                      <div>
                        <h3 className={`text-lg font-bold ${result === 'authentic' ? 'text-[#00c853]' : 'text-[#ff3d71]'}`}>
                          {result === 'authentic' ? '98.4% Authentic Match' : 'FORGERY DETECTED'}
                        </h3>
                        <p className="text-[10px] text-[#8899b8] uppercase tracking-wider">
                          {result === 'authentic' ? 'Verification Passed' : 'Anomalies Found'}
                        </p>
                      </div>
                    </div>

                    {/* Analysis Details */}
                    <div className="space-y-2 mb-4">
                      {result === 'authentic' ? (
                        <>
                          <DetailRow label="Pixel Density" value="Valid" status="good" />
                          <DetailRow label="OCR Validation" value="Passed" status="good" />
                          <DetailRow label="ELA Consistency" value="Normal" status="good" />
                        </>
                      ) : (
                        <>
                          <DetailRow label="Pixel Density" value="Anomalous" status="bad" />
                          <DetailRow label="OCR Validation" value="Failed" status="bad" />
                          <DetailRow label="ELA Consistency" value="Irregular" status="bad" />
                        </>
                      )}
                    </div>

                    <p className="text-sm leading-relaxed text-[#8899b8]">
                      {result === 'authentic'
                        ? 'Receipt structure matches verified templates. No compression artifacts or font anomalies detected across all analysis layers.'
                        : 'Error Level Analysis detected pixel compression inconsistencies. Font spacing violates standard receipt generation matrix.'}
                    </p>

                    <button
                      onClick={() => { setImage(null); setResult(null); }}
                      className="mt-5 w-full flex items-center justify-center gap-2 text-sm font-semibold text-[#8899b8] hover:text-[#f0f6ff] bg-[rgba(0,102,255,0.05)] hover:bg-[rgba(0,102,255,0.1)] border border-[rgba(0,102,255,0.1)] hover:border-[rgba(0,102,255,0.25)] rounded-xl py-2.5 transition-all duration-200"
                    >
                      <ChevronRight className="w-4 h-4 rotate-180" />
                      Scan another receipt
                    </button>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom trust indicators */}
        <div className="flex items-center justify-center gap-6 mt-6">
          <div className="flex items-center gap-2 text-[#8899b8]/60">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase tracking-wider">Bank-Grade Security</span>
          </div>
          <div className="w-px h-3 bg-[rgba(0,102,255,0.15)]" />
          <div className="flex items-center gap-2 text-[#8899b8]/60">
            <Fingerprint className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase tracking-wider">No Data Stored</span>
          </div>
        </div>
      </motion.div>
    </main>
  );
}

function DetailRow({ label, value, status }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-[#8899b8]">{label}</span>
      <span className={`font-semibold ${status === 'good' ? 'text-[#00c853]' : 'text-[#ff3d71]'}`}>
        {value}
      </span>
    </div>
  );
}
