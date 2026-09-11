import {
  useMemo,
  useState,
} from "react";

import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock3,
  Download,
  ExternalLink,
  FileSearch,
  Globe2,
  LoaderCircle,
  Search,
  ShieldAlert,
  Sparkles,
  Target,
  TriangleAlert,
  XCircle,
} from "lucide-react";

import {
  jsPDF,
} from "jspdf";

import autoTable from "jspdf-autotable";

import {
  runWebsiteAudit,
} from "../services/api";


const STATUS_STYLES = {
  passed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
  failed: "border-rose-200 bg-rose-50 text-rose-700",
};


const SEVERITY_STYLES = {
  critical: "border-rose-300 bg-rose-100 text-rose-800",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-sky-200 bg-sky-50 text-sky-700",
  info: "border-slate-200 bg-slate-50 text-slate-600",
};


function scoreTone(score) {
  if (score >= 90) {
    return {
      accent: "#10b981",
      text: "text-emerald-600",
      background: "bg-emerald-50",
    };
  }

  if (score >= 70) {
    return {
      accent: "#3b82f6",
      text: "text-blue-600",
      background: "bg-blue-50",
    };
  }

  if (score >= 50) {
    return {
      accent: "#f59e0b",
      text: "text-amber-600",
      background: "bg-amber-50",
    };
  }

  return {
    accent: "#ef4444",
    text: "text-rose-600",
    background: "bg-rose-50",
  };
}


function humanize(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}


function displayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not detected";
  }

  return String(value);
}


