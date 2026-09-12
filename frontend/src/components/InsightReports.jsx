import { useMemo, useState } from "react";
import {
  AlertTriangle, Check, ChevronDown, ChevronUp, Download,
  ExternalLink, Facebook, Instagram, Linkedin, Link2, Music2,
  SearchCheck, ShieldCheck, Youtube,
} from "lucide-react";

import StatusBadge from "./StatusBadge";
import { buildDefaultReportName, downloadPdfReport } from "../utils/report";

const tone = {
  fail: "border-rose-200 bg-rose-50 text-rose-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
  pass: "border-emerald-200 bg-emerald-50 text-emerald-700",
  info: "border-sky-200 bg-sky-50 text-sky-700",
};

const socialIcons = {
  Instagram, LinkedIn: Linkedin, Facebook, YouTube: Youtube,
  TikTok: Music2,
};

const socialColors = {
  Instagram: "bg-pink-50 text-pink-600",
  LinkedIn: "bg-blue-50 text-blue-700",
  Facebook: "bg-blue-50 text-blue-700",
  YouTube: "bg-red-50 text-red-600",
  TikTok: "bg-slate-100 text-slate-900",
  Pinterest: "bg-red-50 text-red-700",
  "X / Twitter": "bg-slate-100 text-slate-900",
  WhatsApp: "bg-emerald-50 text-emerald-700",
};

function CountStrip({ findings }) {
  const counts = useMemo(() => Object.fromEntries(
    ["fail", "warning", "pass", "info"].map(status => [
      status, findings.filter(item => item.status === status).length,
    ])
  ), [findings]);

  return (
    <div className="grid gap-3 sm:grid-cols-4">
      {Object.entries(counts).map(([status, count]) => (
        <div key={status} className={`rounded-2xl border p-4 ${tone[status]}`}>
          <p className="text-[10px] font-bold uppercase tracking-widest">{status}</p>
          <p className="mt-1 text-2xl font-bold">{count}</p>
        </div>
      ))}
    </div>
  );
}

function ScoreRing({ score, label }) {
  const color = score >= 85 ? "#059669" : score >= 65 ? "#d97706" : "#e11d48";
  return (
    <div className="flex items-center gap-4">
      <div
        className="flex h-[76px] w-[76px] shrink-0 items-center justify-center rounded-full p-[7px]"
        style={{ background: `conic-gradient(${color} ${score}%, #e2e8f0 0)` }}
        aria-label={`${label}: ${score} out of 100`}
      >
        <div className="flex h-full w-full items-center justify-center rounded-full bg-white text-xl font-bold text-slate-950">
          {score}
        </div>
      </div>
      <div>
        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</p>
        <p className="mt-1 text-sm font-semibold text-slate-900">
          {score >= 85 ? "Good foundation" : score >= 65 ? "Some items to review" : "Needs attention"}
        </p>
      </div>
    </div>
  );
}

function ReportHeader({ report, result, children }) {
  const name = buildDefaultReportName(report);
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            {result.category} report
          </p>
          <h2 className="mt-1 text-lg font-bold text-slate-950">
            {result.id === "meta" ? name.replace(/^Meta & Source Data/, "SEO Report") : name}
          </h2>
          <a href={report.page?.final_url} target="_blank" rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1 break-all text-xs text-blue-600">
            {report.page?.final_url}<ExternalLink size={12} />
          </a>
        </div>
        <button type="button" onClick={() => downloadPdfReport(report)}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-xs font-semibold text-white hover:bg-blue-700">
          <Download size={15} />Download PDF Report
        </button>
      </div>
      {children && <div className="mt-5">{children}</div>}
    </div>
  );
}

