# Website QA workspace

The frontend uses Astro with a hydrated React workspace. Audit and responsive
preview are included at startup; report views load on demand. Existing FastAPI endpoints and PDF
exports are retained.

Requires Node.js 22.12 or newer.

```powershell
npm install
npm run dev
```

Open http://127.0.0.1:5173. Start the FastAPI backend on port 8000, or use
the existing `Start Website QA Agent.bat` launcher from the project root.

To use a different backend, copy `.env.example` to `.env` and set
`PUBLIC_API_URL`. Existing `VITE_API_URL` settings are also supported.
These variables are public browser configuration; do not put secrets in them.

```powershell
npm run build
npm run preview
```

Build regenerates `dist/`. Edit the source files, not generated build output.
