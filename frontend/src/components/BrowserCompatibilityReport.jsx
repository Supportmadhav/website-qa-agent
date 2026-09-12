import {
  Download,
  ExternalLink,
  Globe2,
  Info,
} from "lucide-react";

import {
  Fragment,
  useMemo,
  useState,
} from "react";

import StatusBadge from "./StatusBadge";

import {
  downloadPdfReport,
} from "../utils/report";


const FILTERS = [
  {
    id: "attention",
    label: "Needs attention",
  },
  {
    id: "all",
    label: "All",
  },
  {
    id: "pass",
    label: "Pass",
  },
  {
    id: "warning",
    label: "Warning",
  },
  {
    id: "fail",
    label: "Fail",
  },
  {
    id: "info",
    label: "Info",
  },
  {
    id: "manual",
    label: "Manual",
  },
];


function MatrixBadge({
  status,
}) {
  if (
    status ===
    "manual"
  ) {
    return (
      <span className="inline-flex rounded-full border border-violet-200 bg-violet-50 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-violet-700">
        Manual
      </span>
    );
  }

  return (
    <StatusBadge
      status={
        status
        ||
        "info"
      }
      compact
    />
  );
}


function BrowserHeader({
  browser,
}) {
  return (
    <div className="min-w-[195px]">
      <div className="font-semibold text-white">
        {
          browser.name
        }
      </div>

      <div className="mt-1 text-[9px] font-medium normal-case tracking-normal text-slate-400">
        {
          browser.version
            ? `v${browser.version}`
            : browser.engine
        }
      </div>
    </div>
  );
}


function ResultCell({
  cell,
}) {
  const status =
    cell?.status
    ||
    "info";

  const detail =
    cell?.detail
    ||
    "Not available.";

  return (
    <div className="min-w-[195px]">
      <MatrixBadge
        status={
          status
        }
      />

      <p className="mt-2 text-[11px] leading-5 text-slate-600">
        {detail}
      </p>
    </div>
  );
}


function CompatibilityTable({
  browsers,
  rows,
  source,
  activeFilter,
  showGroups = false,
}) {
  const visibleRows =
    useMemo(
      () => {
        if (
          activeFilter ===
          "all"
        ) {
          return rows;
        }

        return rows.filter(
          (row) =>
            browsers.some(
              (browser) => {
                const cell =
                  source(
                    browser,
                    row
                  );

                return activeFilter === "attention"
                  ? cell?.status === "warning" || cell?.status === "fail"
                  : cell?.status === activeFilter;
              }
            )
        );
      },
      [
        browsers,
        rows,
        source,
        activeFilter,
      ]
    );


  if (
    !visibleRows.length
  ) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-10 text-center text-sm text-slate-500">
        No criteria match the selected status filter.
      </div>
    );
  }


  let lastGroup = null;

  return (
    <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[1100px] border-collapse text-left">
        <thead>
          <tr className="bg-slate-950 text-white">
            <th className="sticky left-0 z-20 w-[285px] min-w-[285px] bg-slate-950 px-4 py-4 text-[10px] font-bold uppercase tracking-[0.13em]">
              Criteria
            </th>

            {
              browsers.map(
                (browser) => (
                  <th
                    key={
                      browser.id
                    }
                    className="min-w-[220px] px-4 py-4 align-top text-[10px] font-bold uppercase tracking-[0.13em]"
                  >
                    <BrowserHeader
                      browser={
                        browser
                      }
                    />
                  </th>
                )
              )
            }
          </tr>
        </thead>

        <tbody>
          {
            visibleRows.map(
              (
                row,
                index
              ) => {
                const groupChanged =
                  (
                    showGroups
                    &&
                    row.group
                    &&
                    row.group !==
                    lastGroup
                  );

                if (
                  groupChanged
                ) {
                  lastGroup =
                    row.group;
                }

                return (
                  <Fragment
                    key={
                      `${row.id}-${index}`
                    }
                  >
                    {
                      groupChanged
                      &&
                      (
                        <tr
                          key={
                            `group-${row.group}`
                          }
                        >
                          <td
                            colSpan={
                              browsers.length
                              +
                              1
                            }
                            className="border-y border-slate-200 bg-slate-100 px-4 py-3 text-[10px] font-bold uppercase tracking-[0.15em] text-slate-500"
                          >
                            {
                              row.group
                            }
                          </td>
                        </tr>
                      )
                    }

                    <tr
                      className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50/50"
                    >
                      <td className="sticky left-0 z-10 bg-white px-4 py-4 align-top text-xs font-semibold leading-5 text-slate-800">
                        {
                          row.label
                        }
                      </td>

                      {
                        browsers.map(
                          (browser) => (
                            <td
                              key={
                                `${row.id}-${browser.id}`
                              }
                              className="px-4 py-4 align-top"
                            >
                              <ResultCell
                                cell={
                                  source(
                                    browser,
                                    row
                                  )
                                }
                              />
                            </td>
                          )
                        )
                      }
                    </tr>
                  </Fragment>
                );
              }
            )
          }
        </tbody>
      </table>
    </div>
  );
}


