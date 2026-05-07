'use client';

import { motion } from 'framer-motion';
import { FileSearch } from 'lucide-react';

export default function ImagePreview({ image, isScanning, scanProgress }) {
  return (
    <div className="relative rounded-xl overflow-hidden bg-black border border-[rgba(0,102,255,0.15)]">
      <img
        src={image}
        alt="Uploaded Receipt"
        className={`w-full h-auto max-h-[400px] lg:max-h-[500px] object-contain ${isScanning ? 'opacity-40 blur-[2px]' : ''} transition-all duration-500`}
      />

      {isScanning && (
        <>
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

          <div className="lg:hidden absolute inset-0 flex flex-col items-center justify-center bg-black/60">
            <FileSearch className="w-10 h-10 text-[#00d4ff] mb-3 animate-pulse" />
            <p className="text-[#00d4ff] font-mono text-xs font-bold tracking-[0.2em] uppercase animate-pulse">
              Analyzing Receipt
            </p>
            <div className="w-40 h-1.5 bg-white/20 rounded-full overflow-hidden mt-3">
              <motion.div
                className="h-full bg-gradient-to-r from-[#0066ff] to-[#00d4ff]"
                style={{ width: `${Math.min(scanProgress || 0, 100)}%` }}
              />
            </div>
            <p className="text-[#8899b8] text-[10px] mt-2 font-mono">{Math.min(Math.round(scanProgress), 100)}%</p>
          </div>
        </>
      )}
    </div>
  );
}
