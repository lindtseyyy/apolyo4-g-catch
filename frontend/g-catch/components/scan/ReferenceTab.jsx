'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, AlertTriangle, Search } from 'lucide-react';

export default function ReferenceTab({ referenceNumber, refExists, result, confirmed, onOpenModal, onReferenceCheck }) {
  const [editedRef, setEditedRef] = useState(referenceNumber);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    setEditedRef(referenceNumber);
  }, [referenceNumber]);

  const cleanedEdited = editedRef.replace(/\s+/g, '');
  const cleanedOriginal = (referenceNumber || '').replace(/\s+/g, '');
  const hasChanged = cleanedEdited !== cleanedOriginal;

  const handleCheck = async () => {
    if (!hasChanged || checking) return;
    setChecking(true);
    try {
      await onReferenceCheck(cleanedEdited);
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="p-4 bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl">
        <p className="text-[10px] text-[#8899b8] uppercase tracking-wider mb-2">Reference Number</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={editedRef}
            onChange={(e) => setEditedRef(e.target.value)}
            className="flex-1 bg-[rgba(0,102,255,0.06)] border border-[rgba(0,102,255,0.15)] rounded-lg px-3 py-2 text-sm font-mono text-[#f0f6ff] focus:outline-none focus:border-[#0066ff] transition-all"
          />
          <button
            onClick={handleCheck}
            disabled={checking}
            className="flex items-center gap-1.5 px-3 py-2 bg-[rgba(0,102,255,0.08)] hover:bg-[rgba(0,102,255,0.15)] border border-[rgba(0,102,255,0.2)] text-[#0066ff] rounded-lg text-xs font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
          >
            <Search className="w-3.5 h-3.5" />
            {checking ? 'Checking…' : 'Re-check'}
          </button>
        </div>
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

      {result === 'authentic' && !confirmed && !refExists && (
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={onOpenModal}
          className="w-full bg-[rgba(0,102,255,0.08)] hover:bg-[rgba(0,102,255,0.15)] border border-[rgba(0,102,255,0.2)] text-[#0066ff] font-semibold py-3 px-4 rounded-xl transition-all duration-200 text-sm"
        >
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
