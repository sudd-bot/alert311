'use client';

import { useState } from 'react';

interface ReportsPanelProps {
  address: string;
  onCreateNew: () => void;
}

// Mock recent alerts for demo
// TODO: Replace with real data from /reports API endpoint when authenticated
// Real reports require SF 311 OAuth + cron job polling (see backend/app/routes/cron.py)
const MOCK_RECENT_ALERTS = [
  {
    id: 1,
    type: 'Sidewalk Parking',
    status: 'Open',
    date: '2 days ago',
    description: 'Vehicle blocking sidewalk near entrance',
    icon: '🚗',
  },
  {
    id: 2,
    type: 'Illegal Dumping',
    status: 'Closed',
    date: '1 week ago',
    description: 'Mattress and furniture dumped on corner',
    icon: '🗑️',
  },
  {
    id: 3,
    type: 'Graffiti',
    status: 'Open',
    date: '2 weeks ago',
    description: 'Graffiti on building wall facing street',
    icon: '🎨',
  },
];

export default function ReportsPanel({ address, onCreateNew }: ReportsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <>
      {/* Mobile: Bottom Sheet */}
      <div className="fixed inset-x-0 bottom-0 z-50 lg:hidden safe-bottom animate-slideUp">
        <div 
          className={`glass-light rounded-t-3xl transition-all duration-300 ease-out ${
            isExpanded ? 'max-h-[80vh]' : 'max-h-[280px]'
          }`}
        >
          {/* Drag handle - Better touch target */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full py-4 flex justify-center"
            aria-label={isExpanded ? 'Collapse panel' : 'Expand panel'}
          >
            <div className="h-1.5 w-12 rounded-full bg-gray-300" />
          </button>

          <div className={`px-5 pb-5 overflow-y-auto scrollbar-hide ${isExpanded ? 'max-h-[calc(80vh-60px)]' : 'max-h-[220px]'}`}>
            {/* Header - Better spacing */}
            <div className="mb-5">
              <h2 className="font-display text-xl font-bold text-gray-900">
                Nearby Reports
              </h2>
              <p className="text-sm text-gray-500 truncate mt-1">
                {address}
              </p>
            </div>

            {/* Reports list - Better card spacing */}
            <div className="space-y-3">
              {MOCK_RECENT_ALERTS.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-start gap-3 rounded-xl bg-gray-100/80 p-4"
                >
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-white text-xl shadow-sm">
                    {alert.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm text-gray-900">{alert.type}</span>
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                          alert.status === 'Open'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {alert.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 line-clamp-1">{alert.description}</p>
                  </div>
                  <span className="shrink-0 text-[10px] text-gray-400 font-medium mt-0.5">{alert.date}</span>
                </div>
              ))}
            </div>

            {/* CTA Button - More space above */}
            <button
              onClick={onCreateNew}
              className="mt-5 w-full h-14 rounded-xl bg-primary font-display font-semibold text-base text-primary-foreground shadow-lg shadow-primary/25 active:scale-[0.98] transition-transform"
            >
              Create New Alert
            </button>
          </div>
        </div>
      </div>

      {/* Desktop: Side Panel - Better spacing throughout */}
      <div className="fixed right-5 top-24 bottom-5 z-40 hidden lg:block w-96 animate-slideDown">
        <div className="glass-light h-full rounded-2xl overflow-hidden flex flex-col ring-1 ring-black/5 shadow-xl">
          {/* Header - More padding */}
          <div className="p-6 border-b border-gray-100">
            <h2 className="font-display text-xl font-bold text-gray-900">
              Nearby Reports
            </h2>
            <p className="text-sm text-gray-500 truncate mt-1.5">
              {address}
            </p>
          </div>

          {/* Reports list - Better card spacing */}
          <div className="flex-1 overflow-y-auto p-5 space-y-3 scrollbar-hide">
            {MOCK_RECENT_ALERTS.map((alert) => (
              <div
                key={alert.id}
                className="rounded-xl bg-gray-50 p-4 hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex items-start gap-3.5">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-xl shadow-sm ring-1 ring-gray-100">
                    {alert.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="font-semibold text-gray-900">{alert.type}</span>
                      <span className="shrink-0 text-xs text-gray-400">{alert.date}</span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{alert.description}</p>
                    <span
                      className={`inline-block rounded-full px-2.5 py-1 text-xs font-bold ${
                        alert.status === 'Open'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-emerald-100 text-emerald-700'
                      }`}
                    >
                      {alert.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* CTA Button - Better padding */}
          <div className="p-5 border-t border-gray-100">
            <button
              onClick={onCreateNew}
              className="w-full h-14 rounded-xl bg-primary font-display font-semibold text-base text-primary-foreground shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 active:scale-[0.98] transition-all"
            >
              Create New Alert
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
