'use client';

import DetailRow from './DetailRow';

export default function TypographyTab({ analysisResult }) {
  const fields = analysisResult?.fields;
  const hasFields = fields && Object.entries(fields).length > 0;

  if (!hasFields) {
    return <p className="text-sm text-[#8899b8]">No typography analysis data available.</p>;
  }

  return (
    <div className="space-y-4">
      {/* Overall typography integrity */}
      {analysisResult.typography_integrity_score !== undefined && (
        <div className="p-4 bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl">
          <div className="flex items-center justify-between">
            <p className="text-xs text-[#8899b8] uppercase tracking-wider">Typography Integrity</p>
            <p className={`text-lg font-bold ${
              analysisResult.typography_integrity_score >= 75 ? 'text-[#00c853]' : 'text-[#ff3d71]'
            }`}>
              {analysisResult.typography_integrity_score.toFixed(1)}%
            </p>
          </div>
          {analysisResult.penalty_summary?.length > 0 && (
            <div className="mt-3 pt-3 border-t border-[rgba(0,102,255,0.08)]">
              <p className="text-[10px] text-[#8899b8] uppercase tracking-wider mb-2">Penalties Applied</p>
              <ul className="space-y-1">
                {analysisResult.penalty_summary.map((penalty, i) => (
                  <li key={i} className="text-xs text-[#ff3d71] flex items-start gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-[#ff3d71] mt-1.5 flex-shrink-0" />
                    {penalty}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="space-y-3">
        {Object.entries(fields).map(([fieldName, fieldData]) => {
          const isForged = fieldData.verdict === 'forged' || analysisResult.forged_fields?.includes(fieldName);
          return (
            <div
              key={fieldName}
              className={`p-4 rounded-xl border ${
                isForged
                  ? 'bg-[rgba(255,61,113,0.04)] border-[rgba(255,61,113,0.15)]'
                  : 'bg-[rgba(0,200,83,0.04)] border-[rgba(0,200,83,0.12)]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-mono text-[#c8d4e8] capitalize">{fieldName.replace(/_/g, ' ')}</p>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  isForged
                    ? 'bg-[rgba(255,61,113,0.15)] text-[#ff3d71]'
                    : 'bg-[rgba(0,200,83,0.15)] text-[#00c853]'
                }`}>
                  {isForged ? 'FORGED' : 'AUTHENTIC'}
                </span>
              </div>
              {fieldData.text && (
                <p className="text-sm text-[#f0f6ff] font-mono mb-3">&ldquo;{fieldData.text}&rdquo;</p>
              )}
              {fieldData.score !== undefined && fieldData.score !== null && (
                <DetailRow
                  label="Fraud Score"
                  value={fieldData.score.toFixed(2)}
                  status={fieldData.score < 0.5 ? 'good' : 'bad'}
                />
              )}
              {fieldData.reasons && fieldData.reasons.length > 0 && (
                <div className="mt-3 pt-3 border-t border-[rgba(0,102,255,0.08)]">
                  <ul className="space-y-1">
                    {fieldData.reasons.map((reason, i) => (
                      <li key={i} className="text-xs text-[#ff3d71] flex items-start gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-[#ff3d71] mt-1.5 flex-shrink-0" />
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {analysisResult.typography_reasons?.length > 0 && (
        <div className="p-4 bg-[rgba(255,61,113,0.04)] border border-[rgba(255,61,113,0.15)] rounded-xl">
          <p className="text-xs font-semibold text-[#ff3d71] uppercase tracking-wider mb-2">Global Anomalies</p>
          <ul className="space-y-1">
            {analysisResult.typography_reasons.map((reason, i) => (
              <li key={i} className="text-xs text-[#8899b8] flex items-start gap-1.5">
                <span className="w-1 h-1 rounded-full bg-[#ff3d71] mt-1.5 flex-shrink-0" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
