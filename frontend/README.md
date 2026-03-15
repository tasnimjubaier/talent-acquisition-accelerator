# Talent Acquisition Accelerator - Frontend

Modern web interface for the AI-powered recruiting pipeline using Amazon Nova multi-agent system.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **State Management:** React Query + Zustand
- **Charts:** Recharts
- **Animations:** Framer Motion
- **HTTP Client:** Axios

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- AWS API Gateway endpoint (from backend deployment)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Update `.env.local` with your API Gateway URL:
```
NEXT_PUBLIC_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com
```

### Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:
```bash
npm run build
```

Start production server:
```bash
npm start
```

### Type Checking

Run TypeScript type checking:
```bash
npm run type-check
```

### Linting

Run ESLint:
```bash
npm run lint
```

## Project Structure

```
frontend/
├── app/                    # Next.js 14 app directory
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page (job posting)
│   ├── globals.css        # Global styles
│   └── providers.tsx      # React Query provider
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── layout/            # Layout components
│   ├── job/               # Job posting components
│   ├── workflow/          # Workflow dashboard components
│   ├── candidates/        # Candidate pipeline components
│   └── results/           # Results visualization components
├── lib/
│   ├── api.ts            # API client (Axios)
│   ├── types.ts          # TypeScript types
│   ├── utils.ts          # Helper functions
│   └── constants.ts      # Constants
├── hooks/                 # Custom React hooks
├── store/                 # Zustand store
└── public/               # Static assets
```

## Features

- **Job Posting Form** - Create job requirements
- **Workflow Dashboard** - Real-time agent status monitoring
- **Candidate Pipeline** - Visual candidate display with filtering
- **Results Visualization** - Charts, rankings, and recommendations
- **Cost Tracker** - Live AWS cost monitoring
- **Demo Mode** - Pre-configured scenarios for demos

## Environment Variables

- `NEXT_PUBLIC_API_URL` - AWS API Gateway endpoint
- `NEXT_PUBLIC_DEMO_MODE` - Enable demo mode (true/false)

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Configure environment variables
4. Deploy automatically

### Manual Deployment

```bash
npm run build
npm start
```

## Development Status

- ✅ Phase 7.1: Setup & Foundation (Complete)
- 📋 Phase 7.2: Core Components (TODO)
- 📋 Phase 7.3: API Integration (TODO)
- 📋 Phase 7.4: Styling & Polish (TODO)

## Related Documentation

- [Frontend Specification](../00_governing_docs/00_frontend_specification.md)
- [Backend README](../README.md)
- [Implementation Progress](../.kiro/steering/00_implementation_progress_tracker.md)

## License

MIT
