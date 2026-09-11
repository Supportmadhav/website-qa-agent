import {
  AlertTriangle,
  CheckCircle2,
  Download,
  ExternalLink,
  Gauge,
  Info,
  Monitor,
  Smartphone,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import StatusBadge from "./StatusBadge";

import {
  downloadPdfReport,
} from "../utils/report";


function ScoreRing({
  score,
  status,
}) {
  const safeScore =
    Number.isFinite(score)
      ? Math.max(0, Math.min(100, score))
      : null;

  const stroke =
    status === "pass"
      ? "#10b981"
      : status === "warning"
        ? "#f59e0b"
        : status === "fail"
          ? "#ef4444"
          : "#94a3b8";

  const circumference =
    2 * Math.PI * 48;

  const offset =
    safeScore === null
      ? circumference
      : circumference * (1 - safeScore / 100);

  return (
    <div className="relative h-36 w-36">
      <svg
        viewBox="0 0 120 120"
        className="h-full w-full -rotate-90"
      >
        <circle
          cx="60"
          cy="60"
          r="48"
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="10"
        />

        <circle
          cx="60"
          cy="60"
          r="48"
          fill="none"
          stroke={stroke}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold text-slate-950">
          {safeScore === null ? "—" : safeScore}
        </span>

        <span className="mt-1 text-[9px] font-bold uppercase tracking-[0.12em] text-slate-400">
          Lighthouse
        </span>
      </div>
    </div>
  );
}


function SourceBadge({
  source,
}) {
  const local =
    source === "local_lighthouse";

  return (
    <span
      className={[
        "inline-flex rounded-full border px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.1em]",
        local
          ? "border-violet-200 bg-violet-50 text-violet-700"
          : "border-blue-200 bg-blue-50 text-blue-700",
      ].join(" ")}
    >
      {
        local
          ? "Local Lighthouse"
          : "Google PageSpeed Insights"
      }
    </span>
  );
}


function StrategyButton({
  id,
  active,
  data,
  onClick,
}) {
  const Icon =
    id === "mobile"
      ? Smartphone
      : Monitor;

  return (
    <button
      type="button"
      disabled={!data}
      onClick={onClick}
      className={[
        "flex min-h-[48px] items-center gap-3 rounded-xl border px-4 text-left transition",
        active
          ? "border-blue-500 bg-blue-50 ring-4 ring-blue-50"
          : data
            ? "border-slate-200 bg-white hover:border-blue-300"
            : "cursor-not-allowed border-slate-200 bg-slate-50 opacity-45",
      ].join(" ")}
    >
      <Icon
        size={16}
        className={
          active
            ? "text-blue-600"
            : "text-slate-500"
        }
      />

      <div>
        <p className="text-xs font-bold capitalize text-slate-900">
          {id}
        </p>

        <p className="mt-0.5 text-[10px] text-slate-500">
          {
            data
              ? `${data.score ?? "—"} / 100`
              : "Unavailable"
          }
        </p>
      </div>
    </button>
  );
}


function MetricsTable({
  metrics,
}) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
        <h3 className="text-sm font-semibold text-slate-950">
          Performance Metrics
        </h3>

        <p className="mt-1 text-[11px] text-slate-500">
          Lighthouse lab metrics for the selected Mobile or Desktop strategy.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-950 text-white">
              <th className="w-[250px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Metric</th>
              <th className="w-[140px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Result</th>
              <th className="w-[115px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Status</th>
              <th className="w-[160px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Target</th>
              <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Meaning</th>
            </tr>
          </thead>

          <tbody>
            {(metrics || []).map(
              (metric) => (
                <tr
                  key={metric.id}
                  className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                >
                  <td className="px-4 py-3 text-xs font-semibold text-slate-900">
                    {metric.label}
                  </td>
                  <td className="px-4 py-3 text-xs font-bold text-slate-900">
                    {metric.display}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge
                      status={metric.status}
                      compact
                    />
                  </td>
                  <td className="px-4 py-3 text-xs font-medium text-slate-600">
                    {metric.target}
                  </td>
                  <td className="px-4 py-3 text-xs leading-5 text-slate-600">
                    {metric.description}
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


function OpportunityTable({
  opportunities,
}) {
  const rows =
    (opportunities || []).filter(
      (item) =>
        item.status === "warning"
        ||
        item.status === "fail"
    );

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
        <h3 className="text-sm font-semibold text-slate-950">
          What Needs Attention
        </h3>

        <p className="mt-1 text-[11px] text-slate-500">
          Lighthouse audits that can improve the selected performance score.
        </p>
      </div>

      {
        rows.length
          ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] border-collapse text-left">
                  <thead>
                    <tr className="bg-slate-950 text-white">
                      <th className="w-[115px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Status</th>
                      <th className="w-[300px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Audit</th>
                      <th className="w-[175px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Measured Detail</th>
                      <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Meaning / Recommendation</th>
                    </tr>
                  </thead>

                  <tbody>
                    {rows.map(
                      (item) => (
                        <tr
                          key={item.id}
                          className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                        >
                          <td className="px-4 py-3 align-top">
                            <StatusBadge
                              status={item.status}
                              compact
                            />
                          </td>
                          <td className="px-4 py-3 align-top text-xs font-semibold text-slate-900">
                            {item.title}
                          </td>
                          <td className="px-4 py-3 align-top text-xs font-medium text-slate-600">
                            {item.display || "—"}
                          </td>
                          <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                            {item.description || "Review this Lighthouse audit."}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            )
          : (
              <div className="p-8 text-center">
                <CheckCircle2
                  size={26}
                  className="mx-auto text-emerald-600"
                />

                <p className="mt-3 text-sm font-bold text-emerald-900">
                  No major Lighthouse opportunity is flagged
                </p>
              </div>
            )
      }
    </section>
  );
}


export default function PageSpeedReport({
  report,
  result,
}) {
  const data =
    result.page_speed_data
    ||
    {};

  const strategies =
    data.strategies
    ||
    {};

  const initial =
    data.default_strategy
    ||
    (
      strategies.mobile
        ? "mobile"
        : "desktop"
    );

  const [
    strategy,
    setStrategy,
  ] = useState(initial);

  const active =
    strategies[strategy]
    ||
    {};

  const errors =
    useMemo(
      () =>
        Object.entries(
          data.api_errors
          ||
          {}
        ),
      [data.api_errors]
    );

  const resources =
    data.local_resource_diagnostics?.resource_summary
    ||
    data.resource_summary
    ||
    [];

  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                <Gauge size={19} />
              </span>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  Lighthouse Performance Report
                </p>

                <h2 className="mt-0.5 text-lg font-semibold text-slate-950">
                  Page Speed - {report.page?.title || "Website"}
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
            Download Page Speed PDF
          </button>
        </div>

        {
          !data.available
          &&
          (
            <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 p-4">
              <div className="flex gap-3">
                <AlertTriangle
                  size={18}
                  className="mt-0.5 shrink-0 text-rose-600"
                />

                <div>
                  <p className="text-sm font-bold text-rose-900">
                    Lighthouse result unavailable
                  </p>

                  <p className="mt-1 text-xs leading-5 text-rose-800">
                    Google PageSpeed Insights failed and the Local Lighthouse fallback also could not run. No replacement score has been invented.
                  </p>
                </div>
              </div>
            </div>
          )
        }

        {
          data.available
          &&
          (
            <>
              <div className="mt-5 flex flex-wrap gap-2">
                {["mobile", "desktop"].map(
                  (id) => (
                    <StrategyButton
                      key={id}
                      id={id}
                      active={strategy === id}
                      data={strategies[id]}
                      onClick={() =>
                        setStrategy(id)
                      }
                    />
                  )
                )}
              </div>

              <div className="mt-5 grid gap-5 rounded-3xl border border-slate-200 bg-slate-50 p-5 lg:grid-cols-[190px_1fr] lg:items-center">
                <div className="flex justify-center">
                  <ScoreRing
                    score={active.score}
                    status={active.overall_status}
                  />
                </div>

                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-xl font-bold text-slate-950">
                      {strategy === "mobile" ? "Mobile" : "Desktop"} Performance
                    </h3>

                    <SourceBadge
                      source={active.source}
                    />

                    <StatusBadge
                      status={active.overall_status || "info"}
                      compact
                    />
                  </div>

                  <p className="mt-2 text-sm font-semibold text-slate-700">
                    {active.score ?? "—"} / 100 · {active.score_label || "Unavailable"}
                  </p>

                  <p className="mt-2 max-w-3xl text-xs leading-5 text-slate-500">
                    {
                      active.source === "local_lighthouse"
                        ? "Google PageSpeed Insights was unavailable or rate-limited. This is a real Lighthouse score produced locally on this computer. It is accurate for this local lab environment, but can differ from Google's score because the hardware and network are different."
                        : "This score was returned by Google PageSpeed Insights / Lighthouse for this exact URL."
                    }
                  </p>

                  {
                    active.lighthouse_version
                    &&
                    (
                      <p className="mt-2 text-[10px] font-medium text-slate-400">
                        Lighthouse {active.lighthouse_version}
                      </p>
                    )
                  }
                </div>
              </div>
            </>
          )
        }
      </div>

      {
        data.available
        &&
        (
          <>
            <MetricsTable
              metrics={active.metrics || []}
            />

            <OpportunityTable
              opportunities={active.opportunities || []}
            />

            <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
                <h3 className="text-sm font-semibold text-slate-950">
                  Local Page Weight & Requests
                </h3>

                <p className="mt-1 text-[11px] text-slate-500">
                  Local request diagnostics are useful context only and do not determine the Lighthouse score.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] border-collapse text-left">
                  <thead>
                    <tr className="bg-slate-950 text-white">
                      <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Resource Type</th>
                      <th className="w-[180px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Requests</th>
                      <th className="w-[200px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.12em]">Transfer Size</th>
                    </tr>
                  </thead>

                  <tbody>
                    {resources.map(
                      (row) => (
                        <tr
                          key={row.type}
                          className="border-b border-slate-100 last:border-b-0"
                        >
                          <td className="px-4 py-3 text-xs font-semibold text-slate-900">
                            {row.type}
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-600">
                            {row.count}
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-600">
                            {row.size_display}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )
      }

      {
        errors.length > 0
        &&
        (
          <details className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <summary className="cursor-pointer list-none px-5 py-4 text-sm font-semibold text-slate-900">
              Why a score could not be retrieved
            </summary>

            <div className="space-y-2 border-t border-slate-200 p-4">
              {errors.map(
                ([key, value]) => (
                  <div
                    key={key}
                    className="rounded-xl bg-slate-50 p-3 text-[11px] leading-5 text-slate-600"
                  >
                    <strong className="capitalize text-slate-800">
                      {key.replace(/_/g, " ")}:
                    </strong>
                    {" "}
                    {value}
                  </div>
                )
              )}
            </div>
          </details>
        )
      }

      <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
        <div className="flex gap-3">
          <Info
            size={17}
            className="mt-0.5 shrink-0 text-sky-700"
          />

          <p className="text-[11px] leading-5 text-sky-900">
            {
              data.note
              ||
              "Google PageSpeed Insights is preferred. Local Lighthouse is used when Google cannot return a result."
            }
          </p>
        </div>
      </div>
    </section>
  );
}
