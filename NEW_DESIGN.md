# Alert311 - New UI Design

## Overview

Complete redesign of Alert311 with a mobile-first, map-based interface inspired by modern apps like Uber, Airbnb, and Citizen.

## Design Philosophy

### Mobile-First
- Bottom sheets for mobile (native feel)
- Smooth transitions and animations
- Touch-optimized UI (48px+ tap targets)
- Safe area aware (iPhone notch support)

### Simple & Clean
- 3-step user flow: Search → View Location → Create Alert
- Minimal UI chrome - map takes center stage
- Clear visual hierarchy
- Generous whitespace

### Modern Stack
- **Framework:** Next.js 15 (App Router)
- **Styling:** Tailwind CSS v4
- **Components:** Custom (built on Radix UI primitives)
- **Icons:** Lucide React
- **Maps:** Mapbox GL + react-map-gl
- **Type-safe:** TypeScript

## Key Features

### 1. Search View
```
┌─────────────────────┐
│                     │
│    🔔 Alert311     │  ← Logo & branding
│                     │
│  Get notified about │  ← Clear value prop
│   issues near you   │
│                     │
│   🔍 [Search bar]   │  ← Prominent search
│   San Francisco only│  ← Context hint
│                     │
│     [Map bg]        │  ← Visual context
└─────────────────────┘
```

**Design Details:**
- Full-screen map background (dark theme)
- Centered vertical layout
- Glassmorphism search input
- Large, readable text
- Clear call-to-action

### 2. Location Selected View
```
┌─────────────────────┐
│ [×]  📍 123 Main St │  ← Top bar (dismissible)
│                     │
│     [Map view]      │  ← Full map
│                     │
│         [↻]         │  ← Recenter button
│                     │
│╭───────────────────╮│
││ ═══               ││  ← Drag handle
││ 123 Main Street   ││  ← Address
││                   ││
││ [+ Create Alert]  ││  ← Primary action
││                   ││
││ Recent Reports    ││  ← Context
││ • Report 1        ││
││ • Report 2        ││
│╰───────────────────╯│  ← Bottom sheet
└─────────────────────┘
```

**Design Details:**
- Minimal top bar (can scroll away)
- Map with marker and pulse animation
- Bottom sheet with drag handle
- CTA button prominent
- Reports list for context

### 3. Create Alert View
```
┌─────────────────────┐
│ [×]  Create Alert   │  ← Header
├─────────────────────┤
│ Location            │
│ 📍 123 Main Street  │  ← Read-only display
│                     │
│ Phone Number        │
│ (555) 123-4567 ___  │  ← Input
│ We'll text you...   │  ← Helper text
│                     │
│ 💡 How it works     │  ← Info card
│ You'll receive SMS  │
│ notifications...    │
│                     │
│ [🔔 Create Alert]   │  ← Submit
└─────────────────────┘
```

**Design Details:**
- Full-screen form (overlay)
- Clean, vertical layout
- Contextual help inline
- Large, accessible inputs
- Loading states

## Color Palette

### Primary Colors
```css
/* Emerald - Trust, Growth, Action */
--emerald-50: #ecfdf5
--emerald-500: #10b981  /* Primary CTA */
--emerald-600: #059669  /* Hover */

/* Neutral - Background, Text */
--neutral-50: #fafafa   /* Light bg */
--neutral-900: #171717  /* Primary text */
--neutral-950: #0a0a0a  /* Dark bg */
```

### Status Colors
```css
/* Amber - Open/Pending */
--amber-500: #f59e0b
--amber-600: #d97706

/* Red - Critical */
--red-500: #ef4444

/* Blue - Info */
--blue-500: #3b82f6
```

## Typography

### Font Scale
```css
/* Display */
text-4xl: 36px / 40px  /* Page titles */
text-xl:  20px / 28px  /* Section headers */

/* Body */
text-base: 16px / 24px /* Body text */
text-sm:   14px / 20px /* Secondary text */
text-xs:   12px / 16px /* Helper text */
```

### Font Weights
- **Bold (700)**: Headlines
- **Semibold (600)**: Buttons, labels
- **Medium (500)**: Body emphasis
- **Regular (400)**: Body text

## Component Library

### Current Stack (Keep)
✅ **Radix UI** - Headless primitives
- Dialog/Modal
- Dropdown
- Label
- Slot

