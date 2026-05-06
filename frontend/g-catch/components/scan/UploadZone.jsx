'use client';

import { motion } from 'framer-motion';
import { UploadCloud, Fingerprint, Cpu, ScanLine } from 'lucide-react';

const STATS = [
  { icon: Fingerprint, label: 'Pixel Analysis', value: 'ELA' },
  { icon: Cpu, label: 'OCR Engine', value: 'Tesseract' },
  { icon: ScanLine, label: 'Ref No. Check', value: 'Prevent reuse' },
];

export default function UploadZone({ onImageUpload }) {
  return (
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
          onChange={onImageUpload}
        />
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0066ff]/15 to-[#00a8ff]/10 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
          <UploadCloud className="w-8 h-8 text-[#0066ff] group-hover:text-[#00d4ff] transition-colors" />
        </div>
        <p className="text-sm text-[#c8d4e8] font-semibold mb-1">Drop receipt image here</p>
        <p className="text-xs text-[#8899b8]">or click to browse</p>
        <p className="text-[10px] text-[#8899b8]/60 mt-3">Supports JPG, PNG, WEBP</p>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-5">
        {STATS.map((item, i) => (
          <div key={i} className="bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl p-3 text-center">
            <item.icon className="w-4 h-4 text-[#0066ff] mx-auto mb-1.5" />
            <p className="text-[10px] text-[#8899b8] uppercase tracking-wider">{item.label}</p>
            <p className="text-xs font-bold text-[#c8d4e8]">{item.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