function safeFilename(value) {
  return String(value || "website")
    .toLowerCase()
    .replace(/[^a-z0-9.-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || "website";
}


function downloadAuditPdf(report) {
  const doc = new jsPDF({
    unit: "pt",
    format: "a4",
  });

  const margin = 42;
  const pageWidth = doc.internal.pageSize.getWidth();

  doc.setFillColor(15, 23, 42);
  doc.rect(0, 0, pageWidth, 122, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(20);
  doc.setFont("helvetica", "bold");
  doc.text("Website Audit Report", margin, 45);
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text(report.url || report.domain || "", margin, 66, {
    maxWidth: pageWidth - (margin * 2),
  });
  doc.text(
    `Audit ${report.audit_id || ""}  |  ${report.pages_crawled || 0} page(s)  |  ${report.duration_seconds || 0}s`,
    margin,
    88
  );
  doc.setFontSize(25);
  doc.setFont("helvetica", "bold");
  doc.text(`${report.overall_score ?? 0}/100`, pageWidth - margin, 56, {
    align: "right",
  });
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text(report.overall_label || "", pageWidth - margin, 76, {
    align: "right",
  });

  doc.setTextColor(15, 23, 42);
  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text("Executive summary", margin, 154);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  const summaryLines = doc.splitTextToSize(
    report.executive_summary || "No executive summary was generated.",
    pageWidth - (margin * 2)
  );
  doc.text(summaryLines, margin, 172);

  let nextY = 186 + (summaryLines.length * 10);

  autoTable(doc, {
    startY: nextY,
    head: [["Module", "Score", "Passed", "Warnings", "Failed"]],
    body: (report.modules || []).map((module) => [
      module.module,
      `${module.score}/100`,
      module.passed,
      module.warning,
      module.failed,
    ]),
    theme: "grid",
    headStyles: {
      fillColor: [30, 64, 175],
      fontSize: 8,
    },
    bodyStyles: {
      fontSize: 8,
      cellPadding: 5,
    },
    margin: {
      left: margin,
      right: margin,
    },
  });

  nextY = (doc.lastAutoTable?.finalY || nextY) + 24;

  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text("Audit findings", margin, nextY);

  autoTable(doc, {
    startY: nextY + 10,
    head: [["Module", "Test", "Severity", "Status", "Recommendation"]],
    body: (report.issues || []).map((issue) => [
      issue.module,
      issue.test_name,
      humanize(issue.severity),
      humanize(issue.status),
      issue.recommendation,
    ]),
    theme: "striped",
    headStyles: {
      fillColor: [15, 23, 42],
      fontSize: 7,
    },
    bodyStyles: {
      fontSize: 7,
      cellPadding: 4,
      valign: "top",
    },
    columnStyles: {
      0: { cellWidth: 58 },
      1: { cellWidth: 90 },
      2: { cellWidth: 48 },
      3: { cellWidth: 48 },
    },
    margin: {
      left: margin,
      right: margin,
    },
  });

  doc.save(
    `${safeFilename(report.domain)}-website-audit.pdf`
  );
}


function ScoreRing({
  score,
  label,
}) {
  const tone = scoreTone(score);

  return (
    <div
      className="relative flex h-40 w-40 items-center justify-center rounded-full p-3 shadow-2xl"
      style={{
        background:
          `conic-gradient(${tone.accent} ${Math.max(0, Math.min(100, score)) * 3.6}deg, rgba(255,255,255,0.14) 0deg)`,
      }}
    >
      <div className="flex h-full w-full flex-col items-center justify-center rounded-full bg-slate-950">
        <span className="text-4xl font-black tracking-tight text-white">
          {score}
        </span>
        <span className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
          out of 100
        </span>
        <span className="mt-2 rounded-full border border-white/10 bg-white/10 px-3 py-1 text-[10px] font-bold text-white">
          {label}
        </span>
      </div>
    </div>
  );
}


function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
  style,
}) {
  return (
    <div className={`rounded-2xl border p-4 ${style}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/80 shadow-sm">
          <Icon size={17} />
        </span>
        <span className="text-2xl font-black tracking-tight">
          {value}
        </span>
      </div>
      <p className="mt-3 text-xs font-bold uppercase tracking-[0.1em]">
        {label}
      </p>
      <p className="mt-1 text-[10px] opacity-70">
        {detail}
      </p>
    </div>
  );
}


function PriorityList({
  title,
  subtitle,
  items,
  icon: Icon,
  style,
}) {
  return (
    <section className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)]">
      <div className="flex items-start gap-3">
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${style}`}>
          <Icon size={18} />
        </span>
        <div>
          <h3 className="font-display text-base font-bold text-slate-950">
            {title}
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            {subtitle}
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {items?.length ? items.map((item, index) => (
          <div
            key={`${item.module}-${item.test_name}-${index}`}
            className="rounded-xl border border-slate-100 bg-slate-50 p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">
                {item.module}
              </span>
              <span className={`rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase ${SEVERITY_STYLES[item.severity] || SEVERITY_STYLES.info}`}>
                {item.severity}
              </span>
            </div>
            <p className="mt-2 text-sm font-bold text-slate-900">
              {item.test_name}
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              {item.recommendation}
            </p>
          </div>
        )) : (
          <div className="rounded-xl border border-dashed border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-700">
            No items in this priority group.
          </div>
        )}
      </div>
    </section>
  );
}


export default function WebsiteAudit() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState(null);
  const [moduleFilter, setModuleFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("actionable");
  const [search, setSearch] = useState("");

  const filteredIssues = useMemo(() => {
    const query = search.trim().toLowerCase();

    return (report?.issues || []).filter((issue) => {
      if (moduleFilter !== "all" && issue.module !== moduleFilter) {
        return false;
      }

      if (severityFilter !== "all" && issue.severity !== severityFilter) {
        return false;
      }

      if (statusFilter === "actionable" && issue.status === "passed") {
        return false;
      }

      if (statusFilter !== "all" && statusFilter !== "actionable" && issue.status !== statusFilter) {
        return false;
      }

      if (!query) {
        return true;
      }

      return [
        issue.module,
        issue.test_name,
        issue.current_value,
        issue.expected_value,
        issue.recommendation,
      ].some((value) => String(value || "").toLowerCase().includes(query));
    });
  }, [
    report,
    moduleFilter,
    severityFilter,
    statusFilter,
    search,
  ]);

  async function runAudit(event) {
    event.preventDefault();

    if (!url.trim() || loading) {
      return;
    }

    setLoading(true);
    setError("");
    setReport(null);

    try {
      const result = await runWebsiteAudit(url.trim());
      setReport(result);
    } catch (caughtError) {
      setError(
        caughtError.message
        ||
        "The website audit could not be completed."
      );
    } finally {
      setLoading(false);
    }
  }

  const basicEntries = report
    ? Object.entries(report.basic || {})
    : [];

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <section className="relative overflow-hidden rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.25),transparent_34%),linear-gradient(135deg,#020617_0%,#0f172a_48%,#134e4a_100%)] p-6 text-white shadow-[0_26px_76px_rgba(15,23,42,0.24)] sm:p-8 lg:p-10">
        <div className="relative z-10 grid gap-8 lg:grid-cols-[1fr_1.05fr] lg:items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-200">
              <Activity size={13} />
              Complete health audit
            </span>
            <h1 className="mt-5 max-w-2xl font-display text-3xl font-bold tracking-[-0.04em] text-white sm:text-4xl">
              Audit your entire website in one report
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              Crawl priority pages, score seven core modules, identify high-impact issues, and turn the results into a prioritized action plan.
            </p>
          </div>

          <form
            onSubmit={runAudit}
            className="rounded-2xl border border-white/10 bg-white/10 p-3 shadow-2xl backdrop-blur-xl"
          >
            <label className="text-[10px] font-bold uppercase tracking-[0.13em] text-emerald-100/70">
              Website URL
            </label>
            <div className="mt-2 flex flex-col gap-3 sm:flex-row">
              <div className="relative min-w-0 flex-1">
                <Globe2
                  size={16}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="text"
                  value={url}
                  disabled={loading}
                  onChange={(event) => setUrl(event.target.value)}
                  placeholder="https://example.com"
                  className="h-12 w-full rounded-xl border-0 bg-white pl-11 pr-4 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:ring-4 focus:ring-emerald-300/30 disabled:opacity-60"
                />
              </div>
              <button
                type="submit"
                disabled={!url.trim() || loading}
                className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-500 px-6 text-sm font-bold text-slate-950 shadow-[0_12px_28px_rgba(16,185,129,0.3)] transition hover:-translate-y-0.5 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0"
              >
                {loading ? (
                  <>
                    <LoaderCircle size={16} className="animate-spin" />
                    Auditing
                  </>
                ) : (
                  <>
                    <FileSearch size={16} />
                    Run Website Audit
                  </>
                )}
              </button>
            </div>
            <p className="mt-3 text-[10px] leading-5 text-slate-300">
              The audit can take a few minutes while pages, headers, performance, content, mobile, UX, security, and conversion signals are checked.
            </p>
          </form>
        </div>
      </section>

      {error && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <section className="mt-7 rounded-[24px] border border-emerald-100 bg-white p-8 text-center shadow-[0_12px_40px_rgba(15,23,42,0.05)]">
          <LoaderCircle size={30} className="mx-auto animate-spin text-emerald-500" />
          <h2 className="mt-4 font-display text-lg font-bold text-slate-950">
            Building your audit report
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
            Crawling the website and evaluating performance, SEO, UX, security, content, mobile readiness, and conversion opportunities.
          </p>
        </section>
      )}

      {!loading && !report && !error && (
        <section className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Performance", "Load time, TTFB, caching, compression and CDN."],
            ["SEO & Content", "Metadata, crawlability, headings and content quality."],
            ["UX & Mobile", "Navigation, accessibility, touch targets and layout."],
            ["Security & CRO", "TLS, security headers, trust and lead-generation signals."],
          ].map(([title, detail]) => (
            <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <CheckCircle2 size={18} className="text-emerald-500" />
              <h2 className="mt-3 text-sm font-bold text-slate-950">{title}</h2>
              <p className="mt-2 text-xs leading-5 text-slate-500">{detail}</p>
            </div>
          ))}
        </section>
      )}

      {report && (
        <div className="mt-7 space-y-7">
          <section className="overflow-hidden rounded-[28px] bg-slate-950 text-white shadow-[0_22px_64px_rgba(15,23,42,0.20)]">
            <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[auto_1fr_auto] lg:items-center">
              <ScoreRing
                score={report.overall_score ?? 0}
                label={report.overall_label || "Unrated"}
              />

              <div>
                <div className="flex flex-wrap items-center gap-2 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">
                  <span>{report.audit_id}</span>
                  <span>•</span>
                  <span>{report.pages_crawled} pages crawled</span>
                  <span>•</span>
                  <span>{report.duration_seconds}s</span>
                  {report.ecommerce_detected && (
                    <span className="rounded-full border border-violet-400/30 bg-violet-400/10 px-2 py-1 text-violet-200">
                      E-Commerce detected
                    </span>
                  )}
                </div>
                <h2 className="mt-4 font-display text-2xl font-bold tracking-tight sm:text-3xl">
                  Executive summary
                </h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
                  {report.executive_summary}
                </p>
                <a
                  href={report.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 inline-flex items-center gap-2 text-xs font-semibold text-emerald-300 hover:text-emerald-200"
                >
                  {report.domain}
                  <ExternalLink size={13} />
                </a>
              </div>

              <button
                type="button"
                onClick={() => downloadAuditPdf(report)}
                className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl bg-white px-4 text-xs font-bold text-slate-950 transition hover:bg-emerald-50"
              >
                <Download size={15} />
                Download PDF
              </button>
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard icon={ShieldAlert} label="Critical" value={report.counts?.critical || 0} detail="Immediate risk" style="border-rose-200 bg-rose-50 text-rose-700" />
            <MetricCard icon={XCircle} label="High" value={report.counts?.high || 0} detail="High-impact fixes" style="border-orange-200 bg-orange-50 text-orange-700" />
            <MetricCard icon={TriangleAlert} label="Medium" value={report.counts?.medium || 0} detail="Important improvements" style="border-amber-200 bg-amber-50 text-amber-700" />
            <MetricCard icon={CheckCircle2} label="Passed" value={report.counts?.passed || 0} detail="Checks completed successfully" style="border-emerald-200 bg-emerald-50 text-emerald-700" />
          </section>

          <section className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)] sm:p-6">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-blue-600">Health by module</p>
              <h2 className="mt-2 font-display text-xl font-bold text-slate-950">Audit scorecard</h2>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {(report.modules || []).map((module) => {
                const tone = scoreTone(module.score);
                return (
                  <div key={module.module} className={`rounded-2xl border border-slate-100 p-4 ${tone.background}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-bold text-slate-950">{module.module}</p>
                        <p className="mt-1 text-[10px] font-semibold text-slate-500">{module.score_label}</p>
                      </div>
                      <span className={`text-2xl font-black ${tone.text}`}>{module.score}</span>
                    </div>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/80">
                      <div className="h-full rounded-full" style={{ width: `${module.score}%`, backgroundColor: tone.accent }} />
                    </div>
                    <div className="mt-3 flex justify-between text-[9px] font-bold uppercase tracking-wide text-slate-500">
                      <span className="text-emerald-600">{module.passed} pass</span>
                      <span className="text-amber-600">{module.warning} warn</span>
                      <span className="text-rose-600">{module.failed} fail</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <PriorityList
              title="Fix immediately"
              subtitle="Critical and high-severity findings with the greatest impact."
              items={report.priority?.fix_immediately || []}
              icon={ShieldAlert}
              style="bg-rose-100 text-rose-700"
            />
            <PriorityList
              title="High priority"
              subtitle="Medium-severity improvements to schedule next."
              items={report.priority?.high_priority || []}
              icon={Target}
              style="bg-amber-100 text-amber-700"
            />
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)] sm:p-6">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Website profile</p>
              <h2 className="mt-2 font-display text-xl font-bold text-slate-950">Basic information</h2>
              <dl className="mt-5 grid gap-x-6 gap-y-4 sm:grid-cols-2">
                {basicEntries.map(([key, value]) => (
                  <div key={key} className="border-b border-slate-100 pb-3">
                    <dt className="text-[9px] font-bold uppercase tracking-[0.12em] text-slate-400">{humanize(key)}</dt>
                    <dd className="mt-1 break-words text-xs font-semibold text-slate-700">{displayValue(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="rounded-[24px] border border-violet-100 bg-[linear-gradient(145deg,#ffffff,#f5f3ff)] p-5 shadow-[0_12px_40px_rgba(76,29,149,0.06)] sm:p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-700">
                <Sparkles size={18} />
              </span>
              <h2 className="mt-4 font-display text-xl font-bold text-slate-950">Growth opportunities</h2>
              <div className="mt-5 space-y-3">
                {Object.entries(report.opportunities || {}).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-4 rounded-xl border border-violet-100 bg-white p-3">
                    <span className="text-xs font-semibold text-slate-700">{humanize(key)}</span>
                    <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase ${value === "High" ? "bg-rose-100 text-rose-700" : value === "Medium" ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-[0_12px_40px_rgba(15,23,42,0.05)]">
            <div className="border-b border-slate-100 p-5 sm:p-6">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-blue-600">Detailed results</p>
                  <h2 className="mt-2 font-display text-xl font-bold text-slate-950">All audit checks</h2>
                  <p className="mt-1 text-xs text-slate-500">Showing {filteredIssues.length} of {(report.issues || []).length} checks.</p>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="relative">
                    <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search checks" className="h-9 w-full rounded-lg border border-slate-200 bg-white pl-8 pr-3 text-xs outline-none focus:border-blue-400" />
                  </div>
                  <select value={moduleFilter} onChange={(event) => setModuleFilter(event.target.value)} className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-blue-400">
                    <option value="all">All modules</option>
                    {(report.modules || []).map((module) => <option key={module.module} value={module.module}>{module.module}</option>)}
                  </select>
                  <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)} className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-blue-400">
                    <option value="all">All severities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                    <option value="info">Info</option>
                  </select>
                  <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-blue-400">
                    <option value="actionable">Actionable only</option>
                    <option value="all">All statuses</option>
                    <option value="failed">Failed</option>
                    <option value="warning">Warning</option>
                    <option value="passed">Passed</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-[1050px] w-full text-left">
                <thead className="bg-slate-50 text-[9px] font-bold uppercase tracking-[0.12em] text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Module / Check</th>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Current</th>
                    <th className="px-4 py-3">Expected</th>
                    <th className="px-5 py-3">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredIssues.map((issue, index) => (
                    <tr key={`${issue.module}-${issue.test_name}-${index}`} className="align-top hover:bg-slate-50/70">
                      <td className="px-5 py-4">
                        <p className="text-[9px] font-bold uppercase tracking-[0.1em] text-slate-400">{issue.module}</p>
                        <p className="mt-1 text-xs font-bold text-slate-900">{issue.test_name}</p>
                      </td>
                      <td className="px-4 py-4"><span className={`rounded-full border px-2 py-1 text-[9px] font-bold uppercase ${SEVERITY_STYLES[issue.severity] || SEVERITY_STYLES.info}`}>{issue.severity}</span></td>
                      <td className="px-4 py-4"><span className={`rounded-full border px-2 py-1 text-[9px] font-bold uppercase ${STATUS_STYLES[issue.status] || STATUS_STYLES.warning}`}>{issue.status}</span></td>
                      <td className="max-w-[190px] break-words px-4 py-4 text-[11px] leading-5 text-slate-600">{displayValue(issue.current_value)}</td>
                      <td className="max-w-[190px] break-words px-4 py-4 text-[11px] leading-5 text-slate-600">{displayValue(issue.expected_value)}</td>
                      <td className="max-w-[300px] px-5 py-4 text-[11px] leading-5 text-slate-700">{displayValue(issue.recommendation)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!filteredIssues.length && (
                <div className="p-8 text-center text-sm text-slate-500">No checks match the selected filters.</div>
              )}
            </div>
          </section>

          <section className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)] sm:p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700"><Clock3 size={18} /></span>
              <div>
                <h2 className="font-display text-lg font-bold text-slate-950">Pages crawled</h2>
                <p className="mt-1 text-xs text-slate-500">HTTP response and timing details for each audited page.</p>
              </div>
            </div>
            <div className="mt-5 overflow-x-auto rounded-xl border border-slate-100">
              <table className="min-w-[700px] w-full text-left">
                <thead className="bg-slate-50 text-[9px] font-bold uppercase tracking-[0.12em] text-slate-500">
                  <tr><th className="px-4 py-3">URL</th><th className="px-4 py-3">HTTP</th><th className="px-4 py-3">Response time</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(report.page_urls || []).map((page) => (
                    <tr key={page.url}>
                      <td className="max-w-[700px] break-all px-4 py-3 text-xs font-medium text-slate-700">{page.url}</td>
                      <td className="px-4 py-3 text-xs font-bold text-slate-700">{page.status_code ?? "—"}</td>
                      <td className="px-4 py-3 text-xs text-slate-600">{page.response_time_ms == null ? "—" : `${page.response_time_ms} ms`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
