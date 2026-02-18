'use client';

import { useState, useEffect, useCallback } from 'react';
import { formatDistance, formatDate, formatAddress } from '@/lib/format';

interface ReportsPanelProps {
  address: string;
  lat: number;
  lng: number;
  onCreateNew: () => void;
  /** Called with full report list once loaded (used to render map markers) */
  onReportsLoaded?: (reports: Report[]) => void;
}

export interface Report {
  id: string;
  public_id?: string | null;
  type: string;
  date: string;
  raw_date?: string | null;
  status: 'open' | 'closed';
  address: string;
  latitude: number;
  longitude: number;
  photo_url?: string | null;
  distance_meters?: number | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Skeleton card for loading state
const ReportSkeleton = () => (
  <div className="flex items-start gap-3 rounded-xl bg-gray-100/80 p-4 animate-pulse">
    <div className="h-11 w-11 shrink-0 rounded-lg bg-gray-200" />
    <div className="flex-1 space-y-2 pt-0.5">
      <div className="h-3.5 w-3/4 rounded bg-gray-200" />
      <div className="h-3 w-1/2 rounded bg-gray-200" />
    </div>
    <div className="h-3 w-10 shrink-0 rounded bg-gray-200 mt-0.5" />
  </div>
);

const ReportSkeletonDesktop = () => (
  <div className="rounded-xl bg-gray-50 p-4 animate-pulse">
    <div className="flex items-start gap-3.5">
      <div className="h-12 w-12 shrink-0 rounded-xl bg-gray-200" />
      <div className="flex-1 space-y-2 pt-0.5">
        <div className="flex items-center justify-between gap-2">
          <div className="h-4 w-2/5 rounded bg-gray-200" />
          <div className="h-3 w-10 rounded bg-gray-200" />
        </div>
        <div className="h-3 w-3/5 rounded bg-gray-200" />
        <div className="h-5 w-14 rounded-full bg-gray-200" />
      </div>
    </div>
  </div>
);

// Map report types to icons
const getReportIcon = (type: string): string => {
  const lowerType = type.toLowerCase();
  if (lowerType.includes('parking')) return '🚗';
  if (lowerType.includes('graffiti')) return '🎨';
  if (lowerType.includes('dump')) return '🗑️';
  if (lowerType.includes('pothole')) return '🕳️';
  if (lowerType.includes('streetlight')) return '💡';
  return '📍';
};

// formatDate is now a shared utility — imported from @/lib/format

export default function ReportsPanel({ address, lat, lng, onCreateNew, onReportsLoaded }: ReportsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    setHasError(false);
    try {
      const params = new URLSearchParams({
        lat: lat.toString(),
        lng: lng.toString(),
        limit: '10',
      });
      
      const response = await fetch(`${API_URL}/reports/nearby?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch reports');
      }
      
      const data = await response.json();
      setReports(data);
      onReportsLoaded?.(data);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setHasError(true);
      setReports([]);
      onReportsLoaded?.([]);
    } finally {
      setIsLoading(false);
    }
  }, [lat, lng]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

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
              <h2 className="font-display text-xl font-bold text-gray-900 flex items-center gap-2">
                Nearby Reports
                {!isLoading && reports.length > 0 && (
                  <span className="text-xs font-bold text-primary bg-primary/10 rounded-full px-2 py-0.5">
                    {reports.length}
                  </span>
                )}
              </h2>
              <p className="text-sm text-gray-500 truncate mt-1">
                {address}
              </p>
            </div>

            {/* Reports list - Better card spacing */}
            <div className="space-y-3">
              {isLoading ? (
                <>
                  <ReportSkeleton />
                  <ReportSkeleton />
                  <ReportSkeleton />
                </>
              ) : hasError ? (
                <div className="text-center py-8">
                  <div className="text-3xl mb-2" aria-hidden="true">⚠️</div>
                  <p className="font-semibold text-gray-700 text-sm">Couldn't load reports</p>
                  <p className="text-gray-500 text-xs mt-1">Check your connection and try again.</p>
                  <button
                    onClick={fetchReports}
                    className="mt-3 text-xs text-primary font-medium hover:underline"
                  >
                    Retry
                  </button>
                </div>
              ) : reports.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-3xl mb-2" aria-hidden="true">✅</div>
                  <p className="font-semibold text-gray-700 text-sm">All clear!</p>
                  <p className="text-gray-500 text-xs mt-1">No recent 311 reports near this address.</p>
                </div>
              ) : (
                (isExpanded ? reports : reports.slice(0, 4)).map((report) => (
                  <div
                    key={report.id}
                    className="flex items-start gap-3 rounded-xl bg-gray-100/80 p-4"
                  >
                    <div className="relative h-11 w-11 shrink-0 rounded-lg overflow-hidden bg-white shadow-sm flex items-center justify-center text-xl">
                      <span aria-hidden="true">{getReportIcon(report.type)}</span>
                      {report.photo_url && (
                        <img
                          src={report.photo_url.split('#')[0]}
                          alt={report.type}
                          className="absolute inset-0 h-full w-full object-cover"
                          onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-sm text-gray-900 truncate min-w-0">{report.type}</span>
                        <span
                          className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                            report.status === 'open'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {report.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-1">{formatAddress(report.address)}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {report.public_id && (
                          <p className="text-[10px] text-gray-400">Case #{report.public_id}</p>
                        )}
                        {report.distance_meters != null && (
                          <p className="text-[10px] text-gray-400">{formatDistance(report.distance_meters)}</p>
                        )}
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] text-gray-400 font-medium mt-0.5">{formatDate(report.date, report.raw_date)}</span>
                  </div>
                ))
              )}
            </div>

            {/* "Tap to see more" hint when collapsed and there are hidden reports */}
            {!isLoading && !isExpanded && reports.length > 4 && (
              <button
                onClick={() => setIsExpanded(true)}
                className="mt-3 w-full text-center text-xs text-primary font-medium py-1"
              >
                ↑ Tap to see {reports.length - 4} more report{reports.length - 4 !== 1 ? 's' : ''}
              </button>
            )}

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
            <h2 className="font-display text-xl font-bold text-gray-900 flex items-center gap-2">
              Nearby Reports
              {!isLoading && reports.length > 0 && (
                <span className="text-xs font-bold text-primary bg-primary/10 rounded-full px-2 py-0.5">
                  {reports.length}
                </span>
              )}
            </h2>
            <p className="text-sm text-gray-500 truncate mt-1.5">
              {address}
            </p>
          </div>

          {/* Reports list - Better card spacing */}
          <div className="flex-1 overflow-y-auto p-5 space-y-3 scrollbar-hide">
            {isLoading ? (
              <>
                <ReportSkeletonDesktop />
                <ReportSkeletonDesktop />
                <ReportSkeletonDesktop />
                <ReportSkeletonDesktop />
              </>
            ) : hasError ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-3" aria-hidden="true">⚠️</div>
                <p className="font-semibold text-gray-700">Couldn't load reports</p>
                <p className="text-sm text-gray-500 mt-1">Check your connection and try again.</p>
                <button
                  onClick={fetchReports}
                  className="mt-4 text-sm text-primary font-medium hover:underline"
                >
                  Retry
                </button>
              </div>
            ) : reports.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-3" aria-hidden="true">✅</div>
                <p className="font-semibold text-gray-700">All clear!</p>
                <p className="text-sm text-gray-500 mt-1">No recent 311 reports near this address.</p>
              </div>
            ) : (
              reports.map((report) => (
                <div
                  key={report.id}
                  className="rounded-xl bg-gray-50 p-4 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-start gap-3.5">
                    <div className="relative h-12 w-12 shrink-0 rounded-xl overflow-hidden bg-white shadow-sm ring-1 ring-gray-100 flex items-center justify-center text-xl">
                      <span aria-hidden="true">{getReportIcon(report.type)}</span>
                      {report.photo_url && (
                        <img
                          src={report.photo_url.split('#')[0]}
                          alt={report.type}
                          className="absolute inset-0 h-full w-full object-cover"
                          onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="font-semibold text-gray-900 truncate min-w-0">{report.type}</span>
                        <span className="shrink-0 text-xs text-gray-400">{formatDate(report.date, report.raw_date)}</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{formatAddress(report.address)}</p>
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-block rounded-full px-2.5 py-1 text-xs font-bold ${
                            report.status === 'open'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {report.status}
                        </span>
                        {report.public_id && (
                          <span className="text-xs text-gray-400">Case #{report.public_id}</span>
                        )}
                        {report.distance_meters != null && (
                          <span className="text-xs text-gray-400">{formatDistance(report.distance_meters)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
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
