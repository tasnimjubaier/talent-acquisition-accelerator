# Frontend Setup Guide

## Phase 7.1 Complete ✅

The Next.js 14 project foundation has been created with all required configurations.

## What Was Created

### Configuration Files
- ✅ `package.json` - All dependencies configured
- ✅ `tsconfig.json` - TypeScript configuration
- ✅ `tailwind.config.ts` - Tailwind CSS with custom theme
- ✅ `next.config.js` - Next.js optimization settings
- ✅ `postcss.config.js` - PostCSS for Tailwind
- ✅ `.env.local.example` - Environment variable template
- ✅ `.gitignore` - Git ignore rules

### Core Application Files
- ✅ `app/layout.tsx` - Root layout with providers
- ✅ `app/page.tsx` - Home page (placeholder)
- ✅ `app/globals.css` - Global styles with Tailwind
- ✅ `app/providers.tsx` - React Query provider

### Library Files
- ✅ `lib/api.ts` - Axios API client with interceptors
- ✅ `lib/types.ts` - TypeScript type definitions
- ✅ `lib/utils.ts` - Helper functions (cn, formatters, etc.)
- ✅ `lib/constants.ts` - Constants (agent names, endpoints, etc.)

### Directory Structure
- ✅ `components/` - Component directories created
- ✅ `hooks/` - Custom hooks directory
- ✅ `store/` - Zustand store directory
- ✅ `public/` - Static assets directory

## Next Steps - Installation

### 1. Navigate to Frontend Directory

```bash
cd 00_ops/01_job/07_products/00_amazon_nova_hackathon/talent-acquisition-accelerator/frontend
```

### 2. Install Dependencies

```bash
npm install
```

This will install:
- React 18.3.1
- Next.js 14.2.0
- TypeScript 5.4.3
- Tailwind CSS 3.4.1
- React Query 5.28.0
- Zustand 4.5.2
- Axios 1.6.8
- Recharts 2.12.2
- Framer Motion 11.0.24
- Lucide React 0.363.0
- Radix UI components
- And all other dependencies

### 3. Create Environment File

```bash
cp .env.local.example .env.local
```

Then edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_DEMO_MODE=true
```

Note: Update `NEXT_PUBLIC_API_URL` with your actual API Gateway URL after AWS deployment.

### 4. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

### 5. Verify Setup

You should see:
- ✅ No TypeScript errors
- ✅ Tailwind CSS working
- ✅ Page loads successfully
- ✅ "Phase 7.1 Setup Complete ✓" message

## Available Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
frontend/
├── app/                          # Next.js 14 app directory
│   ├── layout.tsx               # Root layout with providers
│   ├── page.tsx                 # Home page
│   ├── globals.css              # Global styles
│   └── providers.tsx            # React Query provider
├── components/
│   └── ui/                      # shadcn/ui components (to be added)
├── lib/
│   ├── api.ts                   # API client (Axios)
│   ├── types.ts                 # TypeScript types
│   ├── utils.ts                 # Helper functions
│   └── constants.ts             # Constants
├── hooks/                       # Custom React hooks (to be added)
├── store/                       # Zustand store (to be added)
├── public/                      # Static assets
├── package.json                 # Dependencies
├── tsconfig.json                # TypeScript config
├── tailwind.config.ts           # Tailwind config
├── next.config.js               # Next.js config
├── postcss.config.js            # PostCSS config
└── .env.local.example           # Environment variables template
```

## What's Next - Phase 7.2

After installation, we'll create:
1. shadcn/ui base components (Button, Card, Input, etc.)
2. Layout components (Header, Footer)
3. Job posting form component
4. Workflow dashboard components
5. Candidate pipeline components
6. Results visualization components

## Troubleshooting

### Port 3000 Already in Use
```bash
# Use a different port
npm run dev -- -p 3001
```

### TypeScript Errors
```bash
# Run type checking
npm run type-check
```

### Tailwind Not Working
```bash
# Rebuild
rm -rf .next
npm run dev
```

### Module Not Found
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## Tech Stack Summary

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5.4
- **Styling:** Tailwind CSS 3.4
- **UI Library:** shadcn/ui (Radix UI)
- **State:** React Query 5 + Zustand 4
- **Charts:** Recharts 2
- **Animation:** Framer Motion 11
- **HTTP:** Axios 1.6
- **Icons:** Lucide React

## Documentation

- [Next.js Docs](https://nextjs.org/docs)
- [React Query Docs](https://tanstack.com/query/latest)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [shadcn/ui Docs](https://ui.shadcn.com/)
- [Frontend Specification](../00_governing_docs/00_frontend_specification.md)

---

**Status:** Phase 7.1 Complete ✅  
**Next:** Install dependencies and proceed to Phase 7.2
