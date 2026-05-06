import MetricCard from './MetricCard';

export default function MetricsGrid({ analysisResult }) {
  if (!analysisResult) return null;

  const totalFields = Object.keys(analysisResult.fields || {}).length;
  const forgedCount = analysisResult.forged_fields?.length || 0;

  return (
    <div className="grid grid-cols-2 gap-3">
      <MetricCard
        label="ELA Noise Score"
        value={`${analysisResult.ela_noise_score?.toFixed(1)}/100`}
        status={analysisResult.ela_noise_score < 50 ? 'good' : 'bad'}
      />
      <MetricCard
        label="AI Generation"
        value={analysisResult.ela_is_ai_generated ? 'Suspected' : 'Not Detected'}
        status={analysisResult.ela_is_ai_generated ? 'bad' : 'good'}
      />
      <MetricCard
        label="Fields Verified"
        value={`${totalFields - forgedCount}/${totalFields} passed`}
        status={forgedCount === 0 ? 'good' : 'bad'}
      />
      <MetricCard
        label="Analysis Time"
        value={`${(analysisResult.duration_ms / 1000).toFixed(1)}s`}
        status="good"
      />
    </div>
  );
}
