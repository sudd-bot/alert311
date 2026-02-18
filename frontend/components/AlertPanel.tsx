'use client';

import { useState, useEffect } from 'react';
import { useToast } from './Toast';

/** Shape of the alert object returned by POST /alerts on success. */
export interface AlertCreatedData {
  id: number;
  address: string;
  report_type_id: string;
  active: boolean;
  latitude?: number | null;
  longitude?: number | null;
}

interface AlertPanelProps {
  address: string;
  lat: number;
  lng: number;
  onClose: () => void;
  onAlertCreated: (alert: AlertCreatedData) => void;
}

/**
 * Normalize a US phone number to E.164 format (+1XXXXXXXXXX).
 * Handles inputs like "646-417-1584", "(646) 417-1584", "6464171584", "16464171584", "+16464171584".
 * Non-US numbers with a + prefix are passed through with spaces/dashes stripped.
 * If normalization isn't possible, returns the original string (backend validates).
 */
const normalizePhone = (phone: string): string => {
  const stripped = phone.trim();
  const digits = stripped.replace(/\D/g, '');
  // Already has a + country code prefix — return as +DIGITS
  if (stripped.startsWith('+') && digits.length >= 7) return `+${digits}`;
  // 10-digit US number (no country code)
  if (digits.length === 10) return `+1${digits}`;
  // 11-digit number starting with 1 (US with country code, no +)
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  // Can't normalize — return as-is and let the backend validate
  return stripped;
};

const REPORT_TYPES = [
  { id: '963f1454-7c22-43be-aacb-3f34ae5d0dc7', name: 'Blocked Driveway & Parking', icon: '🚗', comingSoon: false },
  { id: 'graffiti', name: 'Graffiti', icon: '🎨', comingSoon: true },
  { id: 'illegal-dumping', name: 'Illegal Dumping', icon: '🗑️', comingSoon: true },
  { id: 'homeless-encampment', name: 'Homeless Encampment', icon: '🏕️', comingSoon: true },
  { id: 'pothole', name: 'Pothole', icon: '🕳️', comingSoon: true },
  { id: 'streetlight-out', name: 'Streetlight Out', icon: '💡', comingSoon: true },
];

