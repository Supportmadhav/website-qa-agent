import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  AlertCircle,
  Check,
  ChevronDown,
  ClipboardCheck,
  Globe2,
  MonitorSmartphone,
  Rocket,
  ScanSearch,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";

import ReportPanel from "./components/ReportPanel";
import ResponsivePreviewStudio from "./components/ResponsivePreviewStudio";
import WebsiteAudit from "./components/WebsiteAudit";

import {
  CHECKS,
} from "./data/checks";

import {
  runSelectedScan,
} from "./services/api";



const CHECK_DESCRIPTIONS = {
  page_speed:
    "Performance timing, page weight and slow resources.",

  website_page_list:
    "Discover same-site HTML pages with page number, title and URL.",

  links:
    "Find working, blocked and broken links.",

  images:
    "Image URLs, sizes, formats, ALT and optimization.",

  meta:
    "SEO metadata, social tags and structured data.",

  sticky_header:
    "Sticky header behavior and overlap checks.",

  css_animation:
    "Animations, transitions and reduced-motion support.",

  browser_compatibility:
    "Chrome, Firefox and Edge checks.",

  google_translate:
    "Google Translate presence and functional verification.",

  whatsapp:
    "WhatsApp link format and configuration.",

  social_media:
    "Social links, targets and consistency.",

  contact_form:
    "Fields, labels, required values and anti-spam.",

  blog:
    "Blog archive, posts, images and pagination.",

  content:
    "Visible website content and spelling analysis.",

  layout_design:
    "Text, clipping, image distortion and CTA sizing.",
};


function SelectedChip({
  check,
  disabled,
  onRemove,
}) {
  const Icon =
    check.icon;

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() =>
        onRemove(
          check.id
        )
      }
      className="group inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <Icon
        size={14}
      />

      <span>
        {check.label}
      </span>

      <X
        size={13}
        className="text-blue-500 transition group-hover:text-blue-800"
      />
    </button>
  );
}


