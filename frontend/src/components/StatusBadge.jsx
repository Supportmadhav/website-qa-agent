import { AlertTriangle, Check, Info, X } from "lucide-react";

const STYLES = {
  pass:
    "border-emerald-200 bg-emerald-50 text-emerald-700",

  warning:
    "border-amber-200 bg-amber-50 text-amber-700",

  fail:
    "border-rose-200 bg-rose-50 text-rose-700",

  info:
    "border-sky-200 bg-sky-50 text-sky-700",
};


export default function StatusBadge({
  status,
  compact = false,
}) {
  const normalized =
    status
    ||
    "info";

  const Icon = {
    pass: Check,
    warning: AlertTriangle,
    fail: X,
    info: Info,
  }[normalized] || Info;

  return (
    <span
      className={[
        "inline-flex items-center gap-1 rounded-full border font-bold uppercase tracking-wide",
        compact
          ? "px-2 py-0.5 text-[9px]"
          : "px-2.5 py-1 text-[10px]",
        STYLES[
          normalized
        ]
        ||
        STYLES.info,
      ].join(" ")}
    >
      <Icon size={compact ? 10 : 12} aria-hidden="true" />
      {normalized}
    </span>
  );
}
