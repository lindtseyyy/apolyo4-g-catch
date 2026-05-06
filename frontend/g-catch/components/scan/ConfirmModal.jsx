'use client';

import { motion } from 'framer-motion';
import { Fingerprint, ShieldCheck, AlertTriangle, Hash } from 'lucide-react';

export default function ConfirmModal({
  showModal,
  referenceNumber,
  refExists,
  onConfirm,
  onClose,
  onReferenceChange,
}) {
  return (
    <>
      {showModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#030712]/80 backdrop-blur-sm"
          onClick={onClose}
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
              The system extracted the following reference number from this receipt. Please verify it
              is correct — this will be stored for future cross-referencing against known fraudulent
              receipts.
            </p>

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
                onChange={(e) => onReferenceChange(e.target.value)}
                className="w-full bg-[rgba(0,102,255,0.06)] border border-[rgba(0,102,255,0.2)] hover:border-[rgba(0,102,255,0.35)] rounded-xl pl-10 pr-4 py-3 text-[#f0f6ff] text-sm font-mono transition-all focus:outline-none focus:border-[#0066ff] focus:ring-1 focus:ring-[#0066ff]/30"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={onConfirm}
                className="flex-1 bg-gradient-to-r from-[#0066ff] to-[#00a8ff] hover:from-[#0052cc] hover:to-[#0090e0] text-white font-semibold py-2.5 px-4 rounded-xl transition-all duration-200 text-sm"
              >
                Confirm & Save
              </button>
              <button
                onClick={onClose}
                className="flex-1 bg-[rgba(255,61,113,0.08)] hover:bg-[rgba(255,61,113,0.15)] border border-[rgba(255,61,113,0.15)] text-[#ff3d71] font-medium py-2.5 px-4 rounded-xl transition-all duration-200 text-sm"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </>
  );
}
