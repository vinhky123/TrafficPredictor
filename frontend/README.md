# Frontend — Next.js Dashboard

Interactive traffic monitoring dashboard built with Next.js, Leaflet, and Tailwind CSS. Deployed on Vercel.

## Tech Stack

| Layer | Tool |
|-------|------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5.9 |
| Styling | Tailwind CSS 4 |
| Map | Leaflet 1.9 (dynamic import, no SSR) |
| Icons | lucide-react |
| Deployment | Vercel |

## Features

- Interactive Leaflet map with traffic monitoring markers across Ho Chi Minh City.
- Location search and selection sidebar.
- Real-time speed display (km/h) with color-coded badges.
- Forecast panel showing 10-min and 60-min speed predictions via the backend API.
- Fully responsive dark-themed UI.

## Local Development

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | — |

## Deploy to Vercel

1. Push to GitHub.
2. Import the repo on [vercel.com](https://vercel.com).
3. Set **Root Directory** to `frontend`.
4. Set environment variable `NEXT_PUBLIC_API_URL` to your backend URL.
5. Deploy.
