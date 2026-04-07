# FRONTEND ENGINEERING — Channel Docs

---

## #ui-development

The ASTRA frontend is the human face of everything we're building. The AI engine, the log pipeline, the RCA reports — all of that work needs to be presentable and usable by someone who isn't staring at a terminal. This channel is where we build that interface.

We're using React with Next.js. The reasoning: Next.js gives us server-side rendering when we need it, has a strong ecosystem, and handles routing cleanly. It's also the most common stack for teams building dashboards and internal tools right now, which means there's a lot of prior art to draw from.

**What belongs here:**
- Component design and architecture
- Page designs and layouts
- State management decisions and implementation
- UI library choices and component library discussions
- Accessibility considerations
- Performance optimization (bundle size, render performance, lazy loading)
- Design system and style guide decisions
- Code reviews for frontend PRs
- Browser compatibility issues

**Tech stack:**
```
Framework:      Next.js 14 (App Router)
Language:       TypeScript — strictly typed, no any unless absolutely necessary
Styling:        Tailwind CSS
UI Components:  shadcn/ui (built on Radix UI — accessible by default)
State:          React Query for server state, Zustand for client state
Charts:         Recharts (for incident timelines, metric graphs)
Formatting:     Prettier + ESLint
Testing:        Vitest + React Testing Library
```

**Application pages we're building:**

```
/                       Dashboard — system overview, active incidents, daily digest
/incidents              Incident list — all incidents, filterable by severity/status
/incidents/[id]         Incident detail — full incident thread, RCA report, timeline
/rca-reports            RCA report library — searchable, filterable
/rca-reports/[id]       Individual RCA report — full formatted report
/sprint-board           Task management — Kanban view synced with GitHub Projects
/analytics              Metrics and trends — incident frequency, RCA accuracy over time
/settings               Server configuration, team management
```

**Dashboard layout (main page):**
```
┌─────────────────────────────────────────────────────┐
│ ASTRA                            [System Status: 🟢] │
├─────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│ │ Active       │ │ Open Tasks   │ │ Avg RCA Time │  │
│ │ Incidents    │ │              │ │              │  │
│ │     0        │ │     4        │ │   6m 33s     │  │
│ └──────────────┘ └──────────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────┤
│ Recent Incidents                          [View All] │
│  INC-007  🔴 CRITICAL  EC2 Unresponsive   Resolved  │
│  INC-006  🟡 WARNING   High CPU           Resolved  │
├─────────────────────────────────────────────────────┤
│ Sprint Board                              [View All] │
│  In Progress (4)  |  Backlog (7)  |  Done (2)       │
│  Build RCA Engine → Bhargav                          │
│  API Auth Setup → Nithish                            │
├─────────────────────────────────────────────────────┤
│ EC2 Instance Health                                  │
│  [Metric chart — CPU, memory, disk over 24h]         │
└─────────────────────────────────────────────────────┘
```

**Component conventions:**

File structure:
```
src/
  app/                    Next.js App Router pages
    page.tsx              Dashboard
    incidents/
      page.tsx            Incident list
      [id]/page.tsx       Incident detail
  components/
    ui/                   shadcn/ui base components (don't modify these)
    incidents/            Incident-specific components
      IncidentCard.tsx
      IncidentTimeline.tsx
      SeverityBadge.tsx
    rca/                  RCA-specific components
      RcaReport.tsx
      ConfidenceScore.tsx
    layout/               App shell, sidebar, header
  lib/
    api.ts                API client (calls ASTRA backend)
    utils.ts              Shared utilities
  hooks/                  Custom React hooks
  types/                  TypeScript type definitions
```

Component naming:
- Components: PascalCase (`IncidentCard.tsx`)
- Hooks: camelCase with use prefix (`useIncidents.ts`)
- Utils: camelCase (`formatTimestamp.ts`)
- Types: PascalCase interface names (`type Incident = {...}`)

**How to post a component design for review:**
```
COMPONENT REVIEW | IncidentCard

Purpose:
  Displays a single incident in the incident list. Clickable, links to
  incident detail page.

Props:
  incident: Incident          — the incident data
  onSelect?: (id: string) => void   — optional click handler

Variants:
  Default: full card with all details
  Compact: just title + severity badge (for dashboard)

Design notes:
  Severity badge uses color from our design system:
  🔴 CRITICAL → red-600
  🟡 WARNING  → amber-500
  🔵 INFO     → blue-500

  Card shows: INC-007 | severity | title | service | time | status

Link to Figma/eraser.io design: [link]
Status: Ready for review
Owner: Sai Purna
```

