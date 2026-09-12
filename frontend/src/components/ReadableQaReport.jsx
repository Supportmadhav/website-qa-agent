import {
  Download,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import StatusBadge from "./StatusBadge";

import {
  buildDefaultReportName,
  downloadPdfReport,
} from "../utils/report";


const FILTERS = [
  { id: "attention", label: "Needs attention" },
  { id: "all", label: "All" },
  { id: "fail", label: "Fail" },
  { id: "warning", label: "Warning" },
  { id: "pass", label: "Pass" },
  { id: "info", label: "Info" },
];


function recommendationFor(
  resultId,
  finding
) {
  const status =
    finding?.status
    ||
    "info";

  if (status === "pass") {
    return "No action required.";
  }

  if (status === "info") {
    return "Information only. Review if relevant to the project.";
  }

  const text =
    `${finding?.title || ""} ${finding?.message || ""}`
      .toLowerCase();

  const rules = [
    [
      /small buttons|cta/,
      "Increase the clickable area, padding or control height if the element is genuinely difficult to use.",
    ],
    [
      /small text|font size/,
      "Increase the affected text size for comfortable reading.",
    ],
    [
      /clipping|clipped/,
      "Review overflow, fixed heights and wrapping so the complete text remains visible.",
    ],
    [
      /line height/,
      "Increase line-height or remove conflicting fixed heights.",
    ],
    [
      /wide paragraph/,
      "Use a readable max-width for long text blocks.",
    ],
    [
      /image distortion/,
      "Preserve the source aspect ratio or use an intentional object-fit rule.",
    ],
    [
      /reduced motion/,
      "Add or verify prefers-reduced-motion handling.",
    ],
    [
      /animation duration|transition duration/,
      "Reduce unusually long timing unless it is intentional.",
    ],
    [
      /infinite animation/,
      "Confirm the continuous animation is intentional and not distracting.",
    ],
    [
      /canonical/,
      "Point the canonical tag to the preferred public URL.",
    ],
    [
      /noindex|robots/,
      "Confirm search-engine blocking is intentional before launch.",
    ],
    [
      /broken|404/,
      "Update/remove the broken destination and use a working URL.",
    ],
    [
      /unverified/,
      "Review the URL manually because it could not be confirmed automatically.",
    ],
    [
      /spelling/,
      "Confirm the word in context, then apply the suggestion only if it is not a brand, company or technical term.",
    ],
    [
      /grammar/,
      "Review the complete sentence in context before changing it.",
    ],
  ];

  for (
    const [
      pattern,
      recommendation,
    ] of rules
  ) {
    if (pattern.test(text)) {
      return recommendation;
    }
  }

  if (resultId === "css_animation") {
    return "Review the animation/transition and confirm its duration, repetition and accessibility are intentional.";
  }

  if (resultId === "layout_design") {
    return "Review the affected layout element and correct sizing, spacing or alignment if the issue is visible.";
  }

  return "Review this finding and correct it if the behavior is not intentional.";
}


function CountCard({
  label,
  count,
  tone,
  active,
  onClick,
}) {
  const classes = {
    fail:
      "border-rose-200 bg-rose-50 text-rose-700",
    warning:
      "border-amber-200 bg-amber-50 text-amber-700",
    pass:
      "border-emerald-200 bg-emerald-50 text-emerald-700",
    info:
      "border-sky-200 bg-sky-50 text-sky-700",
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-2xl border p-4 text-left transition",
        classes[tone],
        active
          ? "ring-4 ring-blue-100"
          : "",
      ].join(" ")}
    >
      <p className="text-[10px] font-bold uppercase tracking-[0.12em]">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold">
        {count}
      </p>
    </button>
  );
}


