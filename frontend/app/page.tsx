'use client';

import { useState, useCallback, useRef, useMemo } from 'react';
import MapboxMap, { Marker, Popup, MapRef } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import AddressSearch from '@/components/AddressSearch';
import AlertPanel, { type AlertCreatedData } from '@/components/AlertPanel';
import ReportsPanel, { type Report } from '@/components/ReportsPanel';
import MapControls from '@/components/MapControls';
import { formatDistance, formatDate, formatAddress } from '@/lib/format';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;
const SF_CENTER = { lat: 37.7749, lng: -122.4194 };

const SF_BOUNDS = {
  minLng: -122.52,
  maxLng: -122.35,
  minLat: 37.70,
  maxLat: 37.83,
};

export default function Home() {
  const mapRef = useRef<MapRef>(null);

  const [selectedLocation, setSelectedLocation] = useState<{
    address: string;
    lat: number;
    lng: number;
  } | null>(null);

  const [showAlertPanel, setShowAlertPanel] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  /** True once the user has successfully created an alert for the current location. */
  const [hasAlert, setHasAlert] = useState(false);
  const [reportMarkers, setReportMarkers] = useState<Report[]>([]);
  // popupReport: the primary (first) report in the clicked cluster.
  // popupGroup: the full set of reports at that lat/lng — drives multi-report popup UI.
  const [popupReport, setPopupReport] = useState<Report | null>(null);
  const [popupGroup, setPopupGroup] = useState<Report[]>([]);
  const [popupGroupIndex, setPopupGroupIndex] = useState(0);

  // Group markers that share the exact same lat/lng (e.g. intersection reports).
  // Shows a count badge on clustered markers so stacked dots are visible.
  const groupedMarkers = useMemo<Report[][]>(() => {
    const groups = new Map<string, Report[]>();
    reportMarkers.forEach((r) => {
      const key = `${r.latitude.toFixed(6)},${r.longitude.toFixed(6)}`;
      const group = groups.get(key) ?? [];
      group.push(r);
      groups.set(key, group);
    });
    return Array.from(groups.values());
  }, [reportMarkers]);

  const handleLocationSelect = useCallback(
    (address: string, lat: number, lng: number) => {
      setSelectedLocation({ address, lat, lng });
      setHasSearched(true);
      
      mapRef.current?.flyTo({
        center: [lng, lat],
        zoom: 17,
        duration: 1500,
      });
    },
    []
  );

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleAlertCreated = useCallback((_alert: AlertCreatedData) => {
    // Alert was created — set the badge. Panel handles its own close
    // (via setTimeout → onClose after the success animation, or Done button).
    // _alert data available here for future use (e.g. alert ID tracking, list display).
    setHasAlert(true);
  }, []);

  const handleCreateNew = () => {
    setShowAlertPanel(true);
  };

  // Called when user clicks a report card in the panel.
  // Finds the cluster that contains the clicked report, opens its popup, and flies to it.
  const handleReportCardClick = useCallback((report: Report) => {
    const cluster = groupedMarkers.find((group) => group.some((r) => r.id === report.id)) ?? [report];
    const idx = cluster.findIndex((r) => r.id === report.id);
    setPopupReport(cluster[0]);
    setPopupGroup(cluster);
    setPopupGroupIndex(Math.max(idx, 0));
    mapRef.current?.flyTo({
      center: [report.longitude, report.latitude],
      zoom: 17,
      duration: 800,
    });
  }, [groupedMarkers]);

  const handleBack = () => {
    setSelectedLocation(null);
    setHasSearched(false);
    setReportMarkers([]);
    setPopupReport(null);
    setPopupGroup([]);
    setPopupGroupIndex(0);
    setHasAlert(false);
    mapRef.current?.flyTo({
      center: [SF_CENTER.lng, SF_CENTER.lat],
      zoom: 12,
      duration: 1500,
    });
  };

  const handleRecenter = useCallback(() => {
    if (selectedLocation) {
      mapRef.current?.flyTo({
        center: [selectedLocation.lng, selectedLocation.lat],
        zoom: 17,
        duration: 1000,
      });
    } else {
      mapRef.current?.flyTo({
        center: [SF_CENTER.lng, SF_CENTER.lat],
        zoom: 12,
        duration: 1000,
      });
    }
  }, [selectedLocation]);

  const handleZoomIn = useCallback(() => {
    const zoom = mapRef.current?.getZoom() || 12;
    mapRef.current?.easeTo({ zoom: Math.min(zoom + 1, 20), duration: 300 });
  }, []);

  const handleZoomOut = useCallback(() => {
    const zoom = mapRef.current?.getZoom() || 12;
    mapRef.current?.easeTo({ zoom: Math.max(zoom - 1, 10), duration: 300 });
  }, []);

  return (
    <div className="relative h-dvh w-screen overflow-hidden bg-black">
      {/* Full-screen Map */}
      <div className="absolute inset-0">
        <MapboxMap
          ref={mapRef}
          initialViewState={{
            longitude: SF_CENTER.lng,
            latitude: SF_CENTER.lat,
            zoom: 12,
          }}
          mapStyle="mapbox://styles/mapbox/dark-v11"
          mapboxAccessToken={MAPBOX_TOKEN}
          style={{ width: '100%', height: '100%' }}
          maxBounds={[
            [SF_BOUNDS.minLng, SF_BOUNDS.minLat],
            [SF_BOUNDS.maxLng, SF_BOUNDS.maxLat],
          ]}
          attributionControl={false}
        >
          {/* Report markers — grouped by lat/lng; clustered markers show a count badge */}
          {groupedMarkers.map((group) => {
            const primary = group[0]; // Most relevant report (sorted by distance + recency by backend)
            const count = group.length;
            return (
              <Marker
                key={primary.id}
                longitude={primary.longitude}
                latitude={primary.latitude}
                anchor="center"
                onClick={(e) => {
                  e.originalEvent.stopPropagation();
                  setPopupReport(primary);
                  setPopupGroup(group);
                  setPopupGroupIndex(0);
                }}
              >
                <div className="relative cursor-pointer hover:scale-125 transition-transform">
                  <div
                    className={`h-3.5 w-3.5 rounded-full border-2 border-white shadow-md ${
                      primary.status === 'open' ? 'bg-amber-400' : 'bg-emerald-400'
                    }`}
                    title={`${count > 1 ? `${count} reports` : primary.type} — ${formatAddress(primary.address)}`}
                  />
                  {count > 1 && (
                    <span className="absolute -top-2 -right-2 flex h-3.5 w-3.5 items-center justify-center rounded-full border border-white bg-gray-700 text-[7px] font-bold leading-none text-white shadow">
                      {count}
                    </span>
                  )}
                </div>
              </Marker>
            );
          })}

          {/* Popup for clicked report marker.
              - Single report: standard detail card.
              - Cluster (multiple reports at same lat/lng): header shows "N reports" + pagination
                arrows so users can browse all reports at that location, not just the primary one. */}
          {popupReport && (() => {
            const activeReport = popupGroup.length > 1 ? popupGroup[popupGroupIndex] : popupReport;
            const isCluster = popupGroup.length > 1;
            const closePopup = () => {
              setPopupReport(null);
              setPopupGroup([]);
              setPopupGroupIndex(0);
            };
            return (
              <Popup
                longitude={popupReport.longitude}
                latitude={popupReport.latitude}
                anchor="bottom"
                offset={12}
                closeButton={false}
                onClose={closePopup}
                style={{ padding: 0 }}
              >
                <div className="bg-white rounded-xl shadow-xl ring-1 ring-black/10 overflow-hidden min-w-[200px] max-w-[240px]">
                  {activeReport.photo_url && (
                    <img
                      src={activeReport.photo_url}
                      alt={activeReport.type}
                      className="w-full h-28 object-cover"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  )}
                  <div className="p-3">
                    {/* Header: type + close button; cluster indicator when multiple */}
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900 leading-tight">{activeReport.type}</p>
                        {isCluster && (
                          <p className="text-[10px] text-primary font-medium mt-0.5">
                            {popupGroupIndex + 1} of {popupGroup.length} at this location
                          </p>
                        )}
                      </div>
                      <button
                        onClick={closePopup}
                        className="shrink-0 text-gray-400 hover:text-gray-600 transition-colors -mt-0.5"
                        aria-label="Close popup"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 line-clamp-1">{formatAddress(activeReport.address)}</p>
                    <p className="text-[10px] text-gray-400 mb-2">{formatDate(activeReport.date, activeReport.raw_date)}</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                        activeReport.status === 'open'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-emerald-100 text-emerald-700'
                      }`}>
                        {activeReport.status}
                      </span>
                      {activeReport.distance_meters != null && (
                        <span className="text-[10px] text-gray-400">{formatDistance(activeReport.distance_meters)}</span>
                      )}
                      {activeReport.public_id && (
                        <span className="text-[10px] text-gray-400">#{activeReport.public_id}</span>
                      )}
                    </div>
                    {/* Prev/Next navigation for clustered markers */}
                    {isCluster && (
                      <div className="flex items-center justify-between gap-2 mt-2.5">
                        <button
                          onClick={() => setPopupGroupIndex((i) => Math.max(i - 1, 0))}
                          disabled={popupGroupIndex === 0}
                          className="flex-1 rounded-lg border border-gray-200 py-1 text-xs font-medium text-gray-600 disabled:opacity-30 hover:bg-gray-50 transition-colors"
                        >
                          ← Prev
                        </button>
                        <button
                          onClick={() => setPopupGroupIndex((i) => Math.min(i + 1, popupGroup.length - 1))}
                          disabled={popupGroupIndex === popupGroup.length - 1}
                          className="flex-1 rounded-lg border border-gray-200 py-1 text-xs font-medium text-gray-600 disabled:opacity-30 hover:bg-gray-50 transition-colors"
                        >
                          Next →
                        </button>
                      </div>
                    )}
                    {/* CTA: let users jump straight from a report popup to creating an alert */}
                    <button
                      onClick={() => {
                        closePopup();
                        handleCreateNew();
                      }}
                      className="mt-2.5 w-full rounded-lg bg-primary py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
                    >
                      🔔 Set Alert for This Area
                    </button>
                  </div>
                </div>
              </Popup>
            );
          })()}

          {selectedLocation && (
            <Marker
              longitude={selectedLocation.lng}
              latitude={selectedLocation.lat}
              anchor="center"
            >
              <div className="relative">
                {/* Pulse ring */}
                <div className="absolute inset-0 h-12 w-12 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/30 animate-pulse-ring" />
                {/* Marker */}
                <div className="relative h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-white bg-primary shadow-lg shadow-primary/50" />
              </div>
            </Marker>
          )}
        </MapboxMap>
      </div>

      {/* Initial State: Centered Search */}
      {!hasSearched && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 animate-fadeIn">
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/80 pointer-events-none" />
          
          <div className="relative w-full max-w-md animate-scaleIn">
            {/* Main card - Improved padding: 8 on mobile, 10 on desktop */}
            <div className="glass rounded-2xl p-8 sm:p-10 ring-1 ring-white/10">
              {/* Logo - Better vertical spacing */}
              <div className="mb-10 text-center">
                <div className="inline-flex items-center gap-2 mb-5">
                  <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center">
                    <svg className="h-7 w-7 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                  </div>
                </div>
                <h1 className="font-display text-3xl sm:text-4xl font-bold text-white tracking-tight mb-3">
                  Alert311
                </h1>
                <p className="text-base sm:text-lg text-white/70 font-medium">
                  Get notified about 311 issues near you
                </p>
              </div>

              {/* Search - More space above */}
              <AddressSearch onLocationSelect={handleLocationSelect} />

              {/* Footer hint - More space above */}
              <p className="mt-8 text-center text-xs text-white/40">
                San Francisco only • SMS alerts for nearby reports
              </p>
            </div>
          </div>
        </div>
      )}

      {/* After Search: Header + Reports Panel + Map Controls */}
      {hasSearched && selectedLocation && !showAlertPanel && (
        <>
          {/* Header - Top - Improved padding and spacing */}
          <div className="fixed top-0 left-0 right-0 z-40 safe-top animate-slideDown">
            <div className="flex items-center gap-3 p-4 sm:p-5">
              <button
                onClick={handleBack}
                className="glass flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ring-1 ring-white/10 text-white/80 hover:text-white hover:bg-white/10 transition-colors active:scale-95"
                aria-label="Back to search"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <div className="glass flex-1 rounded-xl px-4 py-3 ring-1 ring-white/10">
                <div className="flex items-center gap-2.5">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse shrink-0" />
                  <span className="text-sm font-medium text-white/90 truncate flex-1 min-w-0">
                    {selectedLocation.address.split(',')[0]}
                  </span>
                  {hasAlert && (
                    <span
                      className="shrink-0 flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[11px] font-semibold text-emerald-300 ring-1 ring-emerald-500/30"
                      title="Alert active for this location"
                    >
                      🔔 Alert active
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Map Controls */}
          <MapControls 
            onRecenter={handleRecenter}
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
          />

          {/* Reports Panel - Bottom Sheet on Mobile, Side Panel on Desktop */}
          <ReportsPanel 
            address={selectedLocation.address}
            lat={selectedLocation.lat}
            lng={selectedLocation.lng}
            onCreateNew={handleCreateNew}
            onReportsLoaded={setReportMarkers}
            onReportClick={handleReportCardClick}
            activeReportId={popupGroup.length > 0 ? popupGroup[popupGroupIndex]?.id : (popupReport?.id ?? null)}
            hasAlert={hasAlert}
          />
        </>
      )}

      {/* Alert Panel (Create New) */}
      {showAlertPanel && selectedLocation && (
        <AlertPanel
          address={selectedLocation.address}
          lat={selectedLocation.lat}
          lng={selectedLocation.lng}
          onClose={() => setShowAlertPanel(false)}
          onAlertCreated={handleAlertCreated}
        />
      )}

      {/* Attribution */}
      <div className="fixed bottom-2 left-2 z-30 text-[10px] text-white/30">
        © Mapbox © OpenStreetMap
      </div>
    </div>
  );
}
