'use client';

import { motion } from 'framer-motion';

export default function PageHeader() {
  return (
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
  );
}