function AttentionList({ findings, title = "Needs attention" }) {
  const issues = findings.filter(item => item.status === "warning" || item.status === "fail");
  if (!issues.length) return null;
  return (
    <section className="overflow-hidden rounded-3xl border border-amber-200 bg-white shadow-sm">
      <div className="border-b border-amber-100 bg-amber-50 px-5 py-4">
        <h3 className="text-sm font-bold text-slate-950">{title}</h3>
      </div>
      <div className="divide-y divide-slate-100">
        {issues.map((item, index) => (
          <div key={`${item.title}-${index}`} className="flex gap-3 px-5 py-4">
            <StatusBadge status={item.status} compact />
            <div className="min-w-0 text-xs">
              <p className="font-bold text-slate-900">{item.title}</p>
              <p className="mt-1 break-words leading-5 text-slate-600">{item.message}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function PassDisclosure({ findings }) {
  const [expanded, setExpanded] = useState(false);
  const passes = findings.filter(item => item.status === "pass");
  if (!passes.length) return null;
  return (
    <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4">
      <button type="button" onClick={() => setExpanded(value => !value)}
        className="flex w-full items-center justify-between gap-2 text-left text-xs font-semibold text-emerald-800">
        <span className="inline-flex items-center gap-2"><Check size={15} />
          {findings.every(item => item.status === "pass") ? "All checks passed" : `${passes.length} checks passed`}
        </span>
        <span className="inline-flex items-center gap-1">
          {expanded ? "Hide checks" : "Show all checks"}
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </span>
      </button>
      {expanded && (
        <ul className="mt-3 space-y-2 border-t border-emerald-200 pt-3 text-xs text-slate-700">
          {passes.map((item, index) => <li key={`${item.title}-${index}`}>
            <span className="font-semibold">{item.title}</span>
            {item.message && <span> — {item.message}</span>}
          </li>)}
        </ul>
      )}
    </section>
  );
}

function SectionCard({ title, children }) {
  return <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <h3 className="text-sm font-bold text-slate-950">{title}</h3>
    <div className="mt-4">{children}</div>
  </section>;
}

function LengthCard({ label, text, length, ideal }) {
  const good = length >= ideal[0] && length <= ideal[1];
  const width = Math.min(100, Math.round(100 * length / ideal[1]));
  return <SectionCard title={label}>
    <p className="min-h-10 break-words text-sm leading-6 text-slate-800">{text || "Not present"}</p>
    <div className="mt-3 flex items-center justify-between text-xs">
      <span className={good ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"}>
        {length} / {ideal[1]} characters
      </span>
      <span className="text-slate-500">Ideal: {ideal[0]}–{ideal[1]}</span>
    </div>
    <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full rounded-full ${good ? "bg-emerald-500" : "bg-amber-500"}`}
        style={{ width: `${width}%` }} />
    </div>
  </SectionCard>;
}

export function SocialMediaInsightReport({ report, result }) {
  const profiles = result.social_profiles || [];
  const uniqueProfiles = Array.from(new Map(profiles.map(item => [item.url, item])).values());
  const issues = result.findings.filter(item => item.status === "fail" || item.status === "warning");
  return <section className="space-y-4">
    <ReportHeader report={report} result={result}><CountStrip findings={result.findings} /></ReportHeader>
    <SectionCard title={`Detected social profiles (${uniqueProfiles.length})`}>
      {uniqueProfiles.length ? <div className="grid gap-3 sm:grid-cols-2">
        {uniqueProfiles.map(profile => {
          const Icon = socialIcons[profile.platform] || Link2;
          const displayUrl = (() => { try { const url = new URL(profile.url); return `${url.hostname}${url.pathname}`.replace(/\/$/, ""); } catch { return profile.url; } })();
          return <a key={profile.url} href={profile.url} target="_blank" rel="noreferrer"
            className={`flex items-center gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-blue-300 hover:bg-blue-50 ${profile.issues?.length ? "border-l-4 border-l-amber-400" : ""}`}>
            <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${socialColors[profile.platform] || "bg-blue-50 text-blue-700"}`}>
              <Icon size={20} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-bold text-slate-950">{profile.platform}</span>
              <span className="block truncate text-xs text-slate-500">{displayUrl}</span>
              {!!profile.issues?.length && <span className="mt-1 block text-[11px] text-amber-700">{profile.issues.join(" • ")}</span>}
            </span>
            <ExternalLink size={15} className="shrink-0 text-slate-400" />
          </a>;
        })}
      </div> : <p className="text-sm text-slate-500">No social profiles detected on this page.</p>}
      <p className="mt-4 text-xs text-slate-500">
        {profiles.every(item => item.opens_new_tab) ? "Opens in new tab" : "Some links do not open in a new tab"}
        {" • "}{profiles.some(item => item.is_duplicate) ? "Duplicate links found" : "No duplicate URLs"}
        {" • "}{profiles.every(item => item.is_consistent) ? "Consistent across this page" : "Conflicting platform URLs found"}
      </p>
    </SectionCard>
    <AttentionList findings={issues} title="Social links to review" />
    <PassDisclosure findings={result.findings} />
  </section>;
}

export function SeoInsightReport({ report, result }) {
  const data = result.seo_overview;
  const total = data.alt_present_count + data.alt_empty_count + data.alt_missing_count;
  const tags = data.meta_tags_present || {};
  return <section className="space-y-4">
    <ReportHeader report={report} result={result}>
      <div className="grid gap-5 lg:grid-cols-[auto_1fr] lg:items-center">
        <ScoreRing score={data.seo_score} label="SEO score / 100" />
        <CountStrip findings={result.findings} />
      </div>
    </ReportHeader>
    <div className="grid gap-4 lg:grid-cols-2">
      <LengthCard label="Page title" text={data.title_text} length={data.title_length} ideal={[50, 60]} />
      <LengthCard label="Meta description" text={data.description_text} length={data.description_length} ideal={[155, 160]} />
    </div>
    <SectionCard title="Heading structure">
      {data.heading_sequence.length ? <div className="space-y-2">
        {data.heading_sequence.slice(0, 40).map((heading, index) =>
          <div key={`${heading.level}-${index}`} className="flex items-start gap-3 rounded-lg bg-slate-50 px-3 py-2"
            style={{ marginLeft: `${Math.min(5, heading.level - 1) * 12}px` }}>
            <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">H{heading.level}</span>
            <span className="text-xs text-slate-700">{heading.text || "Empty heading"}</span>
          </div>)}
        {data.heading_sequence.length > 40 && <p className="text-xs text-slate-500">Showing first 40 headings.</p>}
      </div> : <p className="text-xs text-amber-700">No headings found.</p>}
      {!!data.heading_skips.length && <p className="mt-3 text-xs font-semibold text-amber-700">
        <AlertTriangle size={14} className="mr-1 inline" />Skipped levels: {data.heading_skips.join(", ")}
      </p>}
    </SectionCard>
    <div className="grid gap-4 lg:grid-cols-2">
      <SectionCard title={`Image alt tags (${total} images)`}>
        <div className="grid grid-cols-3 gap-3">
          {[["Present", data.alt_present_count, "text-emerald-700"], ["Empty", data.alt_empty_count, "text-amber-700"], ["Missing", data.alt_missing_count, "text-rose-700"]].map(([label, value, className]) =>
            <div key={label} className="rounded-xl bg-slate-50 p-3 text-center">
              <p className={`text-2xl font-bold ${className}`}>{value}</p><p className="text-[11px] text-slate-500">{label}</p>
            </div>)}
        </div>
      </SectionCard>
      <SectionCard title="Meta tags">
        <div className="flex flex-wrap gap-2">
          {Object.entries(tags).map(([key, present]) =>
            <span key={key} className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${present ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
              {present ? "✓" : "×"} {key.replaceAll("_", " ")}
            </span>)}
        </div>
      </SectionCard>
    </div>
    <AttentionList findings={result.findings} title="SEO items to review" />
    <PassDisclosure findings={result.findings} />
  </section>;
}

export function LayoutInsightReport({ report, result }) {
  const data = result.design_overview;
  const checklist = ["Very Small Text", "Text Clipping", "Line Height", "Wide Paragraphs", "Image Distortion", "Small Buttons / CTAs"];
  const findings = result.findings || [];
  return <section className="space-y-4">
    <ReportHeader report={report} result={result}>
      <div className="grid gap-5 lg:grid-cols-[auto_1fr] lg:items-center">
        <ScoreRing score={data.design_score} label="Design score / 100" />
        <CountStrip findings={findings} />
      </div>
      <p className="mt-4 text-[11px] text-slate-500">{data.score_basis}</p>
    </ReportHeader>
    <SectionCard title="Color palette & contrast">
      <div className="flex flex-wrap gap-3">
        {(data.dominant_colors || []).map(color => <div key={color} className="text-center">
          <div className="h-12 w-12 rounded-xl border border-slate-200" style={{ backgroundColor: color }} />
          <span className="mt-1 block text-[10px] text-slate-500">{color}</span>
        </div>)}
      </div>
      <div className="mt-4 space-y-2">
        {(data.contrast_pairs || []).filter(pair => !pair.passes_aa).slice(0, 8).map((pair, index) =>
          <p key={index} className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
            <AlertTriangle size={13} className="mr-1 inline" />
            {pair.fg} on {pair.bg}: {pair.ratio}:1, below AA {pair.large_text ? "3:1" : "4.5:1"} — {pair.text}
          </p>)}
        {(data.contrast_pairs || []).length > 0 && data.contrast_pairs.every(pair => pair.passes_aa) &&
          <p className="text-xs font-semibold text-emerald-700">Sampled text/background pairs meet WCAG AA contrast.</p>}
      </div>
    </SectionCard>
    <div className="grid gap-4 lg:grid-cols-2">
      <SectionCard title="Typography">
        <p className="text-2xl font-bold text-slate-950">{data.font_families.length} <span className="text-sm font-normal text-slate-500">font families</span></p>
        <p className="mt-2 text-xs text-slate-600">{data.font_families.join(", ") || "None detected"}</p>
        <p className={`mt-3 text-xs font-semibold ${data.type_scale_consistent ? "text-emerald-700" : "text-amber-700"}`}>
          {data.type_scale_consistent ? "Heading type scale is consistent" : "Heading type scale needs review"}
        </p>
      </SectionCard>
      <SectionCard title="Whitespace & density · Beta">
        <p className="text-2xl font-bold text-slate-950">{data.whitespace_density_score}<span className="text-sm font-normal text-slate-500"> / 100</span></p>
        <div className="mt-3 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-blue-500" style={{ width: `${data.whitespace_density_score}%` }} /></div>
        <p className="mt-3 text-xs text-slate-500">Experimental spacing heuristic; not an aesthetic judgment or part of the design score.</p>
      </SectionCard>
    </div>
    <SectionCard title="Usability checklist">
      <div className="grid gap-2 sm:grid-cols-2">
        {checklist.map(label => {
          const finding = findings.find(item => item.title === label);
          const good = finding?.status === "pass";
          return <div key={label} className={`rounded-xl border p-3 text-xs ${good ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}>
            <span className="flex items-center gap-2 font-semibold text-slate-900">
              {good ? <Check size={14} className="text-emerald-700" /> : <AlertTriangle size={14} className="text-amber-700" />}{label}
            </span>
            {!good && finding && <p className="mt-2 leading-5 text-slate-600">{finding.message}</p>}
          </div>;
        })}
      </div>
    </SectionCard>
    <AttentionList findings={findings.filter(item => !checklist.includes(item.title))} title="Other design findings" />
  </section>;
}

export function BrokenLinksInsightReport({ report, result }) {
  const findings = result.findings || [];
  const byTitle = name => findings.find(item => item.title === name)?.message || "";
  const readCount = text => Number((text.match(/\d+/) || [0])[0]);
  const total = readCount(byTitle("HTML Links"));
  const unique = readCount(byTitle("Unique HTTP Links"));
  const ignored = readCount(byTitle("Ignored Non-HTTP Links"));
  const working = readCount(byTitle("Working Links"));
  const flagged = findings.filter(item => item.title === "Broken URL" || item.title === "Unverified URL");
  const broken = flagged.filter(item => item.title === "Broken URL").length;
  const unverified = flagged.length - broken;
  const linkFrom = message => {
    const match = message.match(/https?:\/\/\S+/);
    return match ? match[0] : "";
  };
  return <section className="space-y-4">
    <ReportHeader report={report} result={result}>
      <div className="grid gap-3 sm:grid-cols-4">
        {[["Total links", total, "info"], ["Working", working, "pass"], ["Unverified", unverified, "warning"], ["Broken", broken, "fail"]].map(([label, value, status]) =>
          <div key={label} className={`rounded-2xl border p-4 ${tone[status]}`}>
            <p className="text-[10px] font-bold uppercase tracking-widest">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p>
          </div>)}
      </div>
    </ReportHeader>
    <SectionCard title={`Flagged links (${flagged.length})`}>
      {flagged.length ? <div className="space-y-3">
        {[...flagged].sort((a, b) => (a.status === "fail" ? -1 : 1) - (b.status === "fail" ? -1 : 1)).map((item, index) => {
          const url = linkFrom(item.message || "");
          return <div key={`${url}-${index}`} className="rounded-xl border border-slate-200 p-4">
            <div className="flex items-start gap-2"><StatusBadge status={item.status} compact />
              <div className="min-w-0 flex-1">
                {url && <a href={url} target="_blank" rel="noreferrer" className="break-all text-xs font-semibold text-blue-600 hover:underline">{url} <ExternalLink size={11} className="inline" /></a>}
                <p className="mt-1 text-xs text-slate-600">{(item.message || "").replace(url, "").replace(/^\s*\|\s*|\s*\|\s*$/g, "")}</p>
              </div>
            </div>
          </div>;
        })}
      </div> : <p className="text-sm font-semibold text-emerald-700"><ShieldCheck size={16} className="mr-2 inline" />No broken or unverified links found.</p>}
    </SectionCard>
    <details className="rounded-2xl border border-slate-200 bg-white px-5 py-4 text-xs text-slate-600">
      <summary className="cursor-pointer font-semibold text-slate-800">Link inventory details</summary>
      <p className="mt-3">HTML links: {total} · Unique HTTP links: {unique} · Ignored non-HTTP links: {ignored} · Working: {working}</p>
    </details>
  </section>;
}
