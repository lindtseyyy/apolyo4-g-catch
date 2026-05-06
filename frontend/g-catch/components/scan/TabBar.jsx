export default function TabBar({ tabs, activeTab, onTabChange }) {
  return (
    <div className="flex border-b border-[rgba(0,102,255,0.12)]">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold tracking-wider uppercase transition-all duration-200 border-b-2 -mb-px ${
            activeTab === tab.id
              ? 'text-[#0066ff] border-[#0066ff]'
              : 'text-[#8899b8] border-transparent hover:text-[#c8d4e8]'
          }`}
        >
          <tab.icon className="w-3.5 h-3.5" />
          {tab.label}
        </button>
      ))}
    </div>
  );
}
