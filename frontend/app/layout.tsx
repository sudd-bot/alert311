import type { Metadata, Viewport } from "next";
import { DM_Sans, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/Toast";

const dmSans = DM_Sans({ 
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700"],
});

const ibmPlex = IBM_Plex_Sans({ 
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Alert311 - SF 311 Report Alerts",
  description: "Get instant SMS alerts for 311 reports in San Francisco",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Alert311",
  },
  openGraph: {
    title: "Alert311 - SF 311 Report Alerts",
    description: "Get instant SMS alerts for 311 reports in San Francisco",
    url: "https://alert311-ui.vercel.app",
    siteName: "Alert311",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary",
    title: "Alert311 - SF 311 Report Alerts",
    description: "Get instant SMS alerts for 311 reports in San Francisco",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${dmSans.variable} ${ibmPlex.variable} font-body antialiased`}>
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
