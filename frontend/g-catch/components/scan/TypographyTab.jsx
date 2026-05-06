'use client';

export default function TypographyTab({ analysisResult }) {
  const fields = analysisResult?.fields;
  const hasFields = fields && Object.entries(fields).length > 0;

  if (!hasFields) {
    return <p className="text-sm text-[#8899b8]">No typography analysis data available.</p>;
  }

  const rows = Object.entries(fields).map(([fieldName, fieldData]) => {
    const isForged = fieldData.verdict === 'forged' || analysisResult.forged_fields?.includes(fieldName);
    const isInconclusive = fieldData.verdict === 'INCONCLUSIVE';
    return { fieldName, fieldData, isForged, isInconclusive };
  });

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

      {/* Field Status Table */}
      <div className="rounded-xl border border-[rgba(0,102,255,0.1)] overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[1fr_auto] gap-3 px-4 py-2.5 bg-[rgba(0,102,255,0.06)] border-b border-[rgba(0,102,255,0.08)]">
          <p className="text-[10px] text-[#8899b8] uppercase tracking-wider">Field</p>
          <p className="text-[10px] text-[#8899b8] uppercase tracking-wider text-right">Status</p>
        </div>

        {/* Table rows */}
        {rows.map(({ fieldName, fieldData, isForged, isInconclusive }, i) => (
          <div
            key={fieldName}
            className={`grid grid-cols-[1fr_auto] gap-3 px-4 py-3 items-center ${
              i < rows.length - 1 ? 'border-b border-[rgba(0,102,255,0.06)]' : ''
            }`}
          >
            <p className="text-xs text-[#c8d4e8] capitalize">{fieldName.replace(/_/g, ' ')}</p>
            <span className={`text-[10px] font-semibold px-2.5 py-1 rounded-full ${
              isInconclusive
                ? 'bg-[rgba(255,180,0,0.12)] text-[#ffb800]'
                : isForged
                  ? 'bg-[rgba(255,61,113,0.12)] text-[#ff3d71]'
                  : 'bg-[rgba(0,200,83,0.12)] text-[#00c853]'
            }`}>
              {isInconclusive ? 'Skipped' : isForged ? 'Forged' : 'Unaltered'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