**Rules:**
- TypeScript strict mode is on. No `any` types unless you can explain why in a comment.
- Every user-facing component needs at least one test.
- Accessibility is not optional. Use semantic HTML and ARIA where shadcn doesn't cover it.
- Don't add a new dependency without posting here first. Bundle size matters.
- Mobile responsiveness is required even for internal tools. People check dashboards on their phones.

---

## #deployment-pipeline

Getting the frontend from a local dev server to production involves more steps than most people realize. This channel is for the frontend-specific deployment pipeline — building, optimizing, and shipping the Next.js application to Vercel (production) and managing Streamlit demos.

**What belongs here:**
- Vercel deployment configuration and issues
- Environment variable management for the frontend
- Build performance (build times, bundle sizes)
- Streamlit demo setup and updates
- Preview deployment links (Vercel creates one per PR)
- Deployment failures and rollbacks
- CDN and caching configuration

**Deployment targets:**

```
Vercel (Production frontend):
  URL: https://astra.vercel.app (or custom domain)
  Branch: main → auto-deploys
  Environment: production
  Used for: live team use, demos, stakeholder access

Vercel (Preview):
  URL: https://astra-[branch]-aaryan778.vercel.app
  Branch: any PR → auto-deploys preview
  Used for: PR review, testing before merge

Streamlit (Demo environment):
  Used for: quickly demonstrating RCA reports, ML model outputs,
            data visualizations that are faster to build in Streamlit
            than in the full React app
  Hosted: Streamlit Community Cloud or local
```

**Environment variables (frontend):**

Variables needed in Vercel dashboard (not in code):
```
NEXT_PUBLIC_API_URL          URL of the ASTRA backend API
NEXT_PUBLIC_APP_ENV          production | staging | development
NEXT_PUBLIC_DISCORD_INVITE   Discord server invite link
```

Note: `NEXT_PUBLIC_` prefix means the variable is exposed to the browser.
Don't put secrets in `NEXT_PUBLIC_` variables — they're visible to anyone.

**Build optimization checklist:**
```
☐ Bundle size analyzed (run: next build && next-bundle-analyzer)
☐ Images using next/image (automatic optimization)
☐ Dynamic imports for heavy components (charts, large modals)
☐ No unused dependencies
☐ API calls cached appropriately with React Query
```

**Vercel deployment settings:**
```
Framework:       Next.js (auto-detected)
Build command:   npm run build
Output dir:      .next
Install command: npm ci
Node version:    20.x
```

**How to post a deployment:**
```
DEPLOY | Frontend v1.4.0 → Production

Date: April 7, 2024 at 15:30 UTC
Deployed by: Sai Purna
Vercel URL: https://astra.vercel.app

Changes in this deploy:
  - Added incident detail page (#incidents/[id])
  - Fixed severity badge color on dark backgrounds
  - Improved RCA report loading state
  - Bundle size reduced by 12KB (removed unused chart library)

Monitoring: Watching Vercel analytics for errors. All good so far.
Rollback plan: Vercel instant rollback to v1.3.2 if needed.
```

**Rules:**
- Every PR gets a Vercel preview deployment automatically. Share the preview URL in the PR description.
- Production deploys happen from `main` only. Never deploy a feature branch to production.
- If a production deploy causes errors, rollback immediately via Vercel dashboard and then investigate.
- Post here every time you deploy to production with a summary of what changed.

---

## #ux-and-design-feedback

Good engineering alone doesn't make a good product. The interface has to make sense to the people using it — not just to the person who built it. This channel is where we collect feedback on the UI, discuss design decisions, and make sure what we're building is actually usable.

We're using eraser.io for wireframes and flow diagrams. Post designs here before building them.

**What belongs here:**
- Wireframes and mockups for new pages or components
- Design feedback from team members
- User flow diagrams (how a user moves through the interface to accomplish a task)
- Accessibility review findings
- Usability feedback (things that are confusing, hard to use, or missing)
- Design system updates (new colors, typography changes, spacing changes)
- A/B testing results (if we run any)

