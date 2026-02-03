'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useToast } from './Toast';

interface AddressSearchProps {
  onLocationSelect: (address: string, lat: number, lng: number) => void;
}

export default function AddressSearch({ onLocationSelect }: AddressSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useToast();

  const searchAddress = useCallback(async (searchQuery: string) => {
    if (!searchQuery || searchQuery.length < 3) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
          searchQuery
        )}.json?access_token=${process.env.NEXT_PUBLIC_MAPBOX_TOKEN}&bbox=-122.5148,37.7034,-122.3549,37.8324&proximity=-122.4194,37.7749&types=address,poi`
      );
      const data = await response.json();
      setResults(data.features || []);
      setShowResults(true);
    } catch (error) {
      console.error('Geocoding error:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Reverse geocode coordinates to address
  const reverseGeocode = useCallback(async (lat: number, lng: number) => {
    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${lng},${lat}.json?access_token=${process.env.NEXT_PUBLIC_MAPBOX_TOKEN}&types=address`
      );
      const data = await response.json();
      if (data.features && data.features.length > 0) {
        return data.features[0].place_name;
      }
      return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    } catch (error) {
      console.error('Reverse geocoding error:', error);
      return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
  }, []);

  // Use device location
  const handleUseLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      addToast('error', 'Geolocation is not supported by your browser');
      return;
    }

    setIsLocating(true);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        
        // Check if within SF bounds
        const SF_BOUNDS = {
          minLng: -122.52,
          maxLng: -122.35,
          minLat: 37.70,
          maxLat: 37.83,
        };

        if (
          longitude < SF_BOUNDS.minLng ||
          longitude > SF_BOUNDS.maxLng ||
          latitude < SF_BOUNDS.minLat ||
          latitude > SF_BOUNDS.maxLat
        ) {
          addToast('error', 'Your location is outside San Francisco');
          setIsLocating(false);
          return;
        }

        const address = await reverseGeocode(latitude, longitude);
        setIsLocating(false);
        addToast('success', 'Location found!');
        onLocationSelect(address, latitude, longitude);
      },
      (error) => {
        setIsLocating(false);
        switch (error.code) {
          case error.PERMISSION_DENIED:
            addToast('error', 'Location permission denied');
            break;
          case error.POSITION_UNAVAILABLE:
            addToast('error', 'Location unavailable');
            break;
          case error.TIMEOUT:
            addToast('error', 'Location request timed out');
            break;
          default:
            addToast('error', 'Could not get your location');
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  }, [addToast, onLocationSelect, reverseGeocode]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) {
        searchAddress(query);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, searchAddress]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (feature: any) => {
    const [lng, lat] = feature.center;
    const address = feature.place_name;
    
    setQuery(feature.text);
    setShowResults(false);
    onLocationSelect(address, lat, lng);
  };

  return (
    <div ref={searchRef} className="relative w-full space-y-3">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40">
          {isLoading ? (
            <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowResults(true)}
          placeholder="Enter an address in SF..."
          className="w-full h-14 rounded-xl bg-white/10 pl-12 pr-4 text-base text-white placeholder:text-white/40 ring-1 ring-white/20 focus:ring-2 focus:ring-primary focus:outline-none transition-shadow"
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
          spellCheck="false"
        />
      </div>

      {/* Use My Location Button */}
      <button
        onClick={handleUseLocation}
        disabled={isLocating}
        className="w-full h-12 rounded-xl bg-white/5 ring-1 ring-white/10 text-white/70 font-medium flex items-center justify-center gap-2 hover:bg-white/10 hover:text-white transition-colors disabled:opacity-50"
      >
        {isLocating ? (
          <>
            <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Finding your location...</span>
          </>
        ) : (
          <>
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>Use my location</span>
          </>
        )}
      </button>

      {/* Results Dropdown */}
      {showResults && results.length > 0 && (
        <div className="absolute top-14 left-0 right-0 mt-2 rounded-xl bg-white/95 backdrop-blur-xl overflow-hidden shadow-2xl ring-1 ring-black/10 animate-slideDown z-50">
          <div className="max-h-64 overflow-y-auto scrollbar-hide">
            {results.map((feature, index) => (
              <button
                key={feature.id || index}
                onClick={() => handleSelect(feature)}
                className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-gray-100 transition-colors border-b border-gray-100 last:border-b-0"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-gray-500">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-900">{feature.text}</div>
                  <div className="mt-0.5 text-xs text-gray-500 truncate">
                    {feature.place_name.replace(`${feature.text}, `, '')}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* No results message */}
      {showResults && query.length >= 3 && results.length === 0 && !isLoading && (
        <div className="absolute top-14 left-0 right-0 mt-2 rounded-xl bg-white/95 backdrop-blur-xl p-4 text-center shadow-xl ring-1 ring-black/10 animate-slideDown">
          <p className="text-sm text-gray-500">No addresses found in San Francisco</p>
        </div>
      )}
    </div>
  );
}
