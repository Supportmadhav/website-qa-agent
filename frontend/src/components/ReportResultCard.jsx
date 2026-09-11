import StatusBadge from "./StatusBadge";


function Finding({
  finding,
}) {
  const dotClass = {
    pass:
      "bg-emerald-500",
    warning:
      "bg-amber-500",
    fail:
      "bg-rose-500",
    info:
      "bg-sky-500",
  }[
    finding.status
  ]
  ||
  "bg-slate-400";

  return (
    <div className="flex gap-3 rounded-xl border border-slate-100 bg-slate-50/70 p-3">
      <span
        className={[
          "mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full",
          dotClass,
        ].join(" ")}
      />

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-xs font-semibold text-slate-800">
            {finding.title}
          </p>

          <StatusBadge
            status={
              finding.status
            }
            compact
          />
        </div>

        {finding.message && (
          <p className="mt-1 text-xs leading-5 text-slate-600">
            {finding.message}
          </p>
        )}
      </div>
    </div>
  );
}


export default function ReportResultCard({
  result,
}) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="flex flex-col gap-3 border-b border-slate-100 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-950">
              {result.label}
            </h3>

            <StatusBadge
              status={
                result.status
              }
            />
          </div>

          <p className="mt-1 text-xs text-slate-500">
            {result.category}
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5 text-[10px] font-semibold">
          {!!result.counts?.pass && (
            <span className="rounded-lg bg-emerald-50 px-2 py-1 text-emerald-700">
              {result.counts.pass} pass
            </span>
          )}

          {!!result.counts?.warning && (
            <span className="rounded-lg bg-amber-50 px-2 py-1 text-amber-700">
              {result.counts.warning} warning
            </span>
          )}

          {!!result.counts?.fail && (
            <span className="rounded-lg bg-rose-50 px-2 py-1 text-rose-700">
              {result.counts.fail} fail
            </span>
          )}
        </div>
      </div>

      <div className="space-y-2 p-4">
        {result.findings?.map(
          (finding, index) => (
            <Finding
              key={
                `${result.id}-${index}`
              }
              finding={finding}
            />
          )
        )}
      </div>
    </article>
  );
}
