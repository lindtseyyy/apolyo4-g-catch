'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, FileSearch, ShieldCheck, AlertTriangle, ScanLine, Fingerprint, Cpu, ChevronRight, Hash } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { saveScan, checkReferenceExists } from '@/lib/dbService';

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
  { id: 'reference', label: 'Reference', icon: Hash },
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

  const handleOpenModal = () => {
    setShowModal(true);
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

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setImage(imageUrl);
      setImageFile(file);
      setResult(null);
      setAnalysisResult(null);
      setScanError(null);
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

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 pt-28 pb-12">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10 max-w-lg"
      >
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
              /* ---- Upload Zone ---- */
              <motion.div
                key="upload"
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
                    { icon: ScanLine, label: 'Ref No. Check', value: 'Prevent reuse' },
                  ].map((item, i) => (
                    <div key={i} className="bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl p-3 text-center">
                      <item.icon className="w-4 h-4 text-[#0066ff] mx-auto mb-1.5" />
                      <p className="text-[10px] text-[#8899b8] uppercase tracking-wider">{item.label}</p>
                      <p className="text-xs font-bold text-[#c8d4e8]">{item.value}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : (
              /* ---- Two-Column Layout ---- */
              <motion.div
                key="results"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex flex-col lg:flex-row gap-6">
                  {/* ===== LEFT COLUMN: Image + Controls ===== */}
                  <div className="lg:w-2/5 flex-shrink-0 space-y-5">
                    <div className="relative rounded-xl overflow-hidden bg-black border border-[rgba(0,102,255,0.15)]">
                      <img
                        src={image}
                        alt="Uploaded Receipt"
                        className={`w-full h-auto max-h-[400px] lg:max-h-[500px] object-contain ${isScanning ? 'opacity-40 blur-[2px]' : ''} transition-all duration-500`}
                      />

                      {/* Laser Scan Line */}
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

                    {/* Error Display */}
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

                    {/* Initiate Deep Scan Button */}
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

                  {/* ===== RIGHT COLUMN: Results / Placeholder ===== */}
                  <div className="lg:w-3/5 flex-1 min-h-0">
                    {!result && !isScanning && (
                      <div className="h-full min-h-[300px] flex flex-col items-center justify-center rounded-2xl border border-dashed border-[rgba(0,102,255,0.12)] bg-[rgba(0,102,255,0.02)] p-8 text-center">
                        <ScanLine className="w-12 h-12 text-[#8899b8]/40 mb-4" />
                        <p className="text-[#8899b8] font-semibold">Awaiting Analysis</p>
                        <p className="text-xs text-[#8899b8]/60 mt-1 max-w-xs">
                          Upload a receipt and click &quot;Initiate Deep Scan&quot; to see forensic results here.
                        </p>
                      </div>
                    )}

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

                    {/* ===== Result Dashboard ===== */}
                    {result && (
                      <div className="space-y-4">
                        {/* Verdict Banner */}
                        <motion.div
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`p-5 rounded-2xl border ${
                            result === 'authentic'
                              ? 'bg-[rgba(0,200,83,0.06)] border-[rgba(0,200,83,0.2)]'
                              : 'bg-[rgba(255,61,113,0.06)] border-[rgba(255,61,113,0.2)]'
                          }`}
                        >
                          <div className="flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                              result === 'authentic'
                                ? 'bg-[rgba(0,200,83,0.15)]'
                                : 'bg-[rgba(255,61,113,0.15)]'
                            }`}>
                              {result === 'authentic' ? (
                                <ShieldCheck className="w-6 h-6 text-[#00c853]" />
                              ) : (
                                <AlertTriangle className="w-6 h-6 text-[#ff3d71]" />
                              )}
                            </div>
                            <div>
                              <h3 className={`text-xl font-bold ${
                                result === 'authentic' ? 'text-[#00c853]' : 'text-[#ff3d71]'
                              }`}>
                                {result === 'authentic' ? 'Verified Authentic' : 'FORGERY DETECTED'}
                              </h3>
                              <p className="text-xs text-[#8899b8] uppercase tracking-wider">
                                {result === 'authentic'
                                  ? 'All forensic checks passed'
                                  : `${analysisResult?.forged_fields?.length || 0} field(s) flagged`}
                              </p>
                            </div>
                          </div>
                        </motion.div>

                        {/* 2×2 Metrics Grid */}
                        {analysisResult && (
                          <div className="grid grid-cols-2 gap-3">
                            <MetricCard
                              label="ELA Noise Score"
                              value={`${analysisResult.ela_noise_score?.toFixed(1)}/100`}
                              status={analysisResult.ela_noise_score < 50 ? 'good' : 'bad'}
                            />
                            <MetricCard
                              label="AI Generation"
                              value={analysisResult.ela_is_ai_generated ? 'Suspected' : 'Not Detected'}
                              status={analysisResult.ela_is_ai_generated ? 'bad' : 'good'}
                            />
                            {(() => {
                              const totalFields = Object.keys(analysisResult.fields || {}).length;
                              const forgedCount = analysisResult.forged_fields?.length || 0;
                              return (
                                <MetricCard
                                  label="Fields Verified"
                                  value={`${totalFields - forgedCount}/${totalFields} passed`}
                                  status={forgedCount === 0 ? 'good' : 'bad'}
                                />
                              );
                            })()}
                            <MetricCard
                              label="Analysis Time"
                              value={`${(analysisResult.duration_ms / 1000).toFixed(1)}s`}
                              status="good"
                            />
                          </div>
                        )}

                        {/* Tab Bar */}
                        <div className="flex border-b border-[rgba(0,102,255,0.12)]">
                          {TABS.map((tab) => (
                            <button
                              key={tab.id}
                              onClick={() => setActiveTab(tab.id)}
                              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold tracking-wider uppercase transition-all duration-200 border-b-2 -mb-px ${
                                activeTab === tab.id
                                  ? 'text-[#0066ff] border-[#0066ff]'
                                  : 'text-[#8899b8] border-transparent hover:text-[#c8d4e8]'
                              }`}
                            >
                              <tab.icon className="w-3.5 h-3.5" />
                              {tab.label}
                            </button>
                          ))}
                        </div>

                        {/* Tab Content */}
                        <div className="min-h-[250px]">
                          <AnimatePresence mode="wait">
                            <motion.div
                              key={activeTab}
                              initial={{ opacity: 0, y: 5 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -5 }}
                              transition={{ duration: 0.15 }}
                            >
                              {/* ---- ELA Test Tab ---- */}
                              {activeTab === 'ela' && (
                                <div className="space-y-4">
                                  <div className="space-y-2">
                                    <DetailRow
                                      label="ELA Verdict"
                                      value={analysisResult.ela_noise_score < 50 ? 'AUTHENTIC' : 'FORGED'}
                                      status={analysisResult.ela_noise_score < 50 ? 'good' : 'bad'}
                                    />
                                    <DetailRow
                                      label="ELA Noise Score"
                                      value={`${analysisResult.ela_noise_score?.toFixed(1)}/100`}
                                      status={analysisResult.ela_noise_score < 50 ? 'good' : 'bad'}
                                    />
                                    <DetailRow
                                      label="AI Generation"
                                      value={analysisResult.ela_is_ai_generated ? 'Suspected' : 'Not Detected'}
                                      status={analysisResult.ela_is_ai_generated ? 'bad' : 'good'}
                                    />
                                  </div>

                                  <p className="text-sm leading-relaxed text-[#8899b8]">
                                    {result === 'authentic'
                                      ? `All forensic checks passed. ELA noise score: ${analysisResult?.ela_noise_score?.toFixed(1)}/100. No typography or compression anomalies detected.`
                                      : refExists
                                        ? `Reference number ${referenceNumber} was found in the cross-reference database — a strong indicator of forgery or attempted reuse. Additionally, the forensic analysis flagged ${analysisResult?.forged_fields?.length || 0} field(s).`
                                        : analysisResult?.forged_fields?.length > 0
                                          ? `Forensic analysis flagged ${analysisResult.forged_fields.length} field(s): ${analysisResult.forged_fields.join(', ')}. ${analysisResult.typography_reasons?.join(' ') || ''}`
                                          : `Error Level Analysis detected pixel compression inconsistencies (noise score: ${analysisResult?.ela_noise_score?.toFixed(1)}/100).`}
                                  </p>

                                  {analysisResult?.proof_image_base64 && (
                                    <div>
                                      <img
                                        src={analysisResult.proof_image_base64}
                                        alt="Forensic proof"
                                        className="w-full rounded-xl border border-[rgba(0,102,255,0.15)]"
                                      />
                                      <p className="text-[10px] text-[#8899b8]/60 mt-1.5 text-center uppercase tracking-wider">
                                        Forensic Proof Image
                                      </p>
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* ---- Typography Tab ---- */}
                              {activeTab === 'typography' && (
                                <div className="space-y-4">
                                  {analysisResult?.fields && Object.entries(analysisResult.fields).length > 0 ? (
                                    <>
                                      <div className="space-y-3">
                                        {Object.entries(analysisResult.fields).map(([fieldName, fieldData]) => {
                                          const isForged = fieldData.verdict === 'forged' || analysisResult.forged_fields?.includes(fieldName);
                                          return (
                                            <div
                                              key={fieldName}
                                              className={`p-4 rounded-xl border ${
                                                isForged
                                                  ? 'bg-[rgba(255,61,113,0.04)] border-[rgba(255,61,113,0.15)]'
                                                  : 'bg-[rgba(0,200,83,0.04)] border-[rgba(0,200,83,0.12)]'
                                              }`}
                                            >
                                              <div className="flex items-center justify-between mb-2">
                                                <p className="text-xs font-mono text-[#c8d4e8] capitalize">{fieldName.replace(/_/g, ' ')}</p>
                                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                                  isForged
                                                    ? 'bg-[rgba(255,61,113,0.15)] text-[#ff3d71]'
                                                    : 'bg-[rgba(0,200,83,0.15)] text-[#00c853]'
                                                }`}>
                                                  {isForged ? 'FORGED' : 'AUTHENTIC'}
                                                </span>
                                              </div>
                                              {fieldData.text && (
                                                <p className="text-sm text-[#f0f6ff] font-mono mb-3">&ldquo;{fieldData.text}&rdquo;</p>
                                              )}
                                              {fieldData.score !== undefined && fieldData.score !== null && (
                                                <DetailRow
                                                  label="Fraud Score"
                                                  value={fieldData.score.toFixed(2)}
                                                  status={fieldData.score < 0.5 ? 'good' : 'bad'}
                                                />
                                              )}
                                              {fieldData.reasons && fieldData.reasons.length > 0 && (
                                                <div className="mt-3 pt-3 border-t border-[rgba(0,102,255,0.08)]">
                                                  <ul className="space-y-1">
                                                    {fieldData.reasons.map((reason, i) => (
                                                      <li key={i} className="text-xs text-[#ff3d71] flex items-start gap-1.5">
                                                        <span className="w-1 h-1 rounded-full bg-[#ff3d71] mt-1.5 flex-shrink-0" />
                                                        {reason}
                                                      </li>
                                                    ))}
                                                  </ul>
                                                </div>
                                              )}
                                            </div>
                                          );
                                        })}
                                      </div>

                                      {analysisResult.typography_reasons?.length > 0 && (
                                        <div className="p-4 bg-[rgba(255,61,113,0.04)] border border-[rgba(255,61,113,0.15)] rounded-xl">
                                          <p className="text-xs font-semibold text-[#ff3d71] uppercase tracking-wider mb-2">Global Anomalies</p>
                                          <ul className="space-y-1">
                                            {analysisResult.typography_reasons.map((reason, i) => (
                                              <li key={i} className="text-xs text-[#8899b8] flex items-start gap-1.5">
                                                <span className="w-1 h-1 rounded-full bg-[#ff3d71] mt-1.5 flex-shrink-0" />
                                                {reason}
                                              </li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                    </>
                                  ) : (
                                    <p className="text-sm text-[#8899b8]">No typography analysis data available.</p>
                                  )}
                                </div>
                              )}

                              {/* ---- Reference Tab ---- */}
                              {activeTab === 'reference' && (
                                <div className="space-y-4">
                                  <div className="p-4 bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl">
                                    <p className="text-[10px] text-[#8899b8] uppercase tracking-wider mb-1">Extracted Reference Number</p>
                                    <p className="text-lg font-mono font-bold text-[#f0f6ff]">{referenceNumber}</p>
                                  </div>

                                  {refExists !== null && (
                                    <motion.div
                                      initial={{ opacity: 0, y: -5 }}
                                      animate={{ opacity: 1, y: 0 }}
                                      className={`p-4 rounded-xl flex items-start gap-3 ${
                                        refExists
                                          ? 'bg-[rgba(255,180,0,0.08)] border border-[rgba(255,180,0,0.2)]'
                                          : 'bg-[rgba(0,200,83,0.08)] border border-[rgba(0,200,83,0.2)]'
                                      }`}
                                    >
                                      {refExists ? (
                                        <AlertTriangle className="w-5 h-5 text-[#ffb800] flex-shrink-0 mt-0.5" />
                                      ) : (
                                        <ShieldCheck className="w-5 h-5 text-[#00c853] flex-shrink-0 mt-0.5" />
                                      )}
                                      <div>
                                        <p className={`text-sm font-semibold ${refExists ? 'text-[#ffb800]' : 'text-[#00c853]'}`}>
                                          {refExists ? 'Already Registered' : 'New Reference'}
                                        </p>
                                        <p className="text-xs text-[#8899b8] mt-0.5">
                                          {refExists
                                            ? 'This reference number has been previously registered in the cross-reference database.'
                                            : 'This reference number has not been seen before.'}
                                        </p>
                                      </div>
                                    </motion.div>
                                  )}

                                  {result === 'authentic' && !confirmed && (
                                    <motion.button
                                      initial={{ opacity: 0, y: 10 }}
                                      animate={{ opacity: 1, y: 0 }}
                                      onClick={handleOpenModal}
                                      className="w-full bg-[rgba(0,102,255,0.08)] hover:bg-[rgba(0,102,255,0.15)] border border-[rgba(0,102,255,0.2)] text-[#0066ff] font-semibold py-3 px-4 rounded-xl transition-all duration-200 text-sm flex items-center justify-center gap-2"
                                    >
                                      <Fingerprint className="w-4 h-4" />
                                      Save Reference No. for Cross-Checking
                                    </motion.button>
                                  )}

                                  {result === 'authentic' && confirmed && (
                                    <motion.div
                                      initial={{ opacity: 0, y: 10 }}
                                      animate={{ opacity: 1, y: 0 }}
                                      className="p-4 bg-[rgba(0,200,83,0.08)] border border-[rgba(0,200,83,0.2)] rounded-xl flex items-center gap-3"
                                    >
                                      <ShieldCheck className="w-5 h-5 text-[#00c853] flex-shrink-0" />
                                      <div>
                                        <p className="text-sm text-[#00c853] font-semibold">Reference saved</p>
                                        <p className="text-xs text-[#8899b8]">This receipt has been recorded for cross-referencing.</p>
                                      </div>
                                    </motion.div>
                                  )}
                                </div>
                              )}
                            </motion.div>
                          </AnimatePresence>
                        </div>

                        {/* Scan Another Receipt */}
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

        {/* Bottom trust indicators */}
        <div className="flex items-center justify-center gap-6 mt-6">
          <div className="flex items-center gap-2 text-[#8899b8]/60">
            <Fingerprint className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase tracking-wider">Secured with Firestore</span>
          </div>
        </div>
      </motion.div>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#030712]/80 backdrop-blur-sm"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              onClick={(e) => e.stopPropagation()}
              className="glass rounded-2xl p-6 md:p-8 w-full max-w-md border border-[rgba(0,102,255,0.15)]"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-[rgba(0,102,255,0.1)] flex items-center justify-center">
                  <Fingerprint className="w-5 h-5 text-[#0066ff]" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#f0f6ff]">Confirm Reference Number</h3>
                  <p className="text-xs text-[#8899b8]">Cross-reference verification</p>
                </div>
              </div>

              <p className="text-sm text-[#8899b8] mb-4 leading-relaxed">
                The system extracted the following reference number from this receipt. Please verify it is correct — this will be stored for future cross-referencing against known fraudulent receipts.
              </p>

              {/* Reference check result */}
              {refExists !== null && (
                <motion.div
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mb-4 p-3 rounded-xl flex items-start gap-3 text-sm ${
                    refExists
                      ? 'bg-[rgba(255,180,0,0.08)] border border-[rgba(255,180,0,0.2)]'
                      : 'bg-[rgba(0,200,83,0.08)] border border-[rgba(0,200,83,0.2)]'
                  }`}
                >
                  {refExists ? (
                    <AlertTriangle className="w-5 h-5 text-[#ffb800] flex-shrink-0 mt-0.5" />
                  ) : (
                    <ShieldCheck className="w-5 h-5 text-[#00c853] flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className={`font-semibold ${refExists ? 'text-[#ffb800]' : 'text-[#00c853]'}`}>
                      {refExists ? 'Reference already registered' : 'New reference number'}
                    </p>
                    <p className="text-xs text-[#8899b8] mt-0.5">
                      {refExists
                        ? 'This reference number has been previously used. It may indicate a duplicate or reused receipt.'
                        : 'This reference number has not been seen before. It appears to be a unique receipt.'}
                    </p>
                  </div>
                </motion.div>
              )}

              <div className="relative mb-5">
                <Hash className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8899b8]" />
                <input
                  type="text"
                  value={referenceNumber}
                  onChange={(e) => setReferenceNumber(e.target.value)}
                  className="w-full bg-[rgba(0,102,255,0.06)] border border-[rgba(0,102,255,0.2)] hover:border-[rgba(0,102,255,0.35)] rounded-xl pl-10 pr-4 py-3 text-[#f0f6ff] text-sm font-mono transition-all focus:outline-none focus:border-[#0066ff] focus:ring-1 focus:ring-[#0066ff]/30"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleConfirm}
                  className="flex-1 bg-gradient-to-r from-[#0066ff] to-[#00a8ff] hover:from-[#0052cc] hover:to-[#0090e0] text-white font-semibold py-2.5 px-4 rounded-xl transition-all duration-200 text-sm"
                >
                  Confirm & Save
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-[rgba(255,61,113,0.08)] hover:bg-[rgba(255,61,113,0.15)] border border-[rgba(255,61,113,0.15)] text-[#ff3d71] font-medium py-2.5 px-4 rounded-xl transition-all duration-200 text-sm"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
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

function MetricCard({ label, value, status }) {
  return (
    <div className="bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl p-4">
      <p className="text-[10px] text-[#8899b8] uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-sm font-bold ${status === 'good' ? 'text-[#00c853]' : 'text-[#ff3d71]'}`}>
        {value}
      </p>
    </div>
  );
}
