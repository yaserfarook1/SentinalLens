# SentinelLens Frontend

AI-powered cost optimization dashboard for Microsoft Sentinel. Built with Next.js 14, React 18, and TypeScript.

## Features

- 🔐 **Entra ID Authentication** - Secure login with Azure AD via MSAL.js
- 📊 **Interactive Dashboard** - Monitor audit jobs and cost savings
- 🔍 **Advanced Reporting** - Detailed analysis with tabs and visualizations
- ✅ **Approval Workflow** - Secure tier migration approvals with MFA
- 📈 **Real-time Progress** - SSE-powered audit progress streaming
- 🎨 **Modern UI** - Responsive design with TailwindCSS

## Prerequisites

- Node.js 18+
- npm or yarn
- Azure tenant with appropriate permissions
- Backend API running on `http://localhost:8000`

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env.local`:

```bash
cp .env.example .env.local
```

Fill in your values:
- `NEXT_PUBLIC_TENANT_ID` - Your Azure AD tenant ID
- `NEXT_PUBLIC_CLIENT_ID` - Your app registration client ID
- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8000/api/v1)

### 3. Azure App Registration Setup

1. Go to Azure Portal → App registrations
2. Create new app registration named `SentinelLens-Frontend`
3. Set redirect URI: `http://localhost:3000/auth/redirect`
4. Grant permissions:
   - `api://SentinelLens/.default` (for backend API)
5. Copy the Client ID to `.env.local`

## Development

### Run Dev Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Home redirect
│   ├── layout.tsx         # Root layout with auth
│   ├── dashboard/         # Dashboard screen
│   ├── audit/
│   │   ├── new/           # New audit form
│   │   └── [jobId]/       # Job detail screens
│   │       ├── progress/  # Real-time progress
│   │       ├── report/    # Audit report
│   │       └── approve/   # Approval workflow
│   └── history/           # Search/filter audits
├── components/
│   ├── auth/              # Authentication components
│   ├── layout/            # Layout components
│   ├── report/            # Report display components
│   └── ui/                # Base UI components
├── lib/
│   ├── auth.ts            # MSAL configuration
│   ├── api-client.ts      # Typed API client
│   ├── types.ts           # TypeScript types
│   └── store.ts           # Zustand state (future)
├── hooks/                 # React hooks
├── styles/                # Global styles
└── public/                # Static assets
```

## Key Components

### Authentication

- **AuthProvider** - Wraps app with MSAL provider
- **ProtectedRoute** - Guards pages, redirects to login
- **useAuth** - Custom hook for auth state
- **useApi** - Custom hook for authenticated API calls

### Pages

- **Dashboard** - List of past audits with summary stats
- **New Audit** - Start new audit with workspace selection
- **Progress** - Real-time SSE progress streaming
- **Report** - Detailed audit results with tabs
- **Approve** - Tier migration approval workflow
- **History** - Search and filter all audits

### API Integration

The API client is auto-generated from FastAPI OpenAPI spec:

```typescript
const api = useApi(); // Get authenticated client

// List workspaces
const workspaces = await api.getWorkspaces();

// Start audit
const job = await api.startAudit({
  workspace_id: "xxx",
  days_lookback: 30
});

// Get report
const report = await api.getReport(job.job_id);

// Stream progress
await api.streamAuditProgress(
  job.job_id,
  (progress) => console.log(progress),
  () => console.log("complete"),
  (error) => console.error(error)
);

// Approve migration
await api.approveAudit(job.job_id, {
  job_id: job.job_id,
  selected_tables: ["Table1", "Table2"]
});
```

## Styling

Uses TailwindCSS with custom components in `components/ui/`:

- Button
- Card (Header, Title, Description, Content, Footer)
- Badge
- Tabs (List, Trigger, Content)
- LoadingSpinner

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_TENANT_ID` | Azure AD tenant ID | `00000000-0000-0000-0000-000000000000` |
| `NEXT_PUBLIC_CLIENT_ID` | App registration client ID | `11111111-1111-1111-1111-111111111111` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_DEBUG` | Enable debug logging | `false` |

## Security

- ✅ No secrets in code (all in Azure Key Vault)
- ✅ Entra ID authentication required
- ✅ MFA on approval workflow
- ✅ Security group enforcement for tier changes
- ✅ HTTPS only in production
- ✅ CORS restricted to backend

## Testing

```bash
npm run test
```

## Deployment

### Static Web Apps

```bash
# Build
npm run build

# Deploy to Azure Static Web Apps
# (via GitHub Actions or direct upload)
```

### Docker

```bash
# Build image
docker build -t sentinellens-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_TENANT_ID=xxx \
  -e NEXT_PUBLIC_CLIENT_ID=xxx \
  sentinellens-frontend
```

## Troubleshooting

### Login fails

- Check `NEXT_PUBLIC_TENANT_ID` and `NEXT_PUBLIC_CLIENT_ID`
- Verify redirect URI in App Registration
- Check browser console for errors

### API calls fail

- Verify backend is running (`http://localhost:8000/health`)
- Check `NEXT_PUBLIC_API_BASE_URL` matches backend
- Verify token has correct scopes

### SSE progress not streaming

- Check browser DevTools Network tab for EventSource connection
- Verify backend supports SSE headers
- Check backend logs for connection issues

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes
3. Run tests: `npm run test`
4. Commit: `git commit -am "Add feature"`
5. Push: `git push origin feature/name`
6. Create Pull Request

## License

MIT
