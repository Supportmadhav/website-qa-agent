import {
  Check,
} from "lucide-react";


export default function CheckOption({
  check,
  selected,
  disabled,
  onToggle,
}) {
  const Icon =
    check.icon;

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() =>
        onToggle(
          check.id
        )
      }
      className={[
        "group flex min-h-[66px] items-center gap-3 rounded-2xl border px-3.5 py-3 text-left transition-all",
        "focus:outline-none focus:ring-4 focus:ring-indigo-100",
        selected
          ? "border-indigo-500 bg-indigo-50 shadow-sm"
          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
        disabled
          ? "cursor-not-allowed opacity-60"
          : "cursor-pointer",
      ].join(" ")}
    >
      <span
        className={[
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition",
          selected
            ? "bg-indigo-600 text-white"
            : "bg-slate-100 text-slate-500 group-hover:bg-slate-200",
        ].join(" ")}
      >
        <Icon
          size={17}
        />
      </span>

      <span className="min-w-0 flex-1">
        <span className="block truncate text-xs font-semibold text-slate-900">
          {check.label}
        </span>

        <span className="mt-0.5 block truncate text-[10px] font-medium uppercase tracking-wide text-slate-400">
          {check.category}
        </span>
      </span>

      <span
        className={[
          "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border",
          selected
            ? "border-indigo-600 bg-indigo-600 text-white"
            : "border-slate-300 bg-white text-transparent",
        ].join(" ")}
      >
        <Check
          size={12}
          strokeWidth={3}
        />
      </span>
    </button>
  );
}