function ContentIssueTable({
  issues,
  filter,
}) {
  const rows =
    filter === "all"
      ? issues
      : issues.filter(
          (issue) =>
            filter === "attention"
              ? issue.status === "fail" || issue.status === "warning"
              : issue.status === filter
        );

  if (!rows.length) {
    return null;
  }

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
        <h3 className="text-sm font-semibold text-slate-950">
          Detailed Spelling & Grammar Issues
        </h3>

        <p className="mt-1 text-[11px] text-slate-500">
          High-confidence issues after filtering likely company names, proper nouns, punctuation-only differences and accepted terminology.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1150px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-950 text-white">
              <th className="w-[105px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Status</th>
              <th className="w-[105px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Type</th>
              <th className="w-[155px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Incorrect</th>
              <th className="w-[175px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Suggestion</th>
              <th className="w-[145px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Location</th>
              <th className="w-[180px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Rule</th>
              <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Website Content</th>
            </tr>
          </thead>

          <tbody>
            {rows.map(
              (
                issue,
                index
              ) => (
                <tr
                  key={`${issue.type}-${issue.incorrect}-${issue.location}-${index}`}
                  className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                >
                  <td className="px-4 py-3 align-top">
                    <StatusBadge
                      status={issue.status || "warning"}
                      compact
                    />
                  </td>
                  <td className="px-4 py-3 align-top text-xs font-semibold capitalize text-slate-800">
                    {issue.type || "content"}
                  </td>
                  <td className="px-4 py-3 align-top text-xs font-bold text-slate-900">
                    {issue.incorrect || "—"}
                  </td>
                  <td className="px-4 py-3 align-top text-xs font-semibold text-blue-700">
                    {issue.suggestion || "Review manually"}
                  </td>
                  <td className="px-4 py-3 align-top text-xs text-slate-600">
                    {issue.location || "—"}
                  </td>
                  <td className="px-4 py-3 align-top text-xs text-slate-600">
                    {issue.rule || "—"}
                  </td>
                  <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                    {issue.context?.length > 130 ? (
                      <details>
                        <summary className="cursor-pointer">{issue.context.slice(0, 130)}…</summary>
                        <p className="mt-2 whitespace-pre-wrap">{issue.context}</p>
                      </details>
                    ) : issue.context || "—"}
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}


function FindingsTable({
  result,
  findings,
  filter,
}) {
  const isContent =
    result.id === "content";

  const rows =
    findings.filter(
      (finding) => {
        if (
          isContent
          &&
          /^(Spelling|Grammar)\s*:/i.test(
            finding.title || ""
          )
        ) {
          return false;
        }

        return (
          filter === "all"
          ||
          (filter === "attention"
            ? finding.status === "fail" || finding.status === "warning"
            : finding.status === filter)
        );
      }
    );

  if (!rows.length) {
    if (isContent) {
      return null;
    }

    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
        {filter === "attention" ? "No warning or failure findings." : "No rows match this status filter."}
      </div>
    );
  }

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
        <h3 className="text-sm font-semibold text-slate-950">
          {
            isContent
              ? "Content Check Summary"
              : `${result.label} Findings`
          }
        </h3>

        <p className="mt-1 text-[11px] text-slate-500">
          All PASS, WARNING, FAIL and INFO rows are visible when All is selected.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1050px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-950 text-white">
              <th className="w-[110px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Status</th>
              <th className="w-[280px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Check / Item</th>
              <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Result / Details</th>
              <th className="w-[330px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Recommendation</th>
            </tr>
          </thead>

          <tbody>
            {rows.map(
              (
                finding,
                index
              ) => (
                <tr
                  key={`${finding.status}-${finding.title}-${finding.message}-${index}`}
                  className={[
                    "border-b border-slate-100 last:border-b-0",
                    finding.status === "fail"
                      ? "bg-rose-50/40"
                      : finding.status === "warning"
                        ? "bg-amber-50/30"
                        : "hover:bg-slate-50",
                  ].join(" ")}
                >
                  <td className="px-4 py-3 align-top">
                    <StatusBadge
                      status={finding.status}
                      compact
                    />
                  </td>
                  <td className="px-4 py-3 align-top text-xs font-semibold text-slate-900">
                    {finding.title || result.label}
                  </td>
                  <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                    {finding.message || "No additional detail."}
                  </td>
                  <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                    {recommendationFor(result.id, finding)}
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}


export default function ReadableQaReport({
  report,
  result,
}) {
  const [
    filter,
    setFilter,
  ] = useState(() =>
    (result.findings || []).some(item => item.status === "warning" || item.status === "fail")
      ? "attention"
      : (result.findings || []).length > 0
        && (result.findings || []).every(item => item.status === "pass")
        ? "summary"
        : "all"
  );

  const findings =
    result.findings
    ||
    [];

  const contentIssues =
    result.content_issues
    ||
    [];

  const reportName =
    buildDefaultReportName(report);

  const counts =
    useMemo(
      () => ({
        fail:
          findings.filter(
            (item) =>
              item.status === "fail"
          ).length,
        warning:
          findings.filter(
            (item) =>
              item.status === "warning"
          ).length,
        pass:
          findings.filter(
            (item) =>
              item.status === "pass"
          ).length,
        info:
          findings.filter(
            (item) =>
              item.status === "info"
          ).length,
      }),
      [findings]
    );

  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                <ShieldCheck size={18} />
              </span>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  {result.category || "QA"} Report
                </p>

                <h2 className="mt-0.5 text-lg font-semibold text-slate-950">
                  {reportName}
                </h2>
              </div>
            </div>

            <a
              href={report.page?.final_url}
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-flex items-center gap-1 break-all text-xs font-medium text-blue-600 hover:text-blue-700"
            >
              {report.page?.final_url || "—"}
              <ExternalLink size={12} />
            </a>
          </div>

          <button
            type="button"
            onClick={() =>
              downloadPdfReport(report)
            }
            className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-xs font-semibold text-white transition hover:bg-blue-600"
          >
            <Download size={15} />
            Download PDF Report
          </button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <CountCard
            label="Fail"
            count={counts.fail}
            tone="fail"
            active={filter === "fail"}
            onClick={() => setFilter("fail")}
          />
          <CountCard
            label="Warning"
            count={counts.warning}
            tone="warning"
            active={filter === "warning"}
            onClick={() => setFilter("warning")}
          />
          <CountCard
            label="Pass"
            count={counts.pass}
            tone="pass"
            active={filter === "pass"}
            onClick={() => setFilter("pass")}
          />
          <CountCard
            label="Information"
            count={counts.info}
            tone="info"
            active={filter === "info"}
            onClick={() => setFilter("info")}
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {FILTERS.map(
            (item) => (
              <button
                key={item.id}
                type="button"
                onClick={() =>
                  setFilter(item.id)
                }
                className={[
                  "rounded-lg px-3 py-2 text-xs font-semibold transition",
                  filter === item.id
                    ? "bg-slate-950 text-white"
                    : "bg-slate-50 text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100",
                ].join(" ")}
              >
                {item.label}
                {
                  item.id !== "all"
                  &&
                  ` (${item.id === "attention" ? counts.fail + counts.warning : counts[item.id] || 0})`
                }
              </button>
            )
          )}
        </div>
      </div>

      {
        result.id === "content"
        &&
        (
          <ContentIssueTable
            issues={contentIssues}
            filter={filter}
          />
        )
      }

      {filter === "summary" ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-800">
          <p className="font-semibold">All checks passed.</p>
          <button type="button" onClick={() => setFilter("all")}
            className="mt-2 text-xs font-bold underline">Show all checks</button>
        </div>
      ) : (
        <FindingsTable
          result={result}
          findings={findings}
          filter={filter}
        />
      )}
    </section>
  );
}
