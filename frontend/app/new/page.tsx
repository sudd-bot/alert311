'use client';

import { useState, useCallback, useRef } from 'react';
import Map, { Marker, MapRef } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import { 
  MapPin, 
  Bell, 
  Search, 
  X, 
  Plus,
  Navigation,
  AlertCircle,
  CheckCircle2,
  Loader2
} from 'lucide-react';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const SF_CENTER = { lat: 37.7749, lng: -122.4194 };

type ViewState = 'search' | 'location-selected' | 'create-alert';

type Report = {
  id: string;
  type: string;
  date: string;
  status: 'open' | 'closed';
};

export default function NewHome() {
  const mapRef = useRef<MapRef>(null);
  const [viewState, setViewState] = useState<ViewState>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState<{
    address: string;
    lat: number;
    lng: number;
  } | null>(null);
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [loadingReports, setLoadingReports] = useState(false);

  const fetchReports = async (lat: number, lng: number) => {
    setLoadingReports(true);
    try {
      const response = await fetch(
        `${API_URL}/reports/nearby?lat=${lat}&lng=${lng}&limit=10`
      );
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setReports(data);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setReports([]);
    } finally {
      setLoadingReports(false);
    }
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;
    
    setIsLoading(true);
    
    try {
      // Mapbox Geocoding API - restrict to addresses only
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?` +
        `access_token=${MAPBOX_TOKEN}&` +
        `proximity=-122.4194,37.7749&` + // Bias results to SF
        `bbox=-122.52,37.70,-122.35,37.83&` + // Limit to SF bounds
        `types=address&` + // Only return street addresses
        `limit=5`
      );
      
      const data = await response.json();
      
      if (data.features && data.features.length > 0) {
        // Find first result that has a street number
        const addressFeature = data.features.find((f: any) => {
          // Must be type "address" and include a street number
          return f.place_type.includes('address') && 
                 f.address !== undefined && 
                 f.address !== null;
        });
        
        if (!addressFeature) {
          alert('Please enter a complete street address (e.g., "123 Main St, San Francisco")');
          setIsLoading(false);
          return;
        }
        
        const [lng, lat] = addressFeature.center;
        const address = addressFeature.place_name;
        
        setSelectedLocation({ address, lat, lng });
        setViewState('location-selected');
        
        // Fetch reports for this location
        fetchReports(lat, lng);
        
        mapRef.current?.flyTo({
          center: [lng, lat],
          zoom: 17,
          duration: 1200,
          essential: true
        });
      } else {
        alert('Address not found. Please enter a complete street address in San Francisco.');
      }
    } catch (error) {
      console.error('Geocoding error:', error);
      alert('Error searching for address. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setViewState('search');
    setSelectedLocation(null);
    setSearchQuery('');
    mapRef.current?.flyTo({
      center: [SF_CENTER.lng, SF_CENTER.lat],
      zoom: 12,
      duration: 1200,
    });
  };

  const handleCreateAlert = async () => {
    setIsLoading(true);
    // API call here
    setTimeout(() => {
      setIsLoading(false);
      setViewState('location-selected');
      // Show success toast
    }, 1500);
  };

  return (
    <div className="relative h-dvh w-full bg-[#1a1410] overflow-hidden">
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&family=Space+Mono:wght@400;700&display=swap');
        
        * {
          font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        @keyframes slideUp {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes scaleIn {
          from {
            transform: scale(0.9);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        @keyframes pulse-soft {
          0%, 100% {
            opacity: 0.3;
            transform: scale(1);
          }
          50% {
            opacity: 0.5;
            transform: scale(1.2);
          }
        }

        .animate-slide-up {
          animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .animate-fade-in {
          animation: fadeIn 0.4s ease-out;
        }

        .animate-scale-in {
          animation: scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .animate-pulse-soft {
          animation: pulse-soft 2s ease-in-out infinite;
        }

        .stagger-1 { animation-delay: 0.1s; }
        .stagger-2 { animation-delay: 0.2s; }
        .stagger-3 { animation-delay: 0.3s; }

        .text-gradient {
          background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .bg-grain {
          background-image: 
            repeating-linear-gradient(
              0deg,
              transparent,
              transparent 2px,
              rgba(255, 255, 255, 0.03) 2px,
              rgba(255, 255, 255, 0.03) 4px
            );
        }

        .shadow-brutal {
          box-shadow: 8px 8px 0px rgba(255, 107, 53, 0.3);
        }

        .shadow-brutal-sm {
          box-shadow: 4px 4px 0px rgba(255, 107, 53, 0.2);
        }
      `}</style>

      {/* Map Background */}
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
          attributionControl={false}
        >
          {selectedLocation && (
            <Marker
              longitude={selectedLocation.lng}
              latitude={selectedLocation.lat}
              anchor="bottom"
            >
              <div className="relative flex flex-col items-center animate-scale-in">
                {/* Pulse rings */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-20 h-20 bg-[#ff6b35] rounded-full animate-pulse-soft" />
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-20 h-20 bg-[#ff6b35] rounded-full animate-pulse-soft" style={{ animationDelay: '0.5s' }} />
                {/* Pin */}
                <div className="relative z-10 w-16 h-16 bg-[#ff6b35] rounded-sm rotate-45 border-4 border-[#1a1410] shadow-2xl flex items-center justify-center">
                  <MapPin className="w-7 h-7 text-[#1a1410] -rotate-45" strokeWidth={3} />
                </div>
              </div>
            </Marker>
          )}
        </Map>
      </div>

      {/* Grain overlay */}
      <div className="absolute inset-0 bg-grain pointer-events-none opacity-60" />

      {/* Search View */}
      {viewState === 'search' && (
        <div className="absolute inset-0 z-10 flex flex-col bg-gradient-to-b from-[#1a1410] via-[#1a1410]/50 to-[#1a1410]/90">
          {/* Logo & Title */}
          <div className="relative pt-24 pb-12 px-6 text-center animate-fade-in" style={{ paddingTop: 'max(6rem, env(safe-area-inset-top) + 4rem)' }}>
            <div className="inline-flex items-center justify-center w-28 h-28 bg-[#ff6b35] rounded-sm rotate-45 animate-scale-in shadow-2xl" style={{ marginBottom: '5rem' }}>
              <Bell className="w-14 h-14 text-[#1a1410] -rotate-45" strokeWidth={2.5} />
            </div>
            <h1 className="text-5xl font-black text-[#fef6e4] mb-6 tracking-tight animate-fade-in stagger-1" style={{ fontFamily: 'DM Sans' }}>
              Alert<span className="text-gradient">311</span>
            </h1>
            <p className="text-lg text-[#fef6e4]/70 leading-relaxed text-center animate-fade-in stagger-2" style={{ fontFamily: 'Space Mono' }}>
              Real-time civic alerts<br />for San Francisco
            </p>
          </div>

          {/* Search Input - Centered */}
          <div className="relative flex-1 flex items-center justify-center px-6 animate-slide-up">
            <div className="w-full max-w-md">
              <div className="relative">
                <div className="absolute inset-0 bg-[#ff6b35]/20 rounded-sm transform translate-x-2 translate-y-2" />
                <div className="relative bg-[#2a2420] border-4 border-[#ff6b35] rounded-sm">
                  {isLoading ? (
                    <Loader2 className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-[#ff6b35] animate-spin" strokeWidth={2.5} />
                  ) : (
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-[#ff6b35]" strokeWidth={2.5} />
                  )}
                  <input
                    type="text"
                    placeholder="123 Main St, San Francisco..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    disabled={isLoading}
                    className="w-full h-20 bg-transparent text-[#fef6e4] placeholder-[#fef6e4]/40 text-lg font-medium focus:outline-none disabled:opacity-50"
                    style={{ fontFamily: 'DM Sans', paddingLeft: '6rem', paddingRight: '1.5rem' }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && searchQuery && !isLoading) {
                        handleSearch(searchQuery);
                      }
                    }}
                  />
                </div>
              </div>
              <div className="mt-8 flex items-center justify-center gap-2 text-sm text-[#fef6e4]/50" style={{ fontFamily: 'Space Mono' }}>
                <div className="w-2 h-2 bg-[#ff6b35] rounded-full" />
                <span>San Francisco only</span>
              </div>
            </div>
          </div>

          {/* Bottom spacer */}
          <div className="h-32" />
        </div>
      )}

      {/* Location Selected View */}
      {viewState === 'location-selected' && selectedLocation && (
        <>
          {/* Top Bar */}
          <div className="absolute top-0 left-0 right-0 z-20 pt-safe animate-slide-up">
            <div className="flex items-center gap-3 p-4">
              <button
                onClick={handleBack}
                className="w-14 h-14 bg-[#fef6e4] border-4 border-[#1a1410] rounded-sm shadow-brutal-sm flex items-center justify-center active:translate-x-1 active:translate-y-1 active:shadow-none transition-all"
              >
                <X className="w-6 h-6 text-[#1a1410]" strokeWidth={3} />
              </button>
              <div className="flex-1 bg-[#2a2420] border-4 border-[#ff6b35] rounded-sm px-5 py-4 shadow-brutal-sm">
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-[#ff6b35] shrink-0" strokeWidth={3} />
                  <span className="text-base font-bold text-[#fef6e4] truncate" style={{ fontFamily: 'DM Sans' }}>
                    {selectedLocation.address.split(',')[0]}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Recenter Button */}
          <div className="absolute top-32 right-4 z-20 animate-scale-in" style={{ animationDelay: '0.2s' }}>
            <button
              onClick={() => {
                mapRef.current?.flyTo({
                  center: [selectedLocation.lng, selectedLocation.lat],
                  zoom: 17,
                  duration: 800,
                });
              }}
              className="w-14 h-14 bg-[#fef6e4] border-4 border-[#1a1410] rounded-sm shadow-brutal-sm flex items-center justify-center active:translate-x-1 active:translate-y-1 active:shadow-none transition-all"
            >
              <Navigation className="w-6 h-6 text-[#1a1410]" strokeWidth={3} />
            </button>
          </div>

          {/* Bottom Sheet */}
          <div className="absolute bottom-0 left-0 right-0 z-30 pb-safe animate-slide-up">
            <div className="bg-[#fef6e4] border-t-8 border-[#ff6b35] max-h-[70vh] overflow-hidden">
              {/* Decorative top bar */}
              <div className="h-3 bg-gradient-to-r from-[#ff6b35] via-[#f7931e] to-[#ff6b35]" />

              {/* Content */}
              <div className="px-6 py-8">
                {/* Address */}
                <div className="mb-8">
                  <div className="inline-block bg-[#1a1410] px-3 py-1 mb-3">
                    <span className="text-xs font-bold text-[#ff6b35] tracking-wider" style={{ fontFamily: 'Space Mono' }}>
                      LOCATION
                    </span>
                  </div>
                  <h2 className="text-3xl font-black text-[#1a1410] mb-2 tracking-tight" style={{ fontFamily: 'DM Sans' }}>
                    {selectedLocation.address.split(',')[0]}
                  </h2>
                  <p className="text-base text-[#1a1410]/60 font-medium" style={{ fontFamily: 'Space Mono' }}>
                    {selectedLocation.address.split(',').slice(1).join(',')}
                  </p>
                </div>

                {/* Create Alert Button */}
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-[#1a1410] rounded-sm transform translate-x-2 translate-y-2" />
                  <button
                    onClick={() => setViewState('create-alert')}
                    className="relative w-full h-16 bg-[#ff6b35] hover:bg-[#f7931e] border-4 border-[#1a1410] text-[#1a1410] font-black text-lg rounded-sm flex items-center justify-center gap-3 transition-all active:translate-x-2 active:translate-y-2"
                    style={{ fontFamily: 'DM Sans' }}
                  >
                    <Plus className="w-6 h-6" strokeWidth={3} />
                    CREATE ALERT
                  </button>
                </div>

                {/* Recent Reports */}
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="inline-block bg-[#1a1410] px-3 py-1">
                      <span className="text-xs font-bold text-[#ff6b35] tracking-wider" style={{ fontFamily: 'Space Mono' }}>
                        RECENT REPORTS
                      </span>
                    </div>
                    <div className="h-px flex-1 bg-[#1a1410]/20" />
                    {loadingReports ? (
                      <Loader2 className="w-4 h-4 text-[#1a1410]/40 animate-spin" />
                    ) : (
                      <span className="text-sm font-bold text-[#1a1410]/40" style={{ fontFamily: 'Space Mono' }}>
                        {reports.length}
                      </span>
                    )}
                  </div>

                  {loadingReports ? (
                    <div className="py-8 text-center">
                      <Loader2 className="w-8 h-8 text-[#1a1410]/40 animate-spin mx-auto mb-3" />
                      <p className="text-sm text-[#1a1410]/60" style={{ fontFamily: 'Space Mono' }}>
                        Loading reports...
                      </p>
                    </div>
                  ) : reports.length === 0 ? (
                    <div className="py-8 text-center">
                      <p className="text-sm text-[#1a1410]/60" style={{ fontFamily: 'Space Mono' }}>
                        No recent reports found nearby
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {reports.map((report, idx) => {
                        return (
                          <div
                            key={report.id}
                            className="animate-fade-in"
                            style={{ animationDelay: `${idx * 0.1}s` }}
                          >
                        <div className="relative">
                          <div className="absolute inset-0 bg-[#1a1410]/10 rounded-sm transform translate-x-1 translate-y-1" />
                          <div className="relative flex items-center gap-4 p-4 bg-[#2a2420] border-3 border-[#1a1410] rounded-sm">
                            <div className={`w-12 h-12 rounded-sm flex items-center justify-center shrink-0 border-3 border-[#1a1410] ${
                              report.status === 'open' 
                                ? 'bg-[#f7931e]' 
                                : 'bg-[#6dd47e]'
                            }`}>
                              {report.status === 'open' ? (
                                <AlertCircle className="w-6 h-6 text-[#1a1410]" strokeWidth={3} />
                              ) : (
                                <CheckCircle2 className="w-6 h-6 text-[#1a1410]" strokeWidth={3} />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-base font-bold text-[#fef6e4] mb-1" style={{ fontFamily: 'DM Sans' }}>
                                {report.type}
                              </p>
                              <p className="text-sm text-[#fef6e4]/60 font-medium" style={{ fontFamily: 'Space Mono' }}>
                                {report.date}
                              </p>
                            </div>
                            <div className={`px-3 py-1 rounded-sm border-2 border-[#1a1410] ${
                              report.status === 'open'
                                ? 'bg-[#f7931e]'
                                : 'bg-[#6dd47e]'
                            }`}>
                              <span className="text-xs font-black text-[#1a1410]" style={{ fontFamily: 'DM Sans' }}>
                                {report.status.toUpperCase()}
                              </span>
                            </div>
                          </div>
                        </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Create Alert View */}
      {viewState === 'create-alert' && selectedLocation && (
        <div className="absolute inset-0 z-40 bg-[#fef6e4] animate-slide-up">
          {/* Header */}
          <div className="flex items-center gap-4 p-4 border-b-4 border-[#1a1410] pt-safe bg-gradient-to-r from-[#ff6b35] to-[#f7931e]">
            <button
              onClick={() => setViewState('location-selected')}
              className="w-12 h-12 flex items-center justify-center bg-[#fef6e4] border-3 border-[#1a1410] rounded-sm active:translate-x-1 active:translate-y-1 transition-all"
            >
              <X className="w-6 h-6 text-[#1a1410]" strokeWidth={3} />
            </button>
            <h1 className="text-2xl font-black text-[#1a1410]" style={{ fontFamily: 'DM Sans' }}>
              CREATE ALERT
            </h1>
          </div>

          {/* Form */}
          <div className="p-6 space-y-8 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            {/* Location */}
            <div>
              <div className="inline-block bg-[#1a1410] px-3 py-1 mb-4">
                <label className="text-xs font-bold text-[#ff6b35] tracking-wider" style={{ fontFamily: 'Space Mono' }}>
                  LOCATION
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-0 bg-[#1a1410]/10 rounded-sm transform translate-x-1 translate-y-1" />
                <div className="relative flex items-center gap-4 p-5 bg-[#2a2420] border-3 border-[#1a1410] rounded-sm">
                  <MapPin className="w-6 h-6 text-[#ff6b35] shrink-0" strokeWidth={3} />
                  <div className="flex-1 min-w-0">
                    <p className="text-base font-bold text-[#fef6e4] truncate mb-1" style={{ fontFamily: 'DM Sans' }}>
                      {selectedLocation.address.split(',')[0]}
                    </p>
                    <p className="text-sm text-[#fef6e4]/60 truncate font-medium" style={{ fontFamily: 'Space Mono' }}>
                      {selectedLocation.address.split(',').slice(1).join(',')}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Phone */}
            <div>
              <div className="inline-block bg-[#1a1410] px-3 py-1 mb-4">
                <label className="text-xs font-bold text-[#ff6b35] tracking-wider" style={{ fontFamily: 'Space Mono' }}>
                  PHONE NUMBER
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-0 bg-[#ff6b35]/20 rounded-sm transform translate-x-1 translate-y-1" />
                <input
                  type="tel"
                  placeholder="(555) 123-4567"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="relative w-full h-16 px-5 bg-[#fef6e4] border-4 border-[#ff6b35] rounded-sm text-[#1a1410] placeholder-[#1a1410]/40 text-lg font-bold focus:outline-none focus:border-[#f7931e] transition-colors"
                  style={{ fontFamily: 'DM Sans' }}
                />
              </div>
              <p className="mt-3 text-sm text-[#1a1410]/60 font-medium leading-relaxed" style={{ fontFamily: 'Space Mono' }}>
                We'll text you when new reports appear near this location
              </p>
            </div>

            {/* Info Card */}
            <div className="relative">
              <div className="absolute inset-0 bg-[#f7931e]/30 rounded-sm transform translate-x-1 translate-y-1" />
              <div className="relative p-5 bg-[#fff8dc] border-3 border-[#f7931e] rounded-sm">
                <div className="flex gap-4">
                  <Bell className="w-6 h-6 text-[#f7931e] shrink-0 mt-1" strokeWidth={3} />
                  <div>
                    <p className="text-base font-black text-[#1a1410] mb-2" style={{ fontFamily: 'DM Sans' }}>
                      HOW IT WORKS
                    </p>
                    <p className="text-sm text-[#1a1410]/70 leading-relaxed font-medium" style={{ fontFamily: 'Space Mono' }}>
                      You'll receive SMS notifications when new 311 reports (parking violations, blocked driveways, etc.) are submitted near this address.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="relative pt-4">
              <div className="absolute inset-0 bg-[#1a1410] rounded-sm transform translate-x-2 translate-y-2" />
              <button
                onClick={handleCreateAlert}
                disabled={!phone || isLoading}
                className="relative w-full h-16 bg-[#ff6b35] hover:bg-[#f7931e] disabled:bg-[#d4d4d4] border-4 border-[#1a1410] text-[#1a1410] disabled:text-[#1a1410]/30 font-black text-lg rounded-sm flex items-center justify-center gap-3 transition-all active:translate-x-2 active:translate-y-2 disabled:translate-x-0 disabled:translate-y-0"
                style={{ fontFamily: 'DM Sans' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" strokeWidth={3} />
                    CREATING...
                  </>
                ) : (
                  <>
                    <Bell className="w-6 h-6" strokeWidth={3} />
                    CREATE ALERT
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Attribution */}
      <div className="absolute bottom-2 left-2 z-10 text-xs text-[#fef6e4]/30" style={{ fontFamily: 'Space Mono' }}>
        © Mapbox
      </div>
    </div>
  );
}
