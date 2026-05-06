'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScanLine, Fingerprint, AlertTriangle, ChevronRight, FileSearch, Hash } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { saveScan, checkReferenceExists } from '@/lib/dbService';

import PageHeader from '@/components/scan/PageHeader';
import UploadZone from '@/components/scan/UploadZone';
import ImagePreview from '@/components/scan/ImagePreview';
import VerdictBanner from '@/components/scan/VerdictBanner';
import MetricsGrid from '@/components/scan/MetricsGrid';
import TabBar from '@/components/scan/TabBar';
import ElaTab from '@/components/scan/ElaTab';
import TypographyTab from '@/components/scan/TypographyTab';
import ReferenceTab from '@/components/scan/ReferenceTab';
import ConfirmModal from '@/components/scan/ConfirmModal';

export default function Home() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  );
}

const TABS = [
  { id: 'ela', label: 'ELA Test', icon: ScanLine },
  { id: 'typography', label: 'Typography', icon: Fingerprint },
  { id: 'reference', label: 'Reference No.', icon: Hash },
];

function HomeContent() {
  const [image, setImage] = useState(null);
  const [referenceNumber, setReferenceNumber] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [refExists, setRefExists] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [imageFile, setImageFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [scanError, setScanError] = useState(null);
  const [activeTab, setActiveTab] = useState('ela');

  // ── Handlers ──────────────────────────────────────────────

  const handleScan = async () => {
    if (!imageFile) return;

    setIsScanning(true);
    setResult(null);
    setAnalysisResult(null);
    setScanError(null);
    setScanProgress(0);
    setRefExists(null);
    setActiveTab('ela');

    const progressInterval = setInterval(() => {
      setScanProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 15;
      });
    }, 300);

    try {
      const formData = new FormData();
      formData.append('file', imageFile);

      const response = await fetch('http://localhost:8000/api/v1/analyze/receipt', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Analysis failed (${response.status})`);
      }

      const data = await response.json();
      clearInterval(progressInterval);
      setScanProgress(100);
      setAnalysisResult(data);

      const refField = data.fields?.reference_number;
      const extractedRef = refField?.text || null;

      if (extractedRef) {
        setReferenceNumber(extractedRef);
        try {
          const exists = await checkReferenceExists(extractedRef);
          setRefExists(exists);
        } catch (err) {
          console.error('Failed to check reference:', err);
        }
      } else {
        setReferenceNumber('REF-2026-' + String(Math.floor(Math.random() * 9000) + 1000));
      }

      const verdict = data.combined_verdict?.toLowerCase();
      setResult(verdict === 'authentic' ? 'authentic' : 'forged');
    } catch (err) {
      clearInterval(progressInterval);
      setScanProgress(0);
      setScanError(err.message || 'An unexpected error occurred during analysis.');
    } finally {
      await new Promise(resolve => setTimeout(resolve, 400));
      setIsScanning(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(URL.createObjectURL(file));
      setImageFile(file);
      setResult(null);
      setAnalysisResult(null);
      setScanError(null);
    }
  };

  const handleConfirm = async () => {
    try {
      await saveScan({ referenceNumber });
      setConfirmed(true);
      setShowModal(false);
    } catch (err) {
      console.error('Failed to save scan:', err);
    }
  };

  const handleReset = () => {
    setImage(null);
    setImageFile(null);
    setResult(null);
    setAnalysisResult(null);
    setScanError(null);
    setConfirmed(false);
    setReferenceNumber('');
    setActiveTab('ela');
  };

  // ── Render ────────────────────────────────────────────────

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 pt-28 pb-12">
      <PageHeader />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="w-full max-w-6xl"
      >
        <div className="glass rounded-3xl p-6 md:p-8 glow-blue relative overflow-hidden">
          {/* Decorative corner accents */}
          <div className="absolute top-0 left-0 w-16 h-16 border-l-2 border-t-2 border-[rgba(0,102,255,0.2)] rounded-tl-3xl" />
          <div className="absolute top-0 right-0 w-16 h-16 border-r-2 border-t-2 border-[rgba(0,102,255,0.2)] rounded-tr-3xl" />
          <div className="absolute bottom-0 left-0 w-16 h-16 border-l-2 border-b-2 border-[rgba(0,102,255,0.2)] rounded-bl-3xl" />
          <div className="absolute bottom-0 right-0 w-16 h-16 border-r-2 border-b-2 border-[rgba(0,102,255,0.2)] rounded-br-3xl" />

          <AnimatePresence mode="wait">
            {!image ? (
              <UploadZone onImageUpload={handleImageUpload} />
            ) : (
              <motion.div
                key="results"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex flex-col lg:flex-row gap-6">
                  {/* ===== LEFT COLUMN ===== */}
                  <div className="lg:w-2/5 flex-shrink-0 space-y-5">
                    <ImagePreview image={image} isScanning={isScanning} scanProgress={scanProgress} />

                    {scanError && !isScanning && (
                      <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 bg-[rgba(255,61,113,0.08)] border border-[rgba(255,61,113,0.2)] rounded-xl flex items-start gap-3"
                      >
                        <AlertTriangle className="w-5 h-5 text-[#ff3d71] flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm text-[#ff3d71] font-semibold">Scan Failed</p>
                          <p className="text-xs text-[#8899b8] mt-0.5">{scanError}</p>
                        </div>
                      </motion.div>
                    )}

                    {!isScanning && !result && (
                      <motion.button
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        onClick={handleScan}
                        className="w-full bg-gradient-to-r from-[#0066ff] to-[#00a8ff] hover:from-[#0052cc] hover:to-[#0090e0] text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-300 shadow-lg shadow-[#0066ff]/25 hover:shadow-[#0066ff]/40 active:scale-[0.98] flex items-center justify-center gap-2 group"
                      >
                        <ScanLine className="w-5 h-5 group-hover:animate-spin" />
                        Initiate Deep Scan
                      </motion.button>
                    )}
                  </div>

                  {/* ===== RIGHT COLUMN ===== */}
                  <div className="lg:w-3/5 flex-1 min-h-0">
                    {/* Idle placeholder */}
                    {!result && !isScanning && (
                      <div className="h-full min-h-[300px] flex flex-col items-center justify-center rounded-2xl border border-dashed border-[rgba(0,102,255,0.12)] bg-[rgba(0,102,255,0.02)] p-8 text-center">
                        <ScanLine className="w-12 h-12 text-[#8899b8]/40 mb-4" />
                        <p className="text-[#8899b8] font-semibold">Awaiting Analysis</p>
                        <p className="text-xs text-[#8899b8]/60 mt-1 max-w-xs">
                          Upload a receipt and click &quot;Initiate Deep Scan&quot; to see forensic results here.
                        </p>
                      </div>
                    )}

                    {/* Scanning placeholder */}
                    {isScanning && !result && (
                      <div className="h-full min-h-[300px] flex flex-col items-center justify-center rounded-2xl border border-[rgba(0,212,255,0.12)] bg-[rgba(0,212,255,0.02)] p-8 text-center">
                        <FileSearch className="w-12 h-12 text-[#00d4ff] mb-4 animate-pulse" />
                        <p className="text-[#00d4ff] font-mono text-xs font-bold tracking-[0.2em] uppercase animate-pulse">
                          Analyzing Receipt
                        </p>
                        <div className="w-48 h-1 bg-[rgba(0,102,255,0.15)] rounded-full overflow-hidden mt-4">
                          <motion.div
                            className="h-full bg-gradient-to-r from-[#0066ff] to-[#00d4ff] rounded-full"
                            style={{ width: `${Math.min(scanProgress, 100)}%` }}
                            transition={{ duration: 0.3 }}
                          />
                        </div>
                        <p className="text-[#8899b8] text-[10px] mt-2 font-mono">{Math.min(Math.round(scanProgress), 100)}%</p>
                      </div>
                    )}

                    {/* Result Dashboard */}
                    {result && (
                      <div className="space-y-4">
                        <VerdictBanner
                          result={result}
                          forgedFieldCount={analysisResult?.forged_fields?.length || 0}
                        />
                        <MetricsGrid analysisResult={analysisResult} refExists={refExists} />
                        <TabBar tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />

                        <div className="min-h-[250px]">
                          <AnimatePresence mode="wait">
                            <motion.div
                              key={activeTab}
                              initial={{ opacity: 0, y: 5 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -5 }}
                              transition={{ duration: 0.15 }}
                            >
                              {activeTab === 'ela' && (
                                <ElaTab
                                  analysisResult={analysisResult}
                                  result={result}
                                  refExists={refExists}
                                  referenceNumber={referenceNumber}
                                />
                              )}
                              {activeTab === 'typography' && (
                                <TypographyTab analysisResult={analysisResult} />
                              )}
                              {activeTab === 'reference' && (
                                <ReferenceTab
                                  referenceNumber={referenceNumber}
                                  refExists={refExists}
                                  result={result}
                                  confirmed={confirmed}
                                  onOpenModal={() => setShowModal(true)}
                                />
                              )}
                            </motion.div>
                          </AnimatePresence>
                        </div>

                        <button
                          onClick={handleReset}
                          className="w-full flex items-center justify-center gap-2 text-sm font-semibold text-[#8899b8] hover:text-[#f0f6ff] bg-[rgba(0,102,255,0.05)] hover:bg-[rgba(0,102,255,0.1)] border border-[rgba(0,102,255,0.1)] hover:border-[rgba(0,102,255,0.25)] rounded-xl py-2.5 transition-all duration-200"
                        >
                          <ChevronRight className="w-4 h-4 rotate-180" />
                          Scan another receipt
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="flex items-center justify-center gap-6 mt-6">
          <div className="flex items-center gap-2 text-[#8899b8]/60">
            <Fingerprint className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase tracking-wider">Secured with Firestore</span>
          </div>
        </div>
      </motion.div>

      <AnimatePresence>
        <ConfirmModal
          showModal={showModal}
          referenceNumber={referenceNumber}
          refExists={refExists}
          onConfirm={handleConfirm}
          onClose={() => setShowModal(false)}
          onReferenceChange={setReferenceNumber}
        />
      </AnimatePresence>
    </main>
  );
}