**How to request design feedback:**
```
DESIGN REVIEW | Incident Detail Page

What I'm building:
  The page a user sees when they click on an incident. Shows the full
  incident thread, the RCA report, the timeline, and action buttons
  (close incident, create task from incident, view in GitHub).

Link to wireframe: [eraser.io link]

Specific questions:
  1. Is the timeline section clear enough? Should it be a vertical list
     or a horizontal timeline visualization?
  2. Should the RCA report be a collapsible section or always expanded?
  3. Where should the "Create Task" button live — top of page or at
     the end of the RCA report?

Feedback deadline: April 9 (need to start building by then)
Owner: Sai Purna
```

**Design system reference:**

Colors:
```
Brand:
  Primary:    #1E40AF (blue-800)
  Secondary:  #0F172A (slate-900)
  Accent:     #3B82F6 (blue-500)

Severity:
  Critical:   #DC2626 (red-600)
  Warning:    #D97706 (amber-600)
  Info:       #2563EB (blue-600)
  Success:    #16A34A (green-600)

Neutral:
  Background: #F8FAFC (slate-50)
  Surface:    #FFFFFF
  Border:     #E2E8F0 (slate-200)
  Text:       #0F172A (slate-900)
  Muted:      #64748B (slate-500)
```

Typography:
```
Font: Inter (system fallback: -apple-system, BlinkMacSystemFont, sans-serif)
Headings: font-weight: 700
Body: font-weight: 400
Code/monospace: JetBrains Mono
```

**Rules:**
- Don't build new pages without posting a wireframe here first. Building first and designing later wastes time.
- Feedback should be specific. "This looks weird" is not useful. "The severity badge is too small at mobile breakpoints" is.
- If you disagree with feedback, explain why. Design decisions should be discussable.
- Accessibility feedback gets the same priority as functional feedback.

---

## #staging-and-production

This channel is the final checkpoint before code reaches users. It's where we track what's in staging, what's in production, and manage the handoff between the two environments.

**What belongs here:**
- Current version running in each environment
- Environment differences that need attention
- Smoke test results for staging deployments
- Production health observations
- Environment-specific bug reports
- Rollback decisions and their rationale

**Environment status board (keep this pinned and updated):**
```
ENVIRONMENT STATUS — last updated April 7, 2024

PRODUCTION
  Version:    v1.3.2
  Deployed:   April 5 at 14:22 UTC
  Status:     🟢 Healthy
  URL:        https://astra.vercel.app
  API:        https://api.astra.internal/v1
  Ollama:     llama3:8b (production)

STAGING
  Version:    v1.4.0-rc1
  Deployed:   April 7 at 10:15 UTC
  Status:     🟡 Testing in progress
  URL:        https://astra-staging.vercel.app
  API:        https://staging-api.astra.internal/v1
  Ollama:     llama3:8b (staging)

DEVELOPMENT
  Version:    main branch (latest)
  Status:     🟢 Local dev environments
```

**Staging smoke test checklist:**
```
After every staging deployment, run through these manually:

Authentication:
  ☐ Can log in successfully
  ☐ Unauthorized routes redirect correctly

Dashboard:
  ☐ Dashboard loads without errors
  ☐ Incident count shows correctly
  ☐ Task count matches GitHub Projects

Incidents:
  ☐ Incident list loads
  ☐ Creating an incident via /incident command works in dev Discord
  ☐ Incident detail page loads
  ☐ RCA report displays correctly on incident detail page

Sprint Board:
  ☐ Task list loads and syncs with GitHub Projects
  ☐ /task create command creates a task
  ☐ /task status update reflects on board

General:
  ☐ No console errors on key pages
  ☐ Mobile layout not broken
  ☐ Response times acceptable (< 2s for page loads)

Smoke test passed by: [name]
Date: [date]
Issues found: [list or "none"]
```

**Rules:**
- Staging must pass the full smoke test checklist before promoting to production.
- Production version and status must be kept updated in the pinned environment status board.
- If you notice something wrong in production that wasn't in the staging test, document it here and create a bug task.
- Rollback decisions are made here. Post the reason and tag Aaryan before rolling back.