✅ **Lucide React** - Icons
- Consistent style
- Tree-shakeable
- 1000+ icons

### Custom Components (Build)
Create these in `components/v2/`:

1. **Button** - Sizes, variants, states
2. **Input** - Text, tel, with validation
3. **BottomSheet** - Mobile drawer
4. **InfoCard** - Status/help messages
5. **ReportCard** - Report list item

### Why Not a Full UI Library?

**Considered:**
- ❌ Material UI - Too heavy, hard to customize
- ❌ Ant Design - Not mobile-first
- ❌ Chakra UI - Different philosophy

**Decided:**
- ✅ Custom components on Radix + Tailwind
  - Full design control
  - Minimal bundle size
  - Perfect for our simple UI
  - Easy to maintain

## Implementation Plan

### Phase 1: Core UI (This Week)
1. ✅ Create new page (`app/new/page.tsx`)
2. Build v2 components
3. Hook up to existing API
4. Add loading states
5. Error handling

### Phase 2: Features (Next Week)
6. Geocoding integration (Mapbox)
7. Real-time report updates
8. Report filtering
9. Share/deep links
10. PWA setup

### Phase 3: Polish (Week 3)
11. Animations and transitions
12. Skeleton loaders
13. Empty states
14. Success states
15. Accessibility audit

## File Structure

```
alert311/frontend/
├── app/
│   ├── new/
│   │   └── page.tsx          ← New design (prototype)
│   ├── page.tsx              ← Old design (keep for now)
│   └── layout.tsx
├── components/
│   ├── v2/                   ← New components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── BottomSheet.tsx
│   │   ├── InfoCard.tsx
│   │   └── ReportCard.tsx
│   └── [old components]
├── lib/
│   ├── api.ts               ← API client
│   └── utils.ts
└── styles/
    └── globals.css
```

## API Integration

### Endpoints Needed

```typescript
// 1. Geocoding (Mapbox)
GET https://api.mapbox.com/geocoding/v5/...
→ { address, lat, lng }

// 2. Create Alert
POST /api/alerts
{
  "address": "123 Main St",
  "lat": 37.7749,
  "lng": -122.4194,
  "phone": "+15551234567"
}
→ { id, status, ... }

// 3. Get Nearby Reports
GET /api/reports?lat=37.7749&lng=-122.4194&radius=500
→ [{ id, type, date, status, ... }]

// 4. Get Alert Status
GET /api/alerts/:id
→ { id, status, reports_sent, ... }
```

## Responsive Breakpoints

```css
/* Mobile First */
sm: 640px   /* Small tablets */
md: 768px   /* Tablets */
lg: 1024px  /* Small laptops */
xl: 1280px  /* Desktops */
```

### Layout Adaptations

**Mobile (< 768px):**
- Bottom sheet for reports
- Full-screen forms
- Stacked buttons
- Single column

**Desktop (≥ 768px):**
- Side panel for reports (right 400px)
- Modal for forms
- Horizontal button groups
- Multi-column where appropriate

## Accessibility

### WCAG 2.1 AA Compliance
- ✅ Color contrast 4.5:1 minimum
- ✅ Touch targets 44x44px minimum
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Focus indicators
- ✅ ARIA labels

### Testing Checklist
- [ ] VoiceOver (iOS)
- [ ] TalkBack (Android)
- [ ] Keyboard only navigation
- [ ] Color blind simulation
- [ ] Zoom to 200%

## Performance

### Targets
- **First Contentful Paint:** < 1.5s
- **Time to Interactive:** < 3.0s
- **Lighthouse Score:** > 90

### Optimizations
- Dynamic imports for map
- Image optimization (next/image)
- Font subsetting
- Code splitting
- CDN for static assets

## Next Steps

1. **Review this design** - Does it match your vision?
2. **Test the prototype** - Visit `/new` route
3. **Feedback on flow** - Any steps missing?
4. **Component priorities** - Which to build first?
5. **API work needed** - Any backend changes?

## Questions for David

1. Do we need user accounts/login?
2. Should users be able to view/manage multiple alerts?
3. Push notifications or SMS only?
4. Admin dashboard needed?
5. Analytics/tracking requirements?

---

**Live Preview:** `npm run dev` → http://localhost:3000/new

**Figma/Design:** Coming next (if you want detailed mockups)
