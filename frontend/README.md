# Alert311 Frontend

Modern, map-based UI for creating and managing 311 report alerts in San Francisco.

## Features

- 🗺️ **Full-screen Mapbox map** - Interactive map locked to San Francisco
- 🔍 **Address search** - Geocoding with Mapbox to find any SF address
- 🚨 **Create alerts** - Set up SMS notifications for specific addresses
- 📱 **Phone verification** - Secure SMS verification via Twilio
- 📍 **Alert management** - View and manage all your active alerts
- 🎨 **Modern UI** - Minimalist floating panels, clean design

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe code
- **Tailwind CSS** - Utility-first styling
- **React Map GL** - Mapbox GL integration
- **Mapbox GL** - Interactive maps

## Getting Started

### Prerequisites

- Node.js 18+
- Mapbox API token
- Backend API running

### Install Dependencies

```bash
npm install
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
NEXT_PUBLIC_API_URL=https://www.alert311.com
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
npm start
```

## How It Works

1. **Search** - Enter a San Francisco address in the search box
2. **Create Alert** - Click on the map or select from search results
3. **Verify Phone** - Enter your phone number and verification code
4. **Choose Report Type** - Select what type of 311 reports to monitor
5. **Get Notified** - Receive SMS when matching reports are filed

## Deployment

### Deploy to Vercel

```bash
vercel
```

Make sure to add environment variables in Vercel dashboard:
- `NEXT_PUBLIC_MAPBOX_TOKEN`
- `NEXT_PUBLIC_API_URL`

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx          # Main map page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── AddressSearch.tsx # Search box with geocoding
│   ├── AlertPanel.tsx    # Create/edit alert form
│   └── AlertList.tsx     # List of user alerts
└── public/               # Static assets
```

## UI Components

### AddressSearch
Floating search box (top-left) with:
- Real-time geocoding via Mapbox
- Dropdown results with full addresses
- SF-bounded search

### AlertPanel
Modal form (center) for:
- Phone number entry
- SMS verification
- Report type selection
- Alert creation

### AlertList
Floating panel (bottom-right) showing:
- All user alerts
- Active/inactive status
- Click to zoom to location

## Styling

- **Map**: Dark theme (Mapbox dark-v11)
- **Panels**: White with rounded corners and shadows
- **Markers**: Blue (selected), Green (alerts)
- **Animations**: Smooth transitions and bouncing markers

## API Integration

Connects to backend at `NEXT_PUBLIC_API_URL`:

- `POST /auth/register` - Send verification SMS
- `POST /auth/verify` - Verify phone number
- `POST /alerts` - Create new alert
- `GET /alerts` - List user alerts (TODO)

## TODO

- [ ] Fetch existing alerts from API
- [ ] Edit/delete alerts
- [ ] Multiple report type selection
- [ ] Custom alert radius (currently exact address match)
- [ ] Push notifications (via service worker)
- [ ] Dark mode toggle
- [ ] Mobile optimization
- [ ] Alert history/stats

## License

MIT
