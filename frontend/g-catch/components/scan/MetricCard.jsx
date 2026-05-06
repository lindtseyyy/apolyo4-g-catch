export default function MetricCard({ label, value, status }) {
  return (
    <div className="bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] rounded-xl p-4">
      <p className="text-[10px] text-[#8899b8] uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-sm font-bold ${status === 'good' ? 'text-[#00c853]' : 'text-[#ff3d71]'}`}>
        {value}
      </p>
    </div>
  );
}
