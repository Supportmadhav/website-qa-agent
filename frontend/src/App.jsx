import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";

import {
  AlertCircle,
  Check,
  ChevronDown,
  ClipboardCheck,
  Globe2,
  MonitorSmartphone,
  ScanSearch,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";

import ResponsivePreviewStudio from "./components/ResponsivePreviewStudio.jsx";
import WebsiteAudit from "./components/WebsiteAudit.jsx";
import ViewErrorBoundary from "./components/ViewErrorBoundary.jsx";

const ReportPanel = lazy(() => import("./components/ReportPanel.jsx"));

import { CHECKS } from "./data/checks";

import { runSelectedScan } from "./services/api";

const CHECK_DESCRIPTIONS = {
  page_speed: "Performance timing, page weight and slow resources.",

  page_link_list: "Review the names, destinations and status of page links.",

  website_page_list:
    "Discover same-site HTML pages with page number, title and URL.",

  links: "Find working, blocked and broken links.",

  images: "Image URLs, sizes, formats, ALT and optimization.",

  meta: "SEO metadata, social tags and structured data.",

  sticky_header: "Sticky header behavior and overlap checks.",

  css_animation: "Animations, transitions and reduced-motion support.",

  browser_compatibility: "Chrome, Firefox and Edge checks.",

  google_translate: "Google Translate presence and functional verification.",

  whatsapp: "WhatsApp link format and configuration.",

  social_media: "Social links, targets and consistency.",

  contact_form: "Fields, labels, required values and anti-spam.",

  blog: "Blog archive, posts, images and pagination.",

  content: "Visible website content and spelling analysis.",

  layout_design: "Text, clipping, image distortion and CTA sizing.",
};

export default function App() {
  const [activeWorkspace, setActiveWorkspace] = useState("testing");

  const [url, setUrl] = useState("");

  const [selected, setSelected] = useState(() => new Set());

  const [loading, setLoading] = useState(false);

  const [report, setReport] = useState(null);

  const [error, setError] = useState("");
  const [checksOpen, setChecksOpen] = useState(false);
  const selectorRef = useRef(null);

  useEffect(() => {
    if (!checksOpen) return;
    function closeSelector(event) {
      if (event.type === "keydown") {
        if (event.key === "Escape") {
          setChecksOpen(false);
          selectorRef.current?.querySelector(".qa-selector-trigger")?.focus();
        }
      } else if (!selectorRef.current?.contains(event.target)) {
        setChecksOpen(false);
      }
    }
    document.addEventListener("pointerdown", closeSelector);
    document.addEventListener("keydown", closeSelector);
    return () => {
      document.removeEventListener("pointerdown", closeSelector);
      document.removeEventListener("keydown", closeSelector);
    };
  }, [checksOpen]);

  const selectedChecks = useMemo(
    () => CHECKS.filter((check) => selected.has(check.id)),
    [selected],
  );

  const canRun = Boolean(url.trim() && selected.size > 0 && !loading);

  function toggleCheck(checkId) {
    if (loading) {
      return;
    }

    setSelected((current) => {
      const next = new Set(current);

      if (next.has(checkId)) {
        next.delete(checkId);
      } else {
        next.add(checkId);
      }

      return next;
    });
  }

  function selectAllChecks() {
    if (loading) {
      return;
    }

    setSelected(new Set(CHECKS.map((check) => check.id)));
  }

  function clearSelected() {
    if (loading) {
      return;
    }

    setSelected(new Set());
  }

  async function runScan() {
    if (!canRun) {
      return;
    }

    setChecksOpen(false);
    setLoading(true);

    setError("");
    setReport(null);

    try {
      const checks = selectedChecks.map((check) => check.id);

      const result = await runSelectedScan(url, checks);

      setReport(result);
    } catch (scanError) {
      setError(scanError.message || "The scan could not be completed.");
    } finally {
      setLoading(false);
    }
  }

  const [query, setQuery] = useState("");
  const workspaces = [
    { id: "testing", label: "QA Testing", icon: ScanSearch },
    { id: "audit", label: "Website Audit", icon: ClipboardCheck },
    { id: "responsive", label: "Responsive Studio", icon: MonitorSmartphone },
  ];
  const visibleChecks = CHECKS.filter((check) =>
    `${check.label} ${check.category}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <div className="qa-shell">
      <a className="skip-link" href="#workspace">
        Skip to workspace
      </a>
      <aside className="qa-sidebar no-print">
        <a className="qa-brand" href="/">
          <span className="qa-brand-icon">
            <ScanSearch size={24} />
          </span>
          <span>
            Website QA<span className="qa-brand-subtitle">AGENT WORKSPACE</span>
          </span>
        </a>
        <p className="qa-nav-label">WORKSPACE</p>
        <nav aria-label="Workspaces">
          {workspaces.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={`qa-nav-item ${activeWorkspace === id ? "is-active" : ""}`}
              aria-current={activeWorkspace === id ? "page" : undefined}
              onClick={() => setActiveWorkspace(id)}
            >
              <Icon size={19} />
              <span>{label}</span>
              {activeWorkspace === id && <span className="qa-nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="qa-profile">
          <span>QA</span>
          <div>
            <strong>Local workspace</strong>
            <small>Your website testing toolkit</small>
          </div>
        </div>
      </aside>
      <div className="qa-main">
        <header className="qa-topbar no-print">
          <span>
            Workspace <span className="qa-slash">/</span>{" "}
            <strong>
              {workspaces.find((w) => w.id === activeWorkspace).label}
            </strong>
          </span>
          <span className="qa-local">
            <span /> Local environment
          </span>
        </header>
        <main id="workspace" tabIndex={-1}>
          <ViewErrorBoundary key={activeWorkspace}>
            <Suspense
              fallback={
                <div className="qa-loading" role="status">
                  Loading workspace…
                </div>
              }
            >
              {activeWorkspace === "testing" ? (
                <div className="qa-content">
                  <div className="qa-page-heading qa-compact-heading">
                    <h1>QA Testing</h1>
                    <span className="qa-check-total">
                      {CHECKS.length} available checks
                    </span>
                  </div>
                  <section
                    className="qa-scan-toolbar no-print"
                    aria-label="Scan setup"
                  >
                    <form
                      onSubmit={(event) => {
                        event.preventDefault();
                        runScan();
                      }}
                    >
                      <div className="qa-toolbar-row">
                        <div className="qa-url-control">
                          <label htmlFor="website-url">Website URL</label>
                          <div className="qa-url-field">
                            <Globe2 size={18} />
                            <input
                              id="website-url"
                              inputMode="url"
                              autoComplete="url"
                              placeholder="https://example.com"
                              value={url}
                              disabled={loading}
                              onChange={(event) => setUrl(event.target.value)}
                              required
                            />
                          </div>
                        </div>
                        <div className="qa-selector" ref={selectorRef}>
                          <span className="qa-control-label" id="checks-label">
                            QA checks
                          </span>
                          <button
                            type="button"
                            className="qa-selector-trigger"
                            aria-expanded={checksOpen}
                            aria-controls="qa-check-picker"
                            disabled={loading}
                            onClick={() => setChecksOpen(!checksOpen)}
                          >
                            <ShieldCheck size={17} />
                            <span>
                              {selected.size
                                ? `${selected.size} selected`
                                : "Choose checks"}
                            </span>
                            <ChevronDown size={16} />
                          </button>
                          {checksOpen && (
                            <div
                              id="qa-check-picker"
                              className="qa-check-picker"
                              role="region"
                              aria-labelledby="checks-label"
                            >
                              <div className="qa-picker-heading">
                                <strong>Choose QA checks</strong>
                                <button
                                  type="button"
                                  aria-label="Close check selector"
                                  onClick={() => setChecksOpen(false)}
                                >
                                  <X size={18} />
                                </button>
                              </div>
                              <div className="qa-search">
                                <Search size={17} />
                                <input
                                  autoFocus
                                  aria-label="Search QA checks"
                                  placeholder="Find a check…"
                                  value={query}
                                  onChange={(event) =>
                                    setQuery(event.target.value)
                                  }
                                />
                                {query && (
                                  <button
                                    type="button"
                                    aria-label="Clear search"
                                    onClick={() => setQuery("")}
                                  >
                                    <X size={16} />
                                  </button>
                                )}
                              </div>
                              <div className="qa-picker-actions">
                                <span>
                                  {selected.size} of {CHECKS.length} selected
                                </span>
                                <button
                                  type="button"
                                  onClick={selectAllChecks}
                                  disabled={selected.size === CHECKS.length}
                                >
                                  Select all
                                </button>
                                <button
                                  type="button"
                                  onClick={clearSelected}
                                  disabled={!selected.size}
                                >
                                  Clear
                                </button>
                              </div>
                              <div className="qa-picker-list">
                                {visibleChecks.map((check) => {
                                  const Icon = check.icon;
                                  const checked = selected.has(check.id);
                                  return (
                                    <button
                                      type="button"
                                      key={check.id}
                                      className={`qa-check-option ${checked ? "is-selected" : ""}`}
                                      aria-pressed={checked}
                                      onClick={() => toggleCheck(check.id)}
                                      title={CHECK_DESCRIPTIONS[check.id]}
                                    >
                                      <Icon size={17} />
                                      <span>{check.label}</span>
                                      <span
                                        className="qa-checkbox"
                                        aria-hidden="true"
                                      >
                                        {checked && (
                                          <Check size={12} strokeWidth={3} />
                                        )}
                                      </span>
                                    </button>
                                  );
                                })}
                                {!visibleChecks.length && (
                                  <p className="qa-no-results">
                                    No checks match “{query}”.
                                  </p>
                                )}
                              </div>
                              <button
                                type="button"
                                className="qa-picker-done"
                                onClick={() => setChecksOpen(false)}
                              >
                                Done
                              </button>
                            </div>
                          )}
                        </div>
                        <button
                          className="qa-run-button"
                          type="submit"
                          disabled={!canRun}
                        >
                          {loading ? (
                            <>
                              <span className="qa-spinner" /> Scanning…
                            </>
                          ) : (
                            <>
                              <ScanSearch size={18} /> Run scan
                            </>
                          )}
                        </button>
                      </div>
                      <div className="qa-toolbar-summary">
                        {selected.size ? (
                          <span
                            title={selectedChecks
                              .map((check) => check.label)
                              .join(", ")}
                          >
                            {selectedChecks
                              .map((check) => check.label)
                              .join(" · ")}
                          </span>
                        ) : (
                          <span>
                            Select one or more checks to start a scan.
                          </span>
                        )}
                        {!!selected.size && (
                          <button
                            type="button"
                            onClick={clearSelected}
                            disabled={loading}
                          >
                            Clear selection
                          </button>
                        )}
                      </div>
                    </form>
                  </section>
                  {error && (
                    <div className="qa-error" role="alert">
                      <AlertCircle size={18} />
                      {error}
                    </div>
                  )}
                  <section
                    className="qa-results"
                    aria-label="Scan results"
                    aria-live="polite"
                    aria-busy={loading}
                  >
                    {loading ? (
                      <div className="qa-loading">
                        <span className="qa-spinner" />
                        <h2>Your scan is in progress</h2>
                        <p>
                          Checking {selected.size}{" "}
                          {selected.size === 1 ? "area" : "areas"} of your
                          website. Keep this workspace open.
                        </p>
                      </div>
                    ) : report ? (
                      <ReportPanel report={report} />
                    ) : (
                      <div className="qa-empty">
                        <ClipboardCheck size={24} />
                        <div>
                          <h2>Your report will appear here</h2>
                          <p>
                            Enter a URL, choose your checks, and run a scan.
                          </p>
                        </div>
                      </div>
                    )}
                  </section>
                </div>
              ) : activeWorkspace === "audit" ? (
                <WebsiteAudit />
              ) : (
                <ResponsivePreviewStudio />
              )}
            </Suspense>
          </ViewErrorBoundary>
        </main>
      </div>
    </div>
  );
}
