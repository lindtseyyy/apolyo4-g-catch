'use client';

import DetailRow from './DetailRow';

export default function ElaTab({ analysisResult, result, refExists, referenceNumber }) {
  const isAiGenerated = analysisResult.ela_is_ai_generated;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <DetailRow
          label="Result"
          value={isAiGenerated ? 'Forensics Artifacts Detected' : 'No Forensics Artifacts Detected'}
          status={isAiGenerated ? 'bad' : 'good'}
        />
        <DetailRow
          label={isAiGenerated ? 'Forgery Evidence' : 'Confidence'}
          value={isAiGenerated
            ? `${(100 - analysisResult.ela_integrity_score)?.toFixed(1)}%`
            : `${analysisResult.ela_integrity_score?.toFixed(1)}%`
          }
          status={analysisResult.ela_integrity_score >= 75 ? 'good' : 'bad'}
        />
      </div>

      {analysisResult?.proof_image_base64 && (
        <div className="p-4 bg-[rgba(0,102,255,0.03)] rounded-xl border border-[rgba(0,102,255,0.08)] space-y-3">
          <p className="text-sm font-semibold text-[#c8d4e8]">Error Level Analysis Overlay</p>
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <img
              src={analysisResult.proof_image_base64}
              alt="Forensic proof"
              className="w-full sm:w-[220px] rounded-xl border border-[rgba(0,102,255,0.15)]"
            />
            <div className="space-y-2">
              <p className="text-xs text-[#8899b8] leading-relaxed text-justify">
                Bright areas represent Error Level Variance. In a legitimate receipt, noise should only appear around text edges — bright clusters in flat background areas indicate pixel manipulation.
              </p>
              <p className={`text-xs leading-relaxed font-medium text-justify ${isAiGenerated ? 'text-[#ff3d71]' : 'text-[#00c853]'}`}>
                {isAiGenerated
                  ? "This image displays unnatural noise distribution. We have identified high-frequency artifacts in the flat background areas and card panels. These 'hallucinated' pixels are a signature of Generative AI or manual image tampering, indicating the receipt was likely edited."
                  : 'This image displays standardized noise patterns. High-frequency residuals are localized strictly on the text fields, with a clean, low-noise background. This is mathematically consistent with an original, system-rendered digital receipt.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
