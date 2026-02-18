'use client';

import { useState, useCallback, useRef } from 'react';
import Map, { Marker, Popup, MapRef } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import AddressSearch from '@/components/AddressSearch';
import AlertPanel from '@/components/AlertPanel';
import ReportsPanel, { type Report } from '@/components/ReportsPanel';
import MapControls from '@/components/MapControls';
import { formatDistance, formatDate } from '@/lib/format';

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
  const [reportMarkers, setReportMarkers] = useState<Report[]>([]);
  const [popupReport, setPopupReport] = useState<Report | null>(null);

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

  const handleAlertCreated = useCallback(() => {
    setShowAlertPanel(false);
  }, []);

  const handleCreateNew = () => {
    setShowAlertPanel(true);
  };

  const handleBack = () => {
    setSelectedLocation(null);
    setHasSearched(false);
    setReportMarkers([]);
    setPopupReport(null);
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
        <Map
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
          {/* Report markers — amber (open) or emerald (closed) dots; clickable for popup */}
          {reportMarkers.map((report) => (
            <Marker
              key={report.id}
              longitude={report.longitude}
              latitude={report.latitude}
              anchor="center"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setPopupReport(report);
              }}
            >
              <div
                className={`h-3.5 w-3.5 rounded-full border-2 border-white shadow-md cursor-pointer hover:scale-125 transition-transform ${
                  report.status === 'open' ? 'bg-amber-400' : 'bg-emerald-400'
                }`}
                title={`${report.type} — ${report.address}`}
              />
            </Marker>
          ))}

          {/* Popup for clicked report marker */}
          {popupReport && (
            <Popup
              longitude={popupReport.longitude}
              latitude={popupReport.latitude}
              anchor="bottom"
              offset={12}
              closeButton={false}
              onClose={() => setPopupReport(null)}
              style={{ padding: 0 }}
            >
              <div className="bg-white rounded-xl shadow-xl ring-1 ring-black/10 overflow-hidden min-w-[200px] max-w-[240px]">
                {popupReport.photo_url && (
                  <img
                    src={popupReport.photo_url}
                    alt={popupReport.type}
                    className="w-full h-28 object-cover"
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                )}
                <div className="p-3">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <p className="text-sm font-semibold text-gray-900 leading-tight">{popupReport.type}</p>
                    <button
                      onClick={() => setPopupReport(null)}
                      className="shrink-0 text-gray-400 hover:text-gray-600 transition-colors -mt-0.5"
                      aria-label="Close popup"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 line-clamp-1">{popupReport.address}</p>
                  <p className="text-[10px] text-gray-400 mb-2">{formatDate(popupReport.date, popupReport.raw_date)}</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                      popupReport.status === 'open'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-emerald-100 text-emerald-700'
                    }`}>
                      {popupReport.status}
                    </span>
                    {popupReport.distance_meters != null && (
                      <span className="text-[10px] text-gray-400">{formatDistance(popupReport.distance_meters)}</span>
                    )}
                    {popupReport.public_id && (
                      <span className="text-[10px] text-gray-400">#{popupReport.public_id}</span>
                    )}
                  </div>
                  {/* CTA: let users jump straight from a report popup to creating an alert */}
                  <button
                    onClick={() => {
                      setPopupReport(null);
                      handleCreateNew();
                    }}
                    className="mt-2.5 w-full rounded-lg bg-primary py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
                  >
                    🔔 Set Alert for This Area
                  </button>
                </div>
              </div>
            </Popup>
          )}

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
        </Map>
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
                  <span className="text-sm font-medium text-white/90 truncate">
                    {selectedLocation.address.split(',')[0]}
                  </span>
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
