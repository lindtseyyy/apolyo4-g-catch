'use client';

import { motion } from 'framer-motion';
import { ShieldCheck, AlertTriangle, Fingerprint } from 'lucide-react';

export default function ReferenceTab({ referenceNumber, refExists, result, confirmed, onOpenModal }) {
  return (
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
                ? 'This reference number has already been registered. This may indicate a Replay Attack — where a legitimate receipt is reused to fraudulently claim the same transaction multiple times.'
                : 'This reference number has not been seen before.'}
            </p>
          </div>
        </motion.div>
      )}

      {result === 'authentic' && !confirmed && (
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={onOpenModal}
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
  );
}
