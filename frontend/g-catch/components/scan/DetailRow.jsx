export default function DetailRow({ label, value, status }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-[#8899b8]">{label}</span>
      <span className={`font-semibold ${status === 'good' ? 'text-[#00c853]' : 'text-[#ff3d71]'}`}>
        {value}
      </span>
    </div>
  );
}
