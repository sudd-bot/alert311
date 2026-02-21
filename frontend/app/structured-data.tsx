/**
 * JSON-LD structured data for Alert311
 * Improves SEO by providing search engines with structured information about the app
 */
import type { Metadata } from "next";

export function generateJsonLd(): object {
  return {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "Alert311",
    "description": "Get instant SMS alerts for 311 reports in San Francisco",
    "url": "https://alert311-ui.vercel.app",
    "applicationCategory": "UtilitiesApplication",
    "operatingSystem": "Web, iOS, Android",
    "browserRequirements": "Requires JavaScript. Requires HTML5.",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "featureList": [
      "Search for 311 reports near any address in San Francisco",
      "Get instant SMS alerts when new reports are filed nearby",
      "View report details including photos, status, and location",
      "Track multiple alert locations",
      "Real-time updates on report status"
    ],
    "provider": {
      "@type": "Organization",
      "name": "Alert311"
    }
  };
}
