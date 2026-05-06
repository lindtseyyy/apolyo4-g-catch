'use client';

import DetailRow from './DetailRow';

export default function ElaTab({ analysisResult, result, refExists, referenceNumber }) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <DetailRow
          label="ELA Verdict"
          value={analysisResult.ela_noise_score < 50 ? 'AUTHENTIC' : 'FORGED'}
          status={analysisResult.ela_noise_score < 50 ? 'good' : 'bad'}
        />
        <DetailRow
          label="ELA Noise Score"
          value={`${analysisResult.ela_noise_score?.toFixed(1)}/100`}
          status={analysisResult.ela_noise_score < 50 ? 'good' : 'bad'}
        />
        <DetailRow
          label="AI Generation"
          value={analysisResult.ela_is_ai_generated ? 'Suspected' : 'Not Detected'}
          status={analysisResult.ela_is_ai_generated ? 'bad' : 'good'}
        />
      </div>

      <p className="text-sm leading-relaxed text-[#8899b8]">
        {result === 'authentic'
          ? `All forensic checks passed. ELA noise score: ${analysisResult?.ela_noise_score?.toFixed(1)}/100. No typography or compression anomalies detected.`
          : refExists
            ? `Reference number ${referenceNumber} was found in the cross-reference database — a strong indicator of forgery or attempted reuse. Additionally, the forensic analysis flagged ${analysisResult?.forged_fields?.length || 0} field(s).`
            : analysisResult?.forged_fields?.length > 0
              ? `Forensic analysis flagged ${analysisResult.forged_fields.length} field(s): ${analysisResult.forged_fields.join(', ')}. ${analysisResult.typography_reasons?.join(' ') || ''}`
              : `Error Level Analysis detected pixel compression inconsistencies (noise score: ${analysisResult?.ela_noise_score?.toFixed(1)}/100).`}
      </p>

      {analysisResult?.proof_image_base64 && (
        <div>
          <img
            src={analysisResult.proof_image_base64}
            alt="Forensic proof"
            className="w-full rounded-xl border border-[rgba(0,102,255,0.15)]"
          />
          <p className="text-[10px] text-[#8899b8]/60 mt-1.5 text-center uppercase tracking-wider">
            Forensic Proof Image
          </p>
        </div>
      )}
    </div>
  );
}
