'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Alert {
  id: number;
  address: string;
  latitude: number;
  longitude: number;
  report_type_id: string;
  active: boolean;
  created_at: string;
}

interface AlertListProps {
  alerts: Alert[];
  onClose: () => void;
  onAlertClick: (alert: Alert) => void;
}

export default function AlertList({ alerts, onClose, onAlertClick }: AlertListProps) {
  return (
    <Card className="fixed bottom-20 right-5 z-50 flex max-h-96 w-80 flex-col overflow-hidden bg-white shadow-lg">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-lg">My Alerts</CardTitle>
          <CardDescription>{alerts.length} active</CardDescription>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </Button>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-0">
        {alerts.length === 0 ? (
          <div className="p-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded bg-muted">
              <svg className="h-6 w-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <p className="text-sm font-medium">No alerts yet</p>
            <p className="mt-1 text-xs text-muted-foreground">Search for an address to create one</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <button
              key={alert.id}
              onClick={() => onAlertClick(alert)}
              className="w-full border-b border-border/50 px-5 py-4 text-left transition-colors last:border-b-0 hover:bg-accent"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{alert.address}</div>
                  <div className="mt-0.5 text-xs text-muted-foreground">{alert.report_type_id}</div>
                </div>
                <span
                  className={`rounded px-2 py-1 text-xs font-medium ${
                    alert.active
                      ? 'bg-green-100 text-green-700'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {alert.active ? 'Active' : 'Off'}
                </span>
              </div>
            </button>
          ))
        )}
      </CardContent>
    </Card>
  );
}