function CheckDropdown({
  selected,
  loading,
  onToggle,
}) {
  const [
    open,
    setOpen,
  ] = useState(
    false
  );

  const [
    search,
    setSearch,
  ] = useState("");

  const containerRef =
    useRef(
      null
    );


  useEffect(
    () => {
      function handleOutside(
        event
      ) {
        if (
          containerRef.current
          &&
          !containerRef.current.contains(
            event.target
          )
        ) {
          setOpen(
            false
          );
        }
      }

      document.addEventListener(
        "mousedown",
        handleOutside
      );

      return () =>
        document.removeEventListener(
          "mousedown",
          handleOutside
        );
    },
    []
  );


  const filteredChecks =
    useMemo(
      () => {
        const query =
          search
            .trim()
            .toLowerCase();

        if (!query) {
          return CHECKS;
        }

        return CHECKS.filter(
          (check) =>
            (
              check.label
              +
              " "
              +
              check.category
              +
              " "
              +
              (
                CHECK_DESCRIPTIONS[
                  check.id
                ]
                ||
                ""
              )
            )
            .toLowerCase()
            .includes(
              query
            )
        );
      },
      [
        search,
      ]
    );


  const groupedChecks =
    useMemo(
      () => {
        const groups = {};

        for (
          const check of
          filteredChecks
        ) {
          if (
            !groups[
              check.category
            ]
          ) {
            groups[
              check.category
            ] = [];
          }

          groups[
            check.category
          ].push(
            check
          );
        }

        return groups;
      },
      [
        filteredChecks,
      ]
    );


  return (
    <div
      ref={
        containerRef
      }
      className="relative"
    >
      <button
        type="button"
        disabled={loading}
        onClick={() =>
          setOpen(
            (current) =>
              !current
          )
        }
        className={[
          "flex min-h-[52px] w-full items-center justify-between gap-3 rounded-xl border bg-white px-4 text-left transition",
          "focus:outline-none focus:ring-4 focus:ring-blue-100",
          open
            ? "border-blue-500 shadow-[0_0_0_1px_rgba(59,130,246,0.08)]"
            : "border-slate-200 hover:border-blue-300",
          loading
            ? "cursor-not-allowed opacity-60"
            : "",
        ].join(" ")}
      >
        <div className="min-w-0">
          <p className="text-xs font-semibold text-slate-950">
            Select checks to include
          </p>

          <p className="mt-0.5 truncate text-[11px] text-slate-500">
            {
              selected.size
                ? `${selected.size} selected`
                : "Choose one or more checks"
            }
          </p>
        </div>

        <ChevronDown
          size={18}
          className={[
            "shrink-0 text-slate-400 transition-transform",
            open
              ? "rotate-180"
              : "",
          ].join(" ")}
        />
      </button>


      {
        open
        &&
        (
          <div className="absolute left-0 right-0 z-50 mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_24px_70px_rgba(15,23,42,0.18)]">
            <div className="border-b border-slate-100 p-3">
              <div className="relative">
                <Search
                  size={15}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  autoFocus
                  value={
                    search
                  }
                  onChange={
                    (event) =>
                      setSearch(
                        event.target.value
                      )
                  }
                  placeholder="Search QA checks..."
                  className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50"
                />
              </div>

              <div className="mt-2 flex items-center justify-between gap-3">
                <p className="text-[10px] font-medium text-slate-500">
                  Select any number of QA checks
                </p>

                <span className="rounded-full bg-blue-50 px-2 py-1 text-[10px] font-bold text-blue-700">
                  {selected.size} selected
                </span>
              </div>
            </div>


            <div className="max-h-[410px] overflow-y-auto p-3">
              {
                Object.keys(
                  groupedChecks
                ).length
                ? (
                  <div className="space-y-4">
                    {
                      Object.entries(
                        groupedChecks
                      ).map(
                        ([
                          category,
                          checks,
                        ]) => (
                          <div
                            key={
                              category
                            }
                          >
                            <p className="mb-2 px-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                              {category}
                            </p>

                            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                              {
                                checks.map(
                                  (check) => {
                                    const Icon =
                                      check.icon;

                                    const isSelected =
                                      selected.has(
                                        check.id
                                      );

                                    return (
                                      <button
                                        key={
                                          check.id
                                        }
                                        type="button"
                                        disabled={
                                          loading
                                        }
                                        onClick={() =>
                                          onToggle(
                                            check.id
                                          )
                                        }
                                        className={[
                                          "group relative flex min-h-[78px] items-start gap-3 rounded-xl border p-3 text-left transition",
                                          isSelected
                                            ? "border-blue-500 bg-blue-50"
                                            : "border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/40",
                                        ].join(" ")}
                                      >
                                        <span
                                          className={[
                                            "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                                            isSelected
                                              ? "bg-blue-600 text-white"
                                              : "bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-700",
                                          ].join(" ")}
                                        >
                                          <Icon
                                            size={15}
                                          />
                                        </span>

                                        <span className="min-w-0 flex-1">
                                          <span className="block text-xs font-semibold text-slate-900">
                                            {check.label}
                                          </span>

                                          <span className="mt-1 block text-[10px] leading-4 text-slate-500">
                                            {
                                              CHECK_DESCRIPTIONS[
                                                check.id
                                              ]
                                            }
                                          </span>
                                        </span>

                                        <span
                                          className={[
                                            "absolute right-2.5 top-2.5 flex h-5 w-5 items-center justify-center rounded-md border",
                                            isSelected
                                              ? "border-blue-600 bg-blue-600 text-white"
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
                                )
                              }
                            </div>
                          </div>
                        )
                      )
                    }
                  </div>
                )
                : (
                  <div className="px-4 py-10 text-center text-xs text-slate-500">
                    No QA checks match your search.
                  </div>
                )
              }
            </div>


          </div>
        )
      }
    </div>
  );
}


export default function App() {
  const [
    activeWorkspace,
    setActiveWorkspace,
  ] = useState(
    "testing"
  );


  const [
    url,
    setUrl,
  ] = useState("");

  const [
    selected,
    setSelected,
  ] = useState(
    () =>
      new Set()
  );

  const [
    loading,
    setLoading,
  ] = useState(
    false
  );

  const [
    report,
    setReport,
  ] = useState(
    null
  );

  const [
    error,
    setError,
  ] = useState("");

  const selectedChecks =
    useMemo(
      () =>
        CHECKS.filter(
          (check) =>
            selected.has(
              check.id
            )
        ),
      [
        selected,
      ]
    );


  const canRun =
    Boolean(
      url.trim()
      &&
      selected.size > 0
      &&
      !loading
    );


  function toggleCheck(
    checkId
  ) {
    if (loading) {
      return;
    }

    setSelected(
      (current) => {
        const next =
          new Set(
            current
          );

        if (
          next.has(
            checkId
          )
        ) {
          next.delete(
            checkId
          );
        } else {
          next.add(
            checkId
          );
        }

        return next;
      }
    );
  }


  function selectAllChecks() {
    if (loading) {
      return;
    }

    setSelected(
      new Set(
        CHECKS.map(
          (check) =>
            check.id
        )
      )
    );
  }


  function clearSelected() {
    if (loading) {
      return;
    }

    setSelected(
      new Set()
    );
  }


  async function runScan() {
    if (!canRun) {
      return;
    }

    setLoading(
      true
    );

    setError("");
    setReport(null);

    try {
      const checks =
        selectedChecks.map(
          (check) =>
            check.id
        );

      const result =
        await runSelectedScan(
          url,
          checks
        );

      setReport(
        result
      );

    } catch (
      scanError
    ) {
      setError(
        scanError.message
        ||
        "The scan could not be completed."
      );

    } finally {
      setLoading(
        false
      );
    }
  }


  return (
    <main className="min-h-screen bg-[#f8f9ff] text-slate-950">
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-white shadow-sm">
              <ScanSearch
                size={18}
              />
            </span>

            <div>
              <p className="font-display text-sm font-bold tracking-tight text-slate-950">
                Website QA Agent
              </p>

              <p className="hidden text-[10px] text-slate-400 sm:block">
                Precision automated website testing
              </p>
            </div>
          </div>

          <nav className="hidden items-center rounded-xl border border-slate-200 bg-slate-50 p-1 md:flex">
            <button
              type="button"
              onClick={() =>
                setActiveWorkspace(
                  "testing"
                )
              }
              className={[
                "inline-flex min-h-[38px] items-center gap-2 rounded-lg px-4 text-xs font-bold transition",
                activeWorkspace ===
                "testing"
                  ? "bg-white text-slate-950 shadow-sm"
                  : "text-slate-500 hover:text-slate-800",
              ].join(" ")}
            >
              <ScanSearch
                size={14}
              />
              QA Testing
            </button>

            <button
              type="button"
              onClick={() =>
                setActiveWorkspace(
                  "audit"
                )
              }
              className={[
                "inline-flex min-h-[38px] items-center gap-2 rounded-lg px-4 text-xs font-bold transition",
                activeWorkspace ===
                "audit"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-800",
              ].join(" ")}
            >
              <ClipboardCheck
                size={14}
              />
              Website Audit
            </button>

            <button
              type="button"
              onClick={() =>
                setActiveWorkspace(
                  "responsive"
                )
              }
              className={[
                "inline-flex min-h-[38px] items-center gap-2 rounded-lg px-4 text-xs font-bold transition",
                activeWorkspace ===
                "responsive"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-800",
              ].join(" ")}
            >
              <MonitorSmartphone
                size={14}
              />
              Responsive Studio
            </button>
          </nav>


          <div className="flex items-center gap-2">
            <span className="hidden rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-blue-700 sm:inline-flex">
              {
                activeWorkspace ===
                "testing"
                  ? "QA Testing"
                  : activeWorkspace ===
                    "audit"
                    ? "Website Audit"
                    : "Responsive"
              }
            </span>

            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
              QA
            </span>
          </div>
        </div>
      </header>


      <div className="border-b border-slate-200 bg-white px-4 py-2 md:hidden">
        <div className="mx-auto grid max-w-[1280px] grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() =>
              setActiveWorkspace(
                "testing"
              )
            }
            className={[
              "inline-flex min-h-[40px] items-center justify-center gap-2 rounded-xl text-xs font-bold transition",
              activeWorkspace ===
              "testing"
                ? "bg-slate-950 text-white"
                : "bg-slate-100 text-slate-600",
            ].join(" ")}
          >
            <ScanSearch
              size={14}
            />
            QA Testing
          </button>

          <button
            type="button"
            onClick={() =>
              setActiveWorkspace(
                "audit"
              )
            }
            className={[
              "inline-flex min-h-[40px] items-center justify-center gap-2 rounded-xl text-xs font-bold transition",
              activeWorkspace ===
              "audit"
                ? "bg-emerald-600 text-white"
                : "bg-slate-100 text-slate-600",
            ].join(" ")}
          >
            <ClipboardCheck
              size={14}
            />
            Audit
          </button>

          <button
            type="button"
            onClick={() =>
              setActiveWorkspace(
                "responsive"
              )
            }
            className={[
              "inline-flex min-h-[40px] items-center justify-center gap-2 rounded-xl text-xs font-bold transition",
              activeWorkspace ===
              "responsive"
                ? "bg-blue-600 text-white"
                : "bg-slate-100 text-slate-600",
            ].join(" ")}
          >
            <MonitorSmartphone
              size={14}
            />
            Responsive
          </button>
        </div>
      </div>


      {
        activeWorkspace ===
        "testing"
        ? (
          <div className="mx-auto max-w-[1280px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <section className="relative overflow-hidden rounded-[28px] bg-[linear-gradient(135deg,#0f172a_0%,#172554_48%,#1d4ed8_100%)] p-6 text-white shadow-[0_24px_70px_rgba(30,64,175,0.20)] sm:p-8 lg:p-10">
          <div className="absolute -right-16 -top-24 h-72 w-72 rounded-full bg-blue-400/20 blur-3xl" />
          <div className="absolute -bottom-24 -left-20 h-64 w-64 rounded-full bg-indigo-400/20 blur-3xl" />

          <div className="relative z-10 grid gap-7 lg:grid-cols-[1fr_1.05fr] lg:items-center">
            <div className="max-w-xl">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl border border-white/15 bg-white/10 backdrop-blur">
                <Globe2
                  size={24}
                />
              </div>

              <h1 className="font-display text-3xl font-bold tracking-[-0.03em] text-white sm:text-4xl">
                Start a new website scan
              </h1>

              <p className="mt-3 max-w-lg text-sm leading-6 text-blue-100/80">
                Enter a website URL and choose one, several, or all available QA checks in a single scan.
              </p>
            </div>


            <form
              onSubmit={
                (event) => {
                  event.preventDefault();
                  runScan();
                }
              }
              className="rounded-2xl border border-white/15 bg-white/10 p-3 backdrop-blur-xl"
            >
              <div className="flex flex-col gap-3 sm:flex-row">
                <div className="relative min-w-0 flex-1">
                  <Globe2
                    size={16}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                  />

                  <input
                    value={
                      url
                    }
                    disabled={
                      loading
                    }
                    onChange={
                      (event) =>
                        setUrl(
                          event.target.value
                        )
                    }
                    placeholder="https://example.com"
                    className="h-12 w-full rounded-xl border-0 bg-white pl-11 pr-4 text-sm text-slate-950 outline-none ring-0 transition placeholder:text-slate-400 focus:ring-4 focus:ring-blue-300/30 disabled:opacity-60"
                  />
                </div>

                <button
                  type="submit"
                  disabled={
                    !canRun
                  }
                  className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-[linear-gradient(135deg,#3b82f6,#6366f1)] px-6 text-sm font-bold text-white shadow-[0_10px_24px_rgba(59,130,246,0.35)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_30px_rgba(59,130,246,0.42)] disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0"
                >
                  {
                    loading
                    ? (
                      <>
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                        Scanning
                      </>
                    )
                    : (
                      <>
                        <Rocket
                          size={16}
                        />

                        Run {
                          selected.size
                        } {
                          selected.size === 1
                            ? "Check"
                            : "Checks"
                        }
                      </>
                    )
                  }
                </button>
              </div>
            </form>
          </div>
        </section>


        {
          error
          &&
          (
            <div className="mt-4 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              <AlertCircle
                size={18}
                className="mt-0.5 shrink-0"
              />

              <span>
                {error}
              </span>
            </div>
          )
        }


        <section className="mt-7 rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.05)] sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="flex items-center gap-2.5">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                  <ShieldCheck
                    size={18}
                  />
                </span>

                <div>
                  <h2 className="font-display text-lg font-bold tracking-tight text-slate-950">
                    Testing options
                  </h2>

                  <p className="mt-0.5 text-xs text-slate-500">
                    Choose one, several, or all available checks for each scan.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="rounded-full bg-blue-50 px-3 py-1.5 text-[11px] font-bold text-blue-700">
                {selected.size} selected
              </span>

              <button
                type="button"
                disabled={
                  loading
                  ||
                  selected.size ===
                    CHECKS.length
                }
                onClick={
                  selectAllChecks
                }
                className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Select all
              </button>

              <button
                type="button"
                disabled={
                  loading
                  ||
                  selected.size === 0
                }
                onClick={
                  clearSelected
                }
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:border-rose-200 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Clear
              </button>
            </div>
          </div>


          <div className="mt-5">
            <CheckDropdown
              selected={
                selected
              }
              loading={
                loading
              }
              onToggle={
                toggleCheck
              }
            />
          </div>


          <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                Selected checks
              </p>

              <p className="text-[10px] font-semibold text-slate-400">
                {selected.size} item{selected.size === 1 ? "" : "s"}
              </p>
            </div>

            {
              selectedChecks.length
              ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {
                    selectedChecks.map(
                      (check) => (
                        <SelectedChip
                          key={
                            check.id
                          }
                          check={
                            check
                          }
                          disabled={
                            loading
                          }
                          onRemove={
                            toggleCheck
                          }
                        />
                      )
                    )
                  }
                </div>
              )
              : (
                <div className="mt-3 rounded-xl border border-dashed border-slate-300 bg-white px-4 py-5 text-center text-xs text-slate-500">
                  No checks selected. Open the selector above and choose any checks you want to run.
                </div>
              )
            }
          </div>
        </section>


        <div className="mt-7">
          <ReportPanel
            report={
              report
            }
          />
        </div>
          </div>
        )
        : activeWorkspace ===
          "audit"
          ? (
            <WebsiteAudit />
          )
          : (
            <ResponsivePreviewStudio />
          )
      }
    </main>
  );
}
