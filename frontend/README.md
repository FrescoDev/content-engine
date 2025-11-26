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
- Script editing and refinement
  - AI-driven script refinement (tighten, casual, regenerate)
  - Manual script editing with auto-save
  - Hook selection for scripts
  - Platform-specific variants (YouTube Short, YouTube Long, TikTok)

## Scripts Functionality

The scripts view (`/scripts`) allows users to:
1. **View Topics with Content Options** - Browse approved topics with generated hooks and scripts
2. **Select Hooks** - Choose from multiple hook options for each script
3. **Edit Scripts** - Manually edit script content with auto-save
4. **Refine Scripts** - Use AI to refine scripts:
   - **Tighten**: Make scripts more concise
   - **Casual**: Adjust tone to be more conversational
   - **Regenerate**: Generate fresh wording while keeping core message
5. **Mark Ready** - Mark scripts as ready for publication
6. **Flag for Ethics Review** - Flag scripts that need ethics review

### API Endpoints

- `GET /api/options` - Fetch topics with content options
- `POST /api/scripts/refine` - Refine a script using AI
- `PUT /api/scripts/[option_id]` - Update script content manually
- `POST /api/options` - Mark script as ready or flag for ethics review

### Environment Variables

Create `.env.local` with:
```bash
OPENAI_API_KEY=your-key
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_DATABASE_ID=main-db
```