export default function AlertPanel({
  address,
  lat,
  lng,
  onClose,
  onAlertCreated,
}: AlertPanelProps) {
  const [userPhone, setUserPhone] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [selectedReportType, setSelectedReportType] = useState(REPORT_TYPES[0].id);
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState<'phone' | 'verify' | 'create' | 'success'>('phone');
  const [resendCooldown, setResendCooldown] = useState(0);
  /** True when the user already has an active alert for the same address + report type */
  const [isDuplicate, setIsDuplicate] = useState(false);
  const { addToast } = useToast();

  // Pre-fill phone from localStorage so returning users don't have to retype it
  useEffect(() => {
    try {
      const saved = localStorage.getItem('alert311_phone');
      if (saved) setUserPhone(saved);
    } catch {
      // localStorage unavailable (private browsing, permissions) — silently skip
    }
  }, []);

  /**
   * Check if the user already has an active alert for this address + report type.
   * Runs whenever the user reaches the 'create' step or changes the selected type.
   * Purely informational — duplicate creation is allowed; the warning just prevents accidents.
   */
  useEffect(() => {
    if (step !== 'create' || !userPhone) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/alerts?phone=${encodeURIComponent(userPhone)}`
        );
        if (!res.ok || cancelled) return;
        const existingAlerts: Array<{ address: string; report_type_id: string; active: boolean }> = await res.json();
        if (cancelled) return;
        // Normalize the current address for comparison (strip city/state suffix)
        const localStreet = address.split(',')[0].trim().toLowerCase();
        const hasDuplicate = existingAlerts.some(
          (a) =>
            a.active &&
            a.report_type_id === selectedReportType &&
            a.address.toLowerCase().includes(localStreet)
        );
        setIsDuplicate(hasDuplicate);
      } catch {
        // Network/parse error — silently skip; no need to block the UI
      }
    })();
    return () => { cancelled = true; };
  }, [step, userPhone, selectedReportType, address]);

  /**
   * Close the panel when Escape is pressed — standard modal dismiss UX for desktop.
   * Disabled during the success state (user shouldn't accidentally skip the confirmation).
   */
  useEffect(() => {
    if (step === 'success') return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose, step]);

  // Countdown timer for resend cooldown — starts when entering verify step
  useEffect(() => {
    if (step === 'verify') {
      setResendCooldown(30);
      const interval = setInterval(() => {
        setResendCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [step]);

  const sendVerification = async () => {
    // Normalize phone to E.164 before sending — handles "646-417-1584", "(646) 417-1584", etc.
    const phone = normalizePhone(userPhone);
    if (phone !== userPhone) setUserPhone(phone); // Update display to normalized form
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });

      if (response.ok) {
        const data = await response.json().catch(() => ({}));
        if (data.already_verified) {
          // Returning user — already verified, skip to alert creation
          try { localStorage.setItem('alert311_phone', phone); } catch { /* ignore */ }
          setStep('create');
          addToast('success', 'Welcome back!');
        } else {
          setStep('verify');
          addToast('success', 'Verification code sent!');
        }
      } else {
        const data = await response.json().catch(() => ({}));
        addToast('error', data.detail || 'Failed to send verification code');
      }
    } catch (error) {
      console.error('Verification error:', error);
      addToast('error', 'Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const verifyCode = async (codeOverride?: string) => {
    const code = codeOverride ?? verificationCode;
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: userPhone, code }),
      });

      if (response.ok) {
        // Phone verified — persist to localStorage so future visits can skip re-entry
        try { localStorage.setItem('alert311_phone', userPhone); } catch { /* ignore */ }
        setStep('create');
        addToast('success', 'Phone verified!');
      } else {
        addToast('error', 'Invalid verification code');
      }
    } catch (error) {
      console.error('Verify error:', error);
      addToast('error', 'Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const createAlert = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/alerts?phone=${encodeURIComponent(userPhone)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            address,
            latitude: lat,
            longitude: lng,
            report_type_id: selectedReportType,
          }),
        }
      );

      if (response.ok) {
        const alertData = await response.json();
        // Signal parent immediately so the "Alert active" badge appears the moment
        // success is shown — not after the 2.5s auto-close timer fires.
        onAlertCreated(alertData);
        setStep('success');
        // Auto-dismiss after showing the success animation; Done button still works for early exit.
        setTimeout(() => onClose(), 2500);
      } else {
        const data = await response.json().catch(() => ({}));
        addToast('error', data.detail || 'Failed to create alert');
      }
    } catch (error) {
      console.error('Create alert error:', error);
      addToast('error', 'Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const resendCode = async () => {
    // Re-use sendVerification; it will stay on 'verify' step (setStep('verify') is a no-op here)
    // because step is already 'verify' → no state change → useEffect([step]) does NOT re-run →
    // the countdown interval is NOT restarted automatically. We restart it manually here.
    await sendVerification();
    setResendCooldown(30);
    const interval = setInterval(() => {
      setResendCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center animate-fadeIn">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={step !== 'success' ? onClose : undefined}
      />
      
      {/* Panel */}
      <div className="relative w-full sm:max-w-md bg-white rounded-t-3xl sm:rounded-2xl overflow-hidden animate-slideUp sm:animate-scaleIn safe-bottom sm:m-4 shadow-2xl">
        {step === 'success' ? (
          /* Success State */
          <div className="px-6 py-12 text-center">
            <div className="relative mx-auto mb-6 h-20 w-20">
              {/* Animated rings */}
              <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" />
              <div className="absolute inset-2 rounded-full bg-emerald-500/30 animate-ping" style={{ animationDelay: '0.2s' }} />
              <div className="relative flex h-full w-full items-center justify-center rounded-full bg-emerald-500">
                <svg className="h-10 w-10 text-white animate-scaleIn" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <h2 className="font-display text-2xl font-bold text-gray-900">Alert Created!</h2>
            <p className="mt-2 text-gray-600">
              You'll receive SMS alerts for{' '}
              <span className="font-semibold">
                {REPORT_TYPES.find((t) => t.id === selectedReportType)?.name}
              </span>{' '}
              reports near this location.
            </p>
            <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-gray-100 px-4 py-2 text-sm text-gray-600">
              {/* Phone/SMS icon — not email; alerts are delivered via text message */}
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <span>SMS alerts will be sent to {userPhone}</span>
            </div>
            {/* Manual dismiss — don't make users wait for the 2.5s auto-close */}
            <button
              onClick={onClose}
              className="mt-6 w-full h-12 rounded-xl bg-gray-100 text-sm font-semibold text-gray-700 hover:bg-gray-200 active:scale-[0.98] transition-all"
            >
              Done
            </button>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="relative px-5 pt-5 pb-4 border-b border-gray-100">
              {/* Drag handle (mobile) */}
              <div className="absolute top-2 left-1/2 -translate-x-1/2 h-1 w-10 rounded-full bg-gray-300 sm:hidden" />
              
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-display text-xl font-bold text-gray-900">Create Alert</h2>
                  <p className="text-sm text-gray-500 truncate mt-0.5 max-w-[280px]">{address.split(',')[0]}</p>
                </div>
                <button
                  onClick={onClose}
                  className="h-10 w-10 rounded-xl bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
                  aria-label="Close"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Progress indicator */}
              <div className="flex gap-1.5 mt-4">
                {['phone', 'verify', 'create'].map((s, i) => (
                  <div
                    key={s}
                    className={`h-1 flex-1 rounded-full transition-colors ${
                      ['phone', 'verify', 'create'].indexOf(step) >= i
                        ? 'bg-primary'
                        : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="p-5">
              {step === 'phone' && (
                <div className="space-y-4">
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                      Phone Number
                    </label>
                    <input
                      id="phone"
                      type="tel"
                      value={userPhone}
                      onChange={(e) => setUserPhone(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && userPhone && !isLoading) {
                          sendVerification();
                        }
                      }}
                      placeholder="(555) 000-0000 or +1 555 000 0000"
                      className="w-full h-12 rounded-xl bg-gray-100 px-4 text-base text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary focus:outline-none transition-shadow"
                      autoFocus
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    US numbers accepted in any format — we'll send a verification code via SMS
                  </p>
                  <button
                    onClick={sendVerification}
                    disabled={!userPhone || isLoading}
                    className="w-full h-12 rounded-xl bg-primary font-display font-semibold text-primary-foreground shadow-lg shadow-primary/25 disabled:opacity-50 disabled:shadow-none active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Sending...</span>
                      </>
                    ) : (
                      'Continue'
                    )}
                  </button>
                </div>
              )}

              {step === 'verify' && (
                <div className="space-y-4">
                  <div>
                    <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-2">
                      Verification Code
                    </label>
                    <input
                      id="code"
                      type="text"
                      inputMode="numeric"
                      value={verificationCode}
                      onChange={(e) => {
                        const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                        setVerificationCode(val);
                        // Auto-submit when all 6 digits are entered — standard OTP UX
                        if (val.length === 6 && !isLoading) verifyCode(val);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && verificationCode.length === 6 && !isLoading) {
                          verifyCode();
                        }
                      }}
                      placeholder="000000"
                      className="w-full h-14 rounded-xl bg-gray-100 px-4 text-center text-2xl font-mono tracking-[0.5em] text-gray-900 placeholder:text-gray-300 focus:ring-2 focus:ring-primary focus:outline-none transition-shadow"
                      maxLength={6}
                      autoFocus
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    Enter the 6-digit code sent to {userPhone}
                  </p>
                  <button
                    onClick={() => verifyCode()}
                    disabled={verificationCode.length !== 6 || isLoading}
                    className="w-full h-12 rounded-xl bg-primary font-display font-semibold text-primary-foreground shadow-lg shadow-primary/25 disabled:opacity-50 disabled:shadow-none active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Verifying...</span>
                      </>
                    ) : (
                      'Verify'
                    )}
                  </button>
                  <div className="flex items-center justify-between gap-2">
                    <button
                      onClick={() => setStep('phone')}
                      className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      Use a different number
                    </button>
                    <button
                      onClick={resendCode}
                      disabled={resendCooldown > 0 || isLoading}
                      className="text-sm font-medium text-primary hover:text-primary/80 disabled:text-gray-400 disabled:cursor-default transition-colors"
                    >
                      {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                    </button>
                  </div>
                </div>
              )}

              {step === 'create' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Report Type
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {REPORT_TYPES.map((type) => (
                        <button
                          key={type.id}
                          onClick={() => !type.comingSoon && setSelectedReportType(type.id)}
                          disabled={type.comingSoon}
                          className={`relative flex items-center gap-2.5 p-3 rounded-xl text-left transition-all ${
                            type.comingSoon
                              ? 'bg-gray-50 cursor-not-allowed opacity-60'
                              : selectedReportType === type.id
                              ? 'bg-primary/10 ring-2 ring-primary'
                              : 'bg-gray-100 hover:bg-gray-200'
                          }`}
                        >
                          <span className={`text-lg ${type.comingSoon ? 'grayscale' : ''}`}>{type.icon}</span>
                          <span className="text-sm font-medium text-gray-900 leading-tight">{type.name}</span>
                          {type.comingSoon && (
                            <span className="absolute top-1.5 right-1.5 text-[9px] font-bold uppercase tracking-wide text-gray-400 bg-gray-200 rounded px-1 py-0.5 leading-none">
                              Soon
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {isDuplicate ? (
                    /* Duplicate-alert warning — informational only, creation is still allowed */
                    <div className="rounded-xl bg-sky-50 border border-sky-100 p-4 flex gap-3">
                      <span className="shrink-0 text-lg" aria-hidden="true">ℹ️</span>
                      <p className="text-sm text-sky-800">
                        You already have an active{' '}
                        <span className="font-semibold">
                          {REPORT_TYPES.find((t) => t.id === selectedReportType)?.name}
                        </span>{' '}
                        alert for this address. Creating another will send you duplicate SMS notifications.
                      </p>
                    </div>
                  ) : (
                    <div className="rounded-xl bg-amber-50 p-4">
                      <p className="text-sm text-amber-800">
                        <span className="font-semibold">You'll receive SMS alerts</span> when{' '}
                        <span className="font-semibold">
                          {REPORT_TYPES.find((t) => t.id === selectedReportType)?.name}
                        </span>{' '}
                        reports are filed near this location.
                      </p>
                    </div>
                  )}

                  <button
                    onClick={createAlert}
                    disabled={isLoading}
                    className="w-full h-12 rounded-xl bg-primary font-display font-semibold text-primary-foreground shadow-lg shadow-primary/25 disabled:opacity-50 disabled:shadow-none active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Creating...</span>
                      </>
                    ) : (
                      'Create Alert'
                    )}
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
