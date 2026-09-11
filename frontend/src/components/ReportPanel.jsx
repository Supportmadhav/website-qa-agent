import {
  Download,
  ExternalLink,
  FileText,
  Filter,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import StatusBadge from "./StatusBadge";
import PageSpeedReport from "./PageSpeedReport";
import ImageOptimizationReport from "./ImageOptimizationReport";
import PageLinkListReport, {
  PageLinkTable,
} from "./PageLinkListReport";
import BlogPageReport from "./BlogPageReport";
import BrowserCompatibilityReport from "./BrowserCompatibilityReport";
import ReadableQaReport from "./ReadableQaReport";

import {
  buildDefaultReportName,
  downloadPdfReport,
} from "../utils/report";


const STATUS_FILTERS = [
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
];


function SummaryTable({
  summary,
  activeFilter,
  onFilter,
}) {
  const rows = [
    {
      id: "all",
      label: "Total Findings",
      value:
        summary.total
        ??
        0,
    },
    {
      id: "pass",
      label: "Pass",
      value:
        summary.pass
        ??
        0,
    },
    {
      id: "warning",
      label: "Warning",
      value:
        summary.warning
        ??
        0,
    },
    {
      id: "fail",
      label: "Fail",
      value:
        summary.fail
        ??
        0,
    },
    {
      id: "info",
      label: "Info",
      value:
        summary.info
        ??
        0,
    },
  ];

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200">
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="bg-slate-950 text-white">
            <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
              Report Summary
            </th>

            <th className="w-[140px] px-4 py-3 text-center text-[10px] font-bold uppercase tracking-[0.14em]">
              Count
            </th>
          </tr>
        </thead>

        <tbody>
          {rows.map(
            (row) => (
              <tr
                key={
                  row.id
                }
                className={[
                  "border-b border-slate-100 last:border-b-0",
                  activeFilter ===
                  row.id
                    ? "bg-indigo-50"
                    : "bg-white hover:bg-slate-50",
                ].join(" ")}
              >
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() =>
                      onFilter(
                        row.id
                      )
                    }
                    className="w-full text-left text-xs font-semibold text-slate-800"
                  >
                    {row.label}
                  </button>
                </td>

                <td className="px-4 py-3 text-center text-sm font-bold text-slate-950">
                  {row.value}
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>
    </div>
  );
}


function ReportInformationTable({
  report,
  reportName,
}) {
  const checkCount =
    report.check_summary?.total
    ??
    report.summary?.total
    ??
    report.total_selected
    ??
    0;

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200">
      <table className="w-full min-w-[760px] border-collapse text-left">
        <thead>
          <tr className="bg-slate-950 text-white">
            <th className="w-[190px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
              Report Information
            </th>

            <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
              Value
            </th>
          </tr>
        </thead>

        <tbody>
          <tr className="border-b border-slate-100">
            <td className="bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700">
              Report Name
            </td>

            <td className="px-4 py-3 text-xs font-semibold text-slate-950">
              {reportName}
            </td>
          </tr>

          <tr className="border-b border-slate-100">
            <td className="bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700">
              Page Title
            </td>

            <td className="px-4 py-3 text-xs text-slate-700">
              {
                report.page?.title
                ||
                "—"
              }
            </td>
          </tr>

          <tr className="border-b border-slate-100">
            <td className="bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700">
              Website
            </td>

            <td className="px-4 py-3">
              <a
                href={
                  report.page?.final_url
                }
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-700"
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
            </td>
          </tr>

          <tr className="border-b border-slate-100">
            <td className="bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700">
              HTTP Status
            </td>

            <td className="px-4 py-3 text-xs text-slate-700">
              {
                report.page?.http_status
                ??
                "—"
              }
            </td>
          </tr>

          <tr>
            <td className="bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700">
              Checks Scanned
            </td>

            <td className="px-4 py-3 text-xs text-slate-700">
              {checkCount}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}


function ImageAssetTable({
  assets,
  statusFilter,
}) {
  const filteredAssets =
    statusFilter ===
    "all"
      ? assets
      : assets.filter(
          (asset) =>
            asset.status ===
            statusFilter
        );

  if (
    !filteredAssets.length
  ) {
    return null;
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-950">
          Image Optimization — All Images
        </h3>

        <p className="mt-1 text-[11px] text-slate-500">
          Warning threshold: image file size greater than 300 KB.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1050px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-950 text-white">
              <th className="w-[65px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                #
              </th>

              <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                Image URL
              </th>

              <th className="w-[100px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                Format
              </th>

              <th className="w-[120px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                File Size
              </th>

              <th className="w-[115px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                Status
              </th>
            </tr>
          </thead>

          <tbody>
            {filteredAssets.map(
              (
                asset,
                index
              ) => (
                <tr
                  key={
                    `${asset.index}-${asset.url}-${index}`
                  }
                  className={[
                    "border-b border-slate-100 last:border-b-0",
                    asset.status ===
                    "warning"
                      ? "bg-amber-50/40"
                      : "hover:bg-slate-50",
                  ].join(" ")}
                >
                  <td className="px-4 py-3 align-top text-xs font-semibold text-slate-500">
                    {
                      asset.index
                      ??
                      index + 1
                    }
                  </td>

                  <td className="px-4 py-3 align-top">
                    {
                      asset.url
                      ? (
                        <a
                          href={
                            asset.url
                          }
                          target="_blank"
                          rel="noreferrer"
                          className="break-all text-xs font-medium leading-5 text-indigo-600 hover:text-indigo-700"
                        >
                          {
                            asset.url
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
                      asset.format
                      ||
                      "UNKNOWN"
                    }
                  </td>

                  <td className="px-4 py-3 align-top text-xs font-semibold text-slate-700">
                    {
                      asset.size_label
                      ||
                      "Unknown"
                    }
                  </td>

                  <td className="px-4 py-3 align-top">
                    <StatusBadge
                      status={
                        asset.status
                        ||
                        "info"
                      }
                      compact
                    />
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



function singleResultReport(
  report,
  result
) {
  const counts =
    result.counts
    ||
    {
      pass: 0,
      warning: 0,
      fail: 0,
      info: 0,
    };

  const findingTotal =
    (
      counts.pass
      ||
      0
    )
    +
    (
      counts.warning
      ||
      0
    )
    +
    (
      counts.fail
      ||
      0
    )
    +
    (
      counts.info
      ||
      0
    );

  const checkSummary = {
    total:
      1,

    pass:
      result.status ===
      "pass"
        ? 1
        : 0,

    warning:
      result.status ===
      "warning"
        ? 1
        : 0,

    fail:
      result.status ===
      "fail"
        ? 1
        : 0,
  };

  const findingSummary = {
    total:
      findingTotal,

    pass:
      counts.pass
      ||
      0,

    warning:
      counts.warning
      ||
      0,

    fail:
      counts.fail
      ||
      0,

    info:
      counts.info
      ||
      0,
  };

  return {
    ...report,

    selected_checks: [
      result.id,
    ],

    total_selected:
      1,

    check_summary:
      checkSummary,

    finding_summary:
      findingSummary,

    summary:
      checkSummary,

    results: [
      result,
    ],
  };
}


function ReportTabs({
  report,
  activeId,
  onChange,
}) {
  const results =
    report?.results
    ||
    [];

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-4 pt-4 sm:px-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400">
              Separate Reports
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Select a tab to view that test's report, filters and download option.
            </p>
          </div>

          <span className="rounded-full bg-blue-50 px-3 py-1.5 text-[10px] font-bold text-blue-700">
            {
              results.length
            } reports
          </span>
        </div>

        <div className="overflow-x-auto">
          <div className="flex min-w-max gap-1">
            {
              results.map(
                (result) => {
                  const active =
                    result.id ===
                    activeId;

                  return (
                    <button
                      key={
                        result.id
                      }
                      type="button"
                      onClick={() =>
                        onChange(
                          result.id
                        )
                      }
                      className={[
                        "relative inline-flex min-h-[46px] items-center gap-2 rounded-t-xl px-4 text-xs font-semibold transition",
                        active
                          ? "bg-white text-slate-950 shadow-[0_-1px_0_0_#e2e8f0,1px_0_0_0_#e2e8f0,-1px_0_0_0_#e2e8f0]"
                          : "text-slate-500 hover:bg-white/70 hover:text-slate-800",
                      ].join(" ")}
                    >
                      <span>
                        {
                          result.label
                        }
                      </span>

                      <StatusBadge
                        status={
                          result.status
                        }
                        compact
                      />

                      {
                        active
                        &&
                        (
                          <span className="absolute inset-x-0 bottom-0 h-0.5 bg-blue-600" />
                        )
                      }
                    </button>
                  );
                }
              )
            }
          </div>
        </div>
      </div>
    </section>
  );
}


export default function ReportPanel({
  report,
}) {
  const [
    activeReportId,
    setActiveReportId,
  ] = useState(
    () =>
      report?.results?.[
        0
      ]?.id
      ||
      ""
  );


  const [
    statusFilter,
    setStatusFilter,
  ] = useState(
    "all"
  );

  const [
    categoryFilter,
    setCategoryFilter,
  ] = useState(
    "all"
  );


  const categories =
    useMemo(
      () => [
        "all",
        ...Array.from(
          new Set(
            (
              report?.results
              ||
              []
            )
            .map(
              (result) =>
                result.category
            )
            .filter(Boolean)
          )
        ),
      ],
      [
        report,
      ]
    );


  const tableRows =
    useMemo(
      () => {
        const rows = [];

        for (
          const result of
          report?.results
          ||
          []
        ) {
          if (
            categoryFilter !==
            "all"
            &&
            result.category !==
            categoryFilter
          ) {
            continue;
          }

          const findings =
            result.findings
            ||
            [];

          for (
            const finding of
            findings
          ) {
            if (
              statusFilter !==
              "all"
              &&
              finding.status !==
              statusFilter
            ) {
              continue;
            }

            rows.push({
              moduleId:
                result.id,

              module:
                result.label,

              category:
                result.category,

              status:
                finding.status,

              item:
                finding.title
                ||
                result.label,

              details:
                finding.message
                ||
                "—",
            });
          }
        }

        return rows;
      },
      [
        report,
        statusFilter,
        categoryFilter,
      ]
    );


  const imageAssets =
    useMemo(
      () => (
        report?.results
        ||
        []
      )
      .filter(
        (result) =>
          result.id ===
          "images"
      )
      .flatMap(
        (result) =>
          result.image_assets
          ||
          []
      ),
      [
        report,
      ]
    );


  const reportResults =
    report?.results
    ||
    [];


  if (
    report
    &&
    reportResults.length > 1
  ) {
    const activeResult =
      reportResults.find(
        (result) =>
          result.id ===
          activeReportId
      )
      ||
      reportResults[
        0
      ];

    const activeReport =
      singleResultReport(
        report,
        activeResult
      );

    return (
      <section className="space-y-4">
        <ReportTabs
          report={
            report
          }
          activeId={
            activeResult.id
          }
          onChange={
            setActiveReportId
          }
        />

        <ReportPanel
          key={
            activeResult.id
          }
          report={
            activeReport
          }
        />
      </section>
    );
  }


  const pageSpeedResult =
    (
      report?.results
      ||
      []
    ).find(
      (result) =>
        result.id ===
        "page_speed"
    );


  const pageSpeedOnly =
    (
      report?.results
      ||
      []
    ).length === 1
    &&
    pageSpeedResult;


  if (
    report
    &&
    pageSpeedOnly
    &&
    pageSpeedResult
  ) {
    return (
      <PageSpeedReport
        report={
          report
        }
        result={
          pageSpeedResult
        }
      />
    );
  }


  const imageResult =
    (
      report?.results
      ||
      []
    ).find(
      (result) =>
        result.id ===
        "images"
    );


  const imageOnly =
    (
      report?.results
      ||
      []
    ).length === 1
    &&
    imageResult;


  if (
    report
    &&
    imageOnly
    &&
    imageResult
  ) {
    return (
      <ImageOptimizationReport
        report={
          report
        }
        result={
          imageResult
        }
      />
    );
  }


  const pageLinkResult =
    (
      report?.results
      ||
      []
    ).find(
      (result) =>
        result.id ===
        "page_link_list"
    );


  const pageLinkOnly =
    (
      report?.results
      ||
      []
    ).length === 1
    &&
    pageLinkResult;


  if (
    report
    &&
    pageLinkOnly
    &&
    pageLinkResult
  ) {
    return (
      <PageLinkListReport
        report={
          report
        }
        result={
          pageLinkResult
        }
      />
    );
  }


  const blogResult =
    (
      report?.results
      ||
      []
    ).find(
      (result) =>
        result.id ===
        "blog"
    );


  const blogOnly =
    (
      report?.results
      ||
      []
    ).length === 1
    &&
    blogResult;


  if (
    report
    &&
    blogOnly
    &&
    blogResult
  ) {
    return (
      <BlogPageReport
        report={
          report
        }
        result={
          blogResult
        }
      />
    );
  }


  const browserCompatibilityResult =
    (
      report?.results
      ||
      []
    ).find(
      (result) =>
        result.id ===
        "browser_compatibility"
    );


  const browserCompatibilityOnly =
    (
      report?.results
      ||
      []
    ).length === 1
    &&
    browserCompatibilityResult;


  if (
    report
    &&
    browserCompatibilityOnly
    &&
    browserCompatibilityResult?.browser_compatibility_data
  ) {
    return (
      <BrowserCompatibilityReport
        report={
          report
        }
        result={
          browserCompatibilityResult
        }
      />
    );
  }


  const simpleReadableResult =
    (
      report?.results
      ||
      []
    )[0];


  const useReadableReport =
    (
      report?.results
      ||
      []
    ).length === 1
    &&
    simpleReadableResult
    &&
    ![
      "page_speed",
      "images",
      "page_link_list",
      "blog",
      "browser_compatibility",
    ].includes(
      simpleReadableResult.id
    );


  if (
    report
    &&
    useReadableReport
  ) {
    return (
      <ReadableQaReport
        report={report}
        result={simpleReadableResult}
      />
    );
  }


  if (!report) {
    return (
      <section className="rounded-3xl border border-dashed border-slate-300 bg-white/70 px-6 py-16 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
          <FileText
            size={22}
          />
        </div>

        <h2 className="mt-4 text-base font-semibold text-slate-800">
          Report will appear here
        </h2>

        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
          Every QA result will be displayed in structured table format.
        </p>
      </section>
    );
  }


  const findingSummary =
    report.finding_summary
    ||
    {
      total: 0,
      pass: 0,
      warning: 0,
      fail: 0,
      info: 0,
    };


  const reportName =
    buildDefaultReportName(
      report
    );


  const showImageTable =
    imageAssets.length > 0
    &&
    (
      categoryFilter ===
      "all"
      ||
      categoryFilter ===
      "Site Integrity"
    );


  return (
    <section className="space-y-4">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
              QA Report
            </p>

            <h2 className="mt-1 text-lg font-semibold text-slate-950">
              {reportName}
            </h2>
          </div>

          <button
            type="button"
            onClick={() =>
              downloadPdfReport(
                report
              )
            }
            className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-xs font-semibold text-white transition hover:bg-indigo-600"
          >
            <Download
              size={15}
            />

            Download PDF Report
          </button>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.7fr_0.8fr]">
          <ReportInformationTable
            report={
              report
            }
            reportName={
              reportName
            }
          />

          <SummaryTable
            summary={
              findingSummary
            }
            activeFilter={
              statusFilter
            }
            onFilter={
              setStatusFilter
            }
          />
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2">
            {STATUS_FILTERS.map(
              (filter) => (
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
                    statusFilter ===
                    filter.id
                      ? "bg-slate-950 text-white"
                      : "bg-slate-50 text-slate-600 hover:bg-slate-100",
                  ].join(" ")}
                >
                  {
                    filter.label
                  }
                </button>
              )
            )}
          </div>

          <div className="flex items-center gap-2">
            <Filter
              size={14}
              className="text-slate-400"
            />

            <select
              value={
                categoryFilter
              }
              onChange={(event) =>
                setCategoryFilter(
                  event.target.value
                )
              }
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 outline-none focus:border-indigo-400"
            >
              {categories.map(
                (category) => (
                  <option
                    key={
                      category
                    }
                    value={
                      category
                    }
                  >
                    {
                      category ===
                      "all"
                        ? "All categories"
                        : category
                    }
                  </option>
                )
              )}
            </select>
          </div>
        </div>

        <p className="mt-2 text-[11px] text-slate-400">
          Showing {
            tableRows.length
          } QA finding(s).
        </p>
      </div>

      {
        showImageTable
        &&
        (
          <ImageAssetTable
            assets={
              imageAssets
            }
            statusFilter={
              statusFilter
            }
          />
        )
      }


      {
        (
          (
            report?.results
            ||
            []
          ).find(
            (result) =>
              result.id ===
              "content"
          )?.content_issues
          ||
          []
        ).length > 0
        &&
        (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
              <h3 className="text-sm font-semibold text-slate-950">
                Content & Spelling — Detailed Issues
              </h3>

              <p className="mt-1 text-[11px] text-slate-500">
                Exact incorrect text, suggested correction, location and website context.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[1120px] border-collapse text-left">
                <thead>
                  <tr className="bg-slate-950 text-white">
                    <th className="w-[95px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Type
                    </th>

                    <th className="w-[175px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Incorrect
                    </th>

                    <th className="w-[190px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Suggestion
                    </th>

                    <th className="w-[155px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Location
                    </th>

                    <th className="w-[170px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Rule
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Website Content
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {
                    (
                      (
                        report?.results
                        ||
                        []
                      ).find(
                        (result) =>
                          result.id ===
                          "content"
                      )?.content_issues
                      ||
                      []
                    ).map(
                      (
                        issue,
                        index
                      ) => (
                        <tr
                          key={
                            `${issue.type}-${issue.incorrect}-${issue.location}-${index}`
                          }
                          className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                        >
                          <td className="px-4 py-3 align-top text-xs font-semibold capitalize text-slate-700">
                            {issue.type}
                          </td>

                          <td className="px-4 py-3 align-top">
                            <span className="rounded-md bg-rose-50 px-2 py-1 font-mono text-xs font-semibold text-rose-700">
                              {issue.incorrect || "—"}
                            </span>
                          </td>

                          <td className="px-4 py-3 align-top">
                            <span className="rounded-md bg-emerald-50 px-2 py-1 font-mono text-xs font-semibold text-emerald-700">
                              {issue.suggestion || "Review manually"}
                            </span>
                          </td>

                          <td className="px-4 py-3 align-top text-xs font-medium text-slate-600">
                            {issue.location || "—"}
                          </td>

                          <td className="px-4 py-3 align-top text-xs font-medium text-slate-700">
                            {issue.rule || "—"}
                          </td>

                          <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                            {issue.context || "—"}
                          </td>
                        </tr>
                      )
                    )
                  }
                </tbody>
              </table>
            </div>
          </div>
        )
      }


      {
        (
          pageLinkResult?.page_links
          ||
          []
        ).length > 0
        &&
        (
          <PageLinkTable
            links={
              pageLinkResult.page_links
            }
          />
        )
      }


      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h3 className="text-sm font-semibold text-slate-950">
            QA Findings
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1100px] border-collapse text-left">
            <thead>
              <tr className="bg-slate-950 text-white">
                <th className="w-[190px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                  Module
                </th>

                <th className="w-[140px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                  Category
                </th>

                <th className="w-[110px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                  Status
                </th>

                <th className="w-[260px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                  Check / Item
                </th>

                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                  Result / Details
                </th>
              </tr>
            </thead>

            <tbody>
              {
                tableRows.length
                ? (
                  tableRows.map(
                    (
                      row,
                      index
                    ) => (
                      <tr
                        key={
                          `${row.moduleId}-${index}`
                        }
                        className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                      >
                        <td className="px-4 py-3 align-top text-xs font-semibold text-slate-900">
                          {
                            row.module
                          }
                        </td>

                        <td className="px-4 py-3 align-top text-xs text-slate-600">
                          {
                            row.category
                          }
                        </td>

                        <td className="px-4 py-3 align-top">
                          <StatusBadge
                            status={
                              row.status
                            }
                            compact
                          />
                        </td>

                        <td className="px-4 py-3 align-top text-xs font-semibold text-slate-800">
                          {
                            row.item
                          }
                        </td>

                        <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                          {
                            row.details
                          }
                        </td>
                      </tr>
                    )
                  )
                )
                : (
                  <tr>
                    <td
                      colSpan={
                        5
                      }
                      className="px-5 py-10 text-center text-sm text-slate-500"
                    >
                      No QA findings match the selected filters.
                    </td>
                  </tr>
                )
              }
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
