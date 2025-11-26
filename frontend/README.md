# Content Engine Frontend

Next.js frontend for the Content Engine AI Production Console.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure Firebase in `lib/firebase.ts` (add your Firebase config).

3. Run development server:
```bash
npm run dev
```

## Project Structure

- `app/` - Next.js App Router pages
  - `today/` - Topic review view
  - `scripts/` - Script review view
  - `integrity/` - Ethics review view
  - `history/` - Audit trail view
  - `performance/` - Performance metrics view
- `components/` - React components
  - `layout/` - Layout components (AppShell)
  - `views/` - View components
  - `ui/` - shadcn/ui components
- `lib/` - Utilities and Firebase setup

## Features

- Dark mode UI
- Responsive design (mobile-friendly)
- Keyboard shortcuts for efficient review
- Real-time updates from Firestore
- Audit trail visualization

