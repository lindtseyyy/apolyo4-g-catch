export default function TabBar({ tabs, activeTab, onTabChange }) {
  return (
    <>
      {/* Mobile dropdown */}
      <select
        value={activeTab}
        onChange={(e) => onTabChange(e.target.value)}
        className="lg:hidden w-full px-4 py-3 text-xs font-semibold tracking-wider uppercase bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.15)] rounded-xl text-[#0066ff] focus:outline-none focus:border-[#0066ff] transition-all duration-200 appearance-none"
        style={{
          colorScheme: 'dark',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='none' stroke='%230066ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m2 4 4 4 4-4'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 16px center',
          paddingRight: '40px',
        }}
      >
        {tabs.map((tab) => (
          <option key={tab.id} value={tab.id}>
            {tab.label}
          </option>
        ))}
      </select>

      {/* Desktop tabs */}
      <div className="hidden lg:flex border-b border-[rgba(0,102,255,0.12)]">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold tracking-wider uppercase transition-all duration-200 border-b-2 -mb-px ${
                activeTab === tab.id
                  ? 'text-[#0066ff] border-[#0066ff]'
                  : 'text-[#8899b8] border-transparent hover:text-[#c8d4e8]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>
    </>
  );
}
