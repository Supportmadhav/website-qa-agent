import {
  CheckCheck,
  RotateCcw,
} from "lucide-react";

import CheckOption from "./CheckOption";


export default function CheckSelector({
  checks,
  selected,
  loading,
  onToggle,
  onSelectAll,
  onClear,
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-5">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-950">
              Testing options
            </h2>

            <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[10px] font-semibold text-indigo-700">
              {selected.size} selected
            </span>
          </div>

          <p className="mt-1 text-xs text-slate-500">
            All options stay visible in a compact grid. Only selected checks will run.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={onSelectAll}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-indigo-200 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <CheckCheck
              size={14}
            />
            Select all
          </button>

          <button
            type="button"
            disabled={loading}
            onClick={onClear}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-rose-200 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RotateCcw
              size={14}
            />
            Clear
          </button>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {checks.map(
          (check) => (
            <CheckOption
              key={check.id}
              check={check}
              selected={
                selected.has(
                  check.id
                )
              }
              disabled={loading}
              onToggle={onToggle}
            />
          )
        )}
      </div>
    </section>
  );
}
