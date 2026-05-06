'use client';

import DetailRow from './DetailRow';

export default function ElaTab({ analysisResult, result, refExists, referenceNumber }) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <DetailRow
          label="Result"
          value={analysisResult.ela_is_ai_generated ? 'Forensics Artifacts Detected' : 'No Forensics Artifacts Detected'}
          status={analysisResult.ela_is_ai_generated ? 'bad' : 'good'}
        />
        <DetailRow
          label="Confidence"
          value={`${analysisResult.ela_integrity_score?.toFixed(1)}%`}
          status={analysisResult.ela_integrity_score >= 75 ? 'good' : 'bad'}
        />
      </div>

      {analysisResult?.proof_image_base64 && (
        <div className="p-4 bg-[rgba(0,102,255,0.03)] rounded-xl border border-[rgba(0,102,255,0.08)] space-y-3">
          <p className="text-sm font-semibold text-[#c8d4e8]">Error Level Analysis Overlay</p>
          <div className="flex gap-4 items-center">
            <img
              src={analysisResult.proof_image_base64}
              alt="Forensic proof"
              className="w-[220px] rounded-xl border border-[rgba(0,102,255,0.15)]"
            />
            <p className="text-xs text-[#8899b8]/70 leading-relaxed">
              Red highlights reveal unnatural noise patterns. Concentrated red on blank areas strongly suggests the receipt was AI-generated.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
