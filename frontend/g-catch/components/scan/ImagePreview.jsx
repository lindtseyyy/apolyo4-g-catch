'use client';

import { motion } from 'framer-motion';

export default function ImagePreview({ image, isScanning }) {
  return (
    <div className="relative rounded-xl overflow-hidden bg-black border border-[rgba(0,102,255,0.15)]">
      <img
        src={image}
        alt="Uploaded Receipt"
        className={`w-full h-auto max-h-[400px] lg:max-h-[500px] object-contain ${isScanning ? 'opacity-40 blur-[2px]' : ''} transition-all duration-500`}
      />

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
    </div>
  );
}
