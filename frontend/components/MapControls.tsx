'use client';

interface MapControlsProps {
  onRecenter: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
}

export default function MapControls({ onRecenter, onZoomIn, onZoomOut }: MapControlsProps) {
  return (
    <div className="fixed right-4 bottom-72 lg:bottom-6 lg:right-[420px] z-40 flex flex-col gap-2">
      {/* Recenter Button */}
      <button
        onClick={onRecenter}
        className="glass h-11 w-11 rounded-xl ring-1 ring-white/10 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 transition-colors active:scale-95"
        aria-label="Recenter map"
        title="Recenter map"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      </button>

      {/* Zoom Controls */}
      <div className="glass rounded-xl ring-1 ring-white/10 overflow-hidden flex flex-col">
        <button
          onClick={onZoomIn}
          className="h-10 w-11 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 transition-colors active:scale-95 border-b border-white/10"
          aria-label="Zoom in"
          title="Zoom in"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <button
          onClick={onZoomOut}
          className="h-10 w-11 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 transition-colors active:scale-95"
          aria-label="Zoom out"
          title="Zoom out"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
          </svg>
        </button>
      </div>
    </div>
  );
}
