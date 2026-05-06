'use client';

import { motion } from 'framer-motion';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

export default function VerdictBanner({ result, forgedFieldCount }) {
  return (
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
            {result === 'authentic' ? 'No Anomalies Detected' : 'FORGERY DETECTED'}
          </h3>
        </div>
      </div>
    </motion.div>
  );
}
