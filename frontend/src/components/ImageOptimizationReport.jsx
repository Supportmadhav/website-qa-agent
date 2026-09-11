import {
  Download,
  ExternalLink,
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Filter,
  Image as ImageIcon,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import StatusBadge from "./StatusBadge";

import {
  downloadPdfReport,
} from "../utils/report";


function getEffectiveStatus(
  item
) {
  if (
    item.status ===
    "fail"
  ) {
    return "fail";
  }

  if (
    item.oversized
    ||
    item.status ===
    "warning"
  ) {
    return "warning";
  }

  if (
    item.status ===
    "info"
  ) {
    return "info";
  }

  return "pass";
}


function getEffectiveIssue(
  item
) {
  const original =
    item.issue_text
    ||
    "";

  if (
    item.oversized
    &&
    !original.includes(
      "Oversized dimensions"
    )
  ) {
    if (
      original
      &&
      original !==
      "No detected issue"
    ) {
      return (
        `Oversized dimensions; ${original}`
      );
    }

    return "Oversized dimensions";
  }

  return (
    original
    ||
    "No detected issue"
  );
}


function countStatus(
  assets,
  status
) {
  return assets.filter(
    (item) =>
      getEffectiveStatus(
        item
      ) ===
      status
  ).length;
}


function countWhere(
  assets,
  predicate
) {
  return assets.filter(
    predicate
  ).length;
}



function SortableHeader({
  label,
  sortKey,
  sortConfig,
  onSort,
  className = "",
}) {
  const active =
    sortConfig.key ===
    sortKey;

  const Icon =
    active
      ? (
          sortConfig.direction ===
          "asc"
            ? ArrowUp
            : ArrowDown
        )
      : ArrowUpDown;

  return (
    <th
      className={[
        "px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]",
        className,
      ].join(" ")}
    >
      <button
        type="button"
        onClick={() =>
          onSort(
            sortKey
          )
        }
        className="inline-flex items-center gap-1.5 text-left text-white/90 transition hover:text-white"
      >
        <span>
          {label}
        </span>

        <Icon
          size={12}
          className={
            active
              ? "text-blue-300"
              : "text-slate-500"
          }
        />
      </button>
    </th>
  );
}


function compareValues(
  a,
  b,
  key
) {
  const statusOrder = {
    fail: 1,
    warning: 2,
    info: 3,
    pass: 4,
  };

  if (
    key ===
    "size_kb"
  ) {
    return (
      (
        a.size_kb
        ??
        -1
      )
      -
      (
        b.size_kb
        ??
        -1
      )
    );
  }

  if (
    key ===
    "status"
  ) {
    return (
      statusOrder[
        getEffectiveStatus(
          a
        )
      ]
      -
      statusOrder[
        getEffectiveStatus(
          b
        )
      ]
    );
  }

  if (
    key ===
    "index"
    ||
    key ===
    "natural_width"
    ||
    key ===
    "display_width"
  ) {
    return (
      (
        Number(
          a[
            key
          ]
        )
        ||
        0
      )
      -
      (
        Number(
          b[
            key
          ]
        )
        ||
        0
      )
    );
  }

  const first =
    String(
      key ===
      "issue_text"
        ? getEffectiveIssue(
            a
          )
        : (
            a[
              key
            ]
            ??
            ""
          )
    ).toLowerCase();

  const second =
    String(
      key ===
      "issue_text"
        ? getEffectiveIssue(
            b
          )
        : (
            b[
              key
            ]
            ??
            ""
          )
    ).toLowerCase();

  return first.localeCompare(
    second
  );
}


function SummaryCard({
  label,
  value,
  tone,
  active,
  onClick,
}) {
  const styles = {
    total:
      "border-slate-200 bg-white text-slate-950",

    pass:
      "border-emerald-200 bg-emerald-50 text-emerald-800",

    warning:
      "border-amber-200 bg-amber-50 text-amber-800",

    fail:
      "border-rose-200 bg-rose-50 text-rose-800",

    info:
      "border-sky-200 bg-sky-50 text-sky-800",
  };

  return (
    <button
      type="button"
      onClick={
        onClick
      }
      className={[
        "rounded-2xl border p-4 text-left transition",
        "hover:-translate-y-0.5 hover:shadow-sm",
        active
          ? "ring-4 ring-blue-100 border-blue-400"
          : "",
        styles[
          tone
        ]
        ||
        styles.total,
      ].join(" ")}
    >
      <p className="text-[10px] font-bold uppercase tracking-[0.13em] opacity-65">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold">
        {value}
      </p>
    </button>
  );
}



export default function ImageOptimizationReport({
  report,
  result,
}) {
  const assets =
    result.image_assets
    ||
    [];

  const [
    statusFilter,
    setStatusFilter,
  ] = useState(
    "all"
  );

  const [
    sortConfig,
    setSortConfig,
  ] = useState({
    key:
      "index",

    direction:
      "asc",
  });


  function handleSort(
    key
  ) {
    setSortConfig(
      (current) => ({
        key,

        direction:
          (
            current.key ===
            key
            &&
            current.direction ===
            "asc"
          )
            ? "desc"
            : "asc",
      })
    );
  }


  const filteredAssets =
    useMemo(
      () => {
        const filtered =
          statusFilter ===
          "all"
            ? [
                ...assets,
              ]
            : assets.filter(
                (item) =>
                  getEffectiveStatus(
                    item
                  ) ===
                  statusFilter
              );

        filtered.sort(
          (a, b) => {
            const result =
              compareValues(
                a,
                b,
                sortConfig.key
              );

            return (
              sortConfig.direction ===
              "asc"
                ? result
                : -result
            );
          }
        );

        return filtered;
      },
      [
        assets,
        statusFilter,
        sortConfig,
      ]
    );

  const total =
    assets.length;

  const pass =
    countStatus(
      assets,
      "pass"
    );

  const warning =
    countStatus(
      assets,
      "warning"
    );

  const fail =
    countStatus(
      assets,
      "fail"
    );

  const info =
    countStatus(
      assets,
      "info"
    );


  const issueSummary = [
    {
      label:
        "Images > 300 KB",

      value:
        countWhere(
          assets,
          (item) =>
            item.size_kb !== null
            &&
            item.size_kb !== undefined
            &&
            item.size_kb > 300
        ),
    },

    {
      label:
        "Missing ALT",

      value:
        countWhere(
          assets,
          (item) =>
            item.alt_state ===
            "Missing"
        ),
    },

    {
      label:
        "Empty ALT",

      value:
        countWhere(
          assets,
          (item) =>
            item.alt_state ===
            "Empty"
        ),
    },

    {
      label:
        "Oversized",

      value:
        countWhere(
          assets,
          (item) =>
            item.oversized
        ),
    },

    {
      label:
        "Non-Lazy Below Fold",

      value:
        countWhere(
          assets,
          (item) =>
            item.non_lazy_below_fold
        ),
    },

    {
      label:
        "Hidden",

      value:
        countWhere(
          assets,
          (item) =>
            item.hidden
        ),
    },

    {
      label:
        "Broken / HTTP Error",

      value:
        countWhere(
          assets,
          (item) =>
            item.broken
            ||
            (
              item.http_status !== null
              &&
              item.http_status !== undefined
              &&
              item.http_status >= 400
            )
        ),
    },

    {
      label:
        "Unknown Size",

      value:
        countWhere(
          assets,
          (item) =>
            item.size_bytes === null
            ||
            item.size_bytes === undefined
        ),
    },
  ];


  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                <ImageIcon
                  size={19}
                />
              </span>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  Image Optimization Report
                </p>

                <h2 className="mt-0.5 text-lg font-semibold text-slate-950">
                  Image Optimization - {
                    report.page?.title
                    ||
                    "Website"
                  }
                </h2>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
              <a
                href={
                  report.page?.final_url
                }
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 font-medium text-blue-600 hover:text-blue-700"
              >
                {
                  report.page?.final_url
                }

                <ExternalLink
                  size={12}
                />
              </a>

              <span>
                HTTP {
                  report.page?.http_status
                  ??
                  "—"
                }
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() =>
              downloadPdfReport(
                report
              )
            }
            className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-xs font-semibold text-white transition hover:bg-blue-600"
          >
            <Download
              size={15}
            />

            Download PDF Report
          </button>
        </div>


        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <SummaryCard
            label="Total Images"
            value={
              total
            }
            tone="total"
            active={
              statusFilter ===
              "all"
            }
            onClick={() =>
              setStatusFilter(
                "all"
              )
            }
          />

          <SummaryCard
            label="Pass"
            value={
              pass
            }
            tone="pass"
            active={
              statusFilter ===
              "pass"
            }
            onClick={() =>
              setStatusFilter(
                "pass"
              )
            }
          />

          <SummaryCard
            label="Warning"
            value={
              warning
            }
            tone="warning"
            active={
              statusFilter ===
              "warning"
            }
            onClick={() =>
              setStatusFilter(
                "warning"
              )
            }
          />

          <SummaryCard
            label="Fail"
            value={
              fail
            }
            tone="fail"
            active={
              statusFilter ===
              "fail"
            }
            onClick={() =>
              setStatusFilter(
                "fail"
              )
            }
          />

          <SummaryCard
            label="Info"
            value={
              info
            }
            tone="info"
            active={
              statusFilter ===
              "info"
            }
            onClick={() =>
              setStatusFilter(
                "info"
              )
            }
          />
        </div>


        <div className="mt-3 flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-[11px] font-medium text-slate-600">
            Image-level summary check:
            {" "}
            {pass} + {warning} + {fail} + {info} = {total}
          </div>

          <div className="flex items-center gap-2 text-[11px] font-semibold text-slate-600">
            <Filter
              size={13}
            />

            Showing {
              filteredAssets.length
            } of {
              total
            } images
          </div>
        </div>
      </div>


      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
          <h3 className="text-sm font-semibold text-slate-950">
            Issue Overview
          </h3>

          <p className="mt-1 text-[11px] text-slate-500">
            These issue counts can overlap because one image can have more than one issue.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[650px] border-collapse text-left">
            <thead>
              <tr className="bg-slate-950 text-white">
                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                  Issue
                </th>

                <th className="w-[140px] px-4 py-3 text-center text-[10px] font-bold uppercase tracking-[0.13em]">
                  Images
                </th>
              </tr>
            </thead>

            <tbody>
              {
                issueSummary.map(
                  (item) => (
                    <tr
                      key={
                        item.label
                      }
                      className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                    >
                      <td className="px-4 py-3 text-xs font-semibold text-slate-800">
                        {
                          item.label
                        }
                      </td>

                      <td className="px-4 py-3 text-center text-sm font-bold text-slate-950">
                        {
                          item.value
                        }
                      </td>
                    </tr>
                  )
                )
              }
            </tbody>
          </table>
        </div>
      </section>


      <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          {
            [
              ["all", "All"],
              ["pass", "Pass"],
              ["warning", "Warning"],
              ["fail", "Fail"],
              ["info", "Info"],
            ].map(
              ([
                value,
                label,
              ]) => (
                <button
                  key={
                    value
                  }
                  type="button"
                  onClick={() =>
                    setStatusFilter(
                      value
                    )
                  }
                  className={[
                    "rounded-lg px-3 py-2 text-xs font-semibold transition",
                    statusFilter ===
                    value
                      ? "bg-slate-950 text-white"
                      : "bg-slate-50 text-slate-600 hover:bg-slate-100",
                  ].join(" ")}
                >
                  {label}
                </button>
              )
            )
          }
        </div>
      </div>


      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
          <h3 className="text-sm font-semibold text-slate-950">
            All Images
          </h3>

          <p className="mt-1 text-[11px] text-slate-500">
            Showing {
              filteredAssets.length
            } of {
              total
            } images. Warning threshold for file size is greater than 300 KB.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1580px] border-collapse text-left">
            <thead>
              <tr className="bg-slate-950 text-white">
                <SortableHeader
                  label="#"
                  sortKey="index"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[60px]"
                />

                <SortableHeader
                  label="Image URL"
                  sortKey="url"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                />

                <SortableHeader
                  label="Format"
                  sortKey="format"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[90px]"
                />

                <SortableHeader
                  label="Size"
                  sortKey="size_kb"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[105px]"
                />

                <SortableHeader
                  label="ALT"
                  sortKey="alt_state"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[95px]"
                />

                <SortableHeader
                  label="Actual Dimensions"
                  sortKey="natural_width"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[135px]"
                />

                <SortableHeader
                  label="Displayed Dimensions"
                  sortKey="display_width"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[145px]"
                />

                <SortableHeader
                  label="Loading"
                  sortKey="loading"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[105px]"
                />

                <SortableHeader
                  label="Status"
                  sortKey="status"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[100px]"
                />

                <SortableHeader
                  label="Issue"
                  sortKey="issue_text"
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  className="w-[260px]"
                />
              </tr>
            </thead>

            <tbody>
              {
                filteredAssets.length
                ? (
                  filteredAssets.map(
                    (
                      item,
                      index
                    ) => (
                    <tr
                      key={
                        `${item.index}-${item.url}-${index}`
                      }
                      className={[
                        "border-b border-slate-100 last:border-b-0",
                        item.status ===
                        "warning"
                          ? "bg-amber-50/35"
                          : item.status ===
                            "fail"
                              ? "bg-rose-50/35"
                              : "hover:bg-slate-50",
                      ].join(" ")}
                    >
                      <td className="px-4 py-3 align-top text-xs font-semibold text-slate-400">
                        {
                          item.index
                          ??
                          index + 1
                        }
                      </td>

                      <td className="px-4 py-3 align-top">
                        {
                          item.url
                          ? (
                            <a
                              href={
                                item.url
                              }
                              target="_blank"
                              rel="noreferrer"
                              className="break-all text-xs font-medium leading-5 text-blue-600 hover:text-blue-700"
                            >
                              {
                                item.url
                              }
                            </a>
                          )
                          : (
                            <span className="text-xs text-slate-400">
                              No URL
                            </span>
                          )
                        }
                      </td>

                      <td className="px-4 py-3 align-top text-xs font-semibold text-slate-700">
                        {
                          item.format
                          ||
                          "UNKNOWN"
                        }
                      </td>

                      <td className="px-4 py-3 align-top text-xs font-semibold text-slate-700">
                        {
                          item.size_label
                          ||
                          "Unknown"
                        }
                      </td>

                      <td className="px-4 py-3 align-top text-xs text-slate-600">
                        {
                          item.alt_state
                          ||
                          "—"
                        }
                      </td>

                      <td className="px-4 py-3 align-top text-xs font-medium text-slate-700">
                        {
                          item.natural_dimensions
                          ||
                          "Unknown"
                        }
                      </td>

                      <td className="px-4 py-3 align-top text-xs font-medium text-slate-700">
                        {
                          item.display_dimensions
                          ||
                          "Unknown"
                        }
                      </td>

                      <td className="px-4 py-3 align-top text-xs text-slate-600">
                        {
                          item.loading
                          ||
                          "default"
                        }
                      </td>

                      <td className="px-4 py-3 align-top">
                        <StatusBadge
                          status={
                            getEffectiveStatus(
                              item
                            )
                          }
                          compact
                        />
                      </td>

                      <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                        {
                          getEffectiveIssue(
                            item
                          )
                        }
                      </td>
                    </tr>
                    )
                  )
                )
                : (
                  <tr>
                    <td
                      colSpan={10}
                      className="px-5 py-10 text-center text-sm text-slate-500"
                    >
                      No images match the selected status filter.
                    </td>
                  </tr>
                )
              }
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
