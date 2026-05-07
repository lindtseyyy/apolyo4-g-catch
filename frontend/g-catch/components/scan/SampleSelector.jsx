'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FlaskConical, CheckCircle2, AlertTriangle, Bot, ChevronDown, ImageIcon, Layers } from 'lucide-react';

const CATEGORY_META = {
  authentic: { label: 'Authentic Receipts', icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-400/8', border: 'border-green-400/20' },
  edited: { label: 'Edited / Forged', icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-400/8', border: 'border-yellow-400/20' },
  'ai-generated': { label: 'AI-Generated', icon: Bot, color: 'text-purple-400', bg: 'bg-purple-400/8', border: 'border-purple-400/20' },
};

async function urlToFile(url, filename) {
  const res = await fetch(url);
  const blob = await res.blob();
  return new File([blob], filename, { type: blob.type });
}

export default function SampleSelector({ onSampleSelect }) {
  const [samples, setSamples] = useState(null);
  const [openCategory, setOpenCategory] = useState(null);
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/samples/manifest.json')
      .then((r) => r.json())
      .then(setSamples)
      .catch(() => setError('Failed to load samples'));
  }, []);

  if (error || (!samples && !error)) return null;

  const grouped = {};
  for (const s of samples) {
    (grouped[s.category] ||= []).push(s);
  }

  const renderSampleButton = (sample) => {
    const isSampleLoading = loading === sample.path;
    return (
      <button
        key={sample.path}
        disabled={!!loading}
        onClick={async () => {
          setLoading(sample.path);
          try {
            const filename = sample.path.split('/').pop();
            const file = await urlToFile(sample.path, filename);
            onSampleSelect(file);
          } catch {
            // ignore
          } finally {
            setLoading(null);
          }
        }}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.08)] hover:border-[rgba(0,102,255,0.25)] hover:bg-[rgba(0,102,255,0.08)] transition-all text-left group"
      >
        <ImageIcon className="w-3.5 h-3.5 text-[#8899b8]/60 group-hover:text-[#0066ff] flex-shrink-0" />
        <span className="text-xs text-[#8899b8] group-hover:text-[#c8d4e8] truncate leading-tight">
          {isSampleLoading ? 'Loading...' : sample.label}
        </span>
      </button>
    );
  };

  const renderItems = (items) => {
    const hasSubcategories = items.some((s) => s.subcategory);
    if (!hasSubcategories) {
      return (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-3 max-h-48 overflow-y-auto">
          {items.map(renderSampleButton)}
        </div>
      );
    }

    const bySub = {};
    for (const s of items) {
      (bySub[s.subcategory || 'Other'] ||= []).push(s);
    }

    return (
      <div className="max-h-72 overflow-y-auto p-3 space-y-3">
        {Object.entries(bySub).map(([sub, subItems]) => (
          <div key={sub}>
            <div className="flex items-center gap-1.5 mb-1.5">
              <Layers className="w-3 h-3 text-[#8899b8]/50" />
              <span className="text-[10px] text-[#8899b8]/60 font-medium uppercase tracking-wider">{sub}</span>
              <span className="text-[10px] text-[#8899b8]/40">({subItems.length})</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {subItems.map(renderSampleButton)}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <FlaskConical className="w-4 h-4 text-[#8899b8]" />
        <p className="text-xs text-[#8899b8] font-semibold uppercase tracking-wider">
          Or pick a sample image
        </p>
      </div>

      {Object.entries(CATEGORY_META).map(([key, meta]) => {
        const items = grouped[key];
        if (!items?.length) return null;

        const Icon = meta.icon;
        const isOpen = openCategory === key;

        return (
          <div key={key} className={`rounded-xl border ${meta.border} ${meta.bg} overflow-hidden`}>
            <button
              onClick={() => setOpenCategory(isOpen ? null : key)}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-white/[0.02] transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${meta.color}`} />
                <span className="text-sm text-[#c8d4e8] font-medium">{meta.label}</span>
                <span className="text-[10px] text-[#8899b8]/60">({items.length})</span>
              </div>
              <ChevronDown
                className={`w-4 h-4 text-[#8899b8] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>

            {isOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="border-t border-white/[0.04]"
              >
                {renderItems(items)}
              </motion.div>
            )}
          </div>
        );
      })}
    </div>
  );
}