export default function BrowserCompatibilityReport({
  report,
  result,
}) {
  const data =
    result.browser_compatibility_data
    ||
    {};

  const browsers =
    data.browsers
    ||
    [];

  const overviewRows =
    data.overview_rows
    ||
    [];

  const criteria =
    data.criteria
    ||
    [];

  const notes =
    data.notes
    ||
    [];

  const [
    statusFilter,
    setStatusFilter,
  ] = useState(
    () => {
      const hasAttention = criteria.some(row => browsers.some(browser =>
        ["warning", "fail"].includes(browser.criteria?.[row.id]?.status)
      ));
      const allPassed = criteria.length > 0 && browsers.length > 0
        && criteria.every(row => browsers.every(browser =>
          browser.criteria?.[row.id]?.status === "pass"
        ));
      return hasAttention ? "attention" : allPassed ? "summary" : "all";
    }
  );


  const statusCounts =
    useMemo(
      () => {
        const counts = {
          pass: 0,
          warning: 0,
          fail: 0,
          info: 0,
          manual: 0,
        };

        for (
          const row of criteria
        ) {
          for (
            const browser of browsers
          ) {
            const status =
              browser.criteria?.[
                row.id
              ]?.status;

            if (
              status
              &&
              Object.prototype.hasOwnProperty.call(
                counts,
                status
              )
            ) {
              counts[
                status
              ] += 1;
            }
          }
        }

        return counts;
      },
      [
        browsers,
        criteria,
      ]
    );


  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                <Globe2
                  size={19}
                />
              </span>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  Browser Compatibility Report
                </p>

                <h2 className="mt-0.5 text-lg font-semibold text-slate-950">
                  Browser Compatibility - {
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
                  ||
                  "—"
                }

                <ExternalLink
                  size={12}
                />
              </a>

              <span>
                Browsers tested: {
                  browsers.length
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


        <div className="mt-5 flex flex-wrap gap-2">
          {
            FILTERS.map(
              (filter) => {
                const active =
                  statusFilter ===
                  filter.id;

                const count =
                  filter.id === "attention"
                    ? statusCounts.warning + statusCounts.fail
                    : filter.id ===
                  "all"
                    ? (
                        statusCounts.pass
                        +
                        statusCounts.warning
                        +
                        statusCounts.fail
                        +
                        statusCounts.info
                        +
                        statusCounts.manual
                      )
                    : statusCounts[
                        filter.id
                      ];

                return (
                  <button
                    key={
                      filter.id
                    }
                    type="button"
                    onClick={() =>
                      setStatusFilter(
                        filter.id
                      )
                    }
                    className={[
                      "rounded-lg px-3 py-2 text-xs font-semibold transition",
                      active
                        ? "bg-slate-950 text-white"
                        : "bg-slate-50 text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100",
                    ].join(" ")}
                  >
                    {
                      filter.label
                    }
                    {" "}
                    ({
                      count
                    })
                  </button>
                );
              }
            )
          }
        </div>
      </div>


      <section className="space-y-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">
            Browser Overview
          </h3>

          <p className="mt-1 text-[11px] text-slate-500">
            Browser names are horizontal; key compatibility checks are vertical.
          </p>
        </div>

        <CompatibilityTable
          browsers={
            browsers
          }
          rows={
            overviewRows
          }
          activeFilter="all"
          showGroups={
            false
          }
          source={
            (
              browser,
              row
            ) =>
              browser.summary?.[
                row.id
              ]
          }
        />
      </section>


      {statusFilter === "summary" ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-800">
          <p className="font-semibold">All detailed browser criteria passed.</p>
          <button type="button" onClick={() => setStatusFilter("all")}
            className="mt-2 text-xs font-bold underline">Show all checks</button>
        </div>
      ) : <section className="space-y-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">
            Detailed Compatibility Matrix
          </h3>

          <p className="mt-1 text-[11px] text-slate-500">
            Criteria are grouped by layout, functionality, performance, CSS/HTML, JavaScript APIs, accessibility and error handling.
          </p>
        </div>

        <CompatibilityTable
          browsers={
            browsers
          }
          rows={
            criteria
          }
          activeFilter={
            statusFilter
          }
          showGroups
          source={
            (
              browser,
              row
            ) =>
              browser.criteria?.[
                row.id
              ]
          }
        />
      </section>}


      {
        notes.length > 0
        &&
        (
          <section className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
            <div className="flex gap-3">
              <Info
                size={17}
                className="mt-0.5 shrink-0 text-sky-700"
              />

              <div className="space-y-2">
                {
                  notes.map(
                    (
                      note,
                      index
                    ) => (
                      <p
                        key={
                          index
                        }
                        className="text-[11px] leading-5 text-sky-900"
                      >
                        {note}
                      </p>
                    )
                  )
                }
              </div>
            </div>
          </section>
        )
      }
    </section>
  );
}
