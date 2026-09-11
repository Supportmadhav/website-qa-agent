import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Download,
  ExternalLink,
  Link2,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import {
  downloadPdfReport,
  wrapLinkName,
} from "../utils/report";


function normalizeType(
  value
) {
  return (
    value ===
    "External"
      ? "external"
      : "internal"
  );
}


function SortHeader({
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


function openHttpLink(
  event,
  url
) {
  event.preventDefault();
  event.stopPropagation();

  const href = String(
    url
    ||
    ""
  ).trim();

  if (
    !/^https?:\/\//i.test(
      href
    )
  ) {
    return;
  }

  window.open(
    href,
    "_blank",
    "noopener,noreferrer"
  );
}


function compareRows(
  first,
  second,
  key
) {
  if (
    key ===
    "no"
  ) {
    return (
      Number(
        first.no
        ||
        0
      )
      -
      Number(
        second.no
        ||
        0
      )
    );
  }

  return String(
    first[
      key
    ]
    ||
    ""
  )
    .toLowerCase()
    .localeCompare(
      String(
        second[
          key
        ]
        ||
        ""
      ).toLowerCase()
    );
}


export function PageLinkTable({
  links,
}) {
  const [
    typeFilter,
    setTypeFilter,
  ] = useState(
    "all"
  );

  const [
    sortConfig,
    setSortConfig,
  ] = useState({
    key:
      "no",

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


  const visibleLinks =
    useMemo(
      () => {
        const rows =
          typeFilter ===
          "all"
            ? [
                ...links,
              ]
            : links.filter(
                (link) =>
                  normalizeType(
                    link.link_type
                  ) ===
                  typeFilter
              );

        rows.sort(
          (
            first,
            second
          ) => {
            const result =
              compareRows(
                first,
                second,
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

        return rows;
      },
      [
        links,
        typeFilter,
        sortConfig,
      ]
    );


  const internalCount =
    links.filter(
      (link) =>
        link.link_type ===
        "Internal"
    ).length;

  const externalCount =
    links.filter(
      (link) =>
        link.link_type ===
        "External"
    ).length;


  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-950">
              Page Link List
            </h3>

            <p className="mt-1 text-[11px] text-slate-500">
              Showing {
                visibleLinks.length
              } of {
                links.length
              } HTML links.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {
              [
                [
                  "all",
                  `All (${links.length})`,
                ],
                [
                  "internal",
                  `Internal (${internalCount})`,
                ],
                [
                  "external",
                  `External (${externalCount})`,
                ],
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
                      setTypeFilter(
                        value
                      )
                    }
                    className={[
                      "rounded-lg px-3 py-2 text-xs font-semibold transition",
                      typeFilter ===
                      value
                        ? "bg-slate-950 text-white"
                        : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100",
                    ].join(" ")}
                  >
                    {label}
                  </button>
                )
              )
            }
          </div>
        </div>
      </div>


      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] table-fixed border-collapse text-left">
          <thead>
            <tr className="bg-slate-950 text-white">
              <SortHeader
                label="No."
                sortKey="no"
                sortConfig={
                  sortConfig
                }
                onSort={
                  handleSort
                }
                className="w-[80px]"
              />

              <SortHeader
                label="URL"
                sortKey="url"
                sortConfig={
                  sortConfig
                }
                onSort={
                  handleSort
                }
                className="w-[46%]"
              />

              <SortHeader
                label="Link Name"
                sortKey="link_name"
                sortConfig={
                  sortConfig
                }
                onSort={
                  handleSort
                }
                className="w-[240px]"
              />

              <SortHeader
                label="Internal / External"
                sortKey="link_type"
                sortConfig={
                  sortConfig
                }
                onSort={
                  handleSort
                }
                className="w-[160px]"
              />
            </tr>
          </thead>

          <tbody>
            {
              visibleLinks.length
              ? (
                visibleLinks.map(
                  (
                    link,
                    index
                  ) => (
                    <tr
                      key={
                        `${link.no}-${link.url}-${index}`
                      }
                      className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                    >
                      <td className="px-4 py-3 align-top text-xs font-semibold text-slate-400">
                        {
                          link.no
                          ??
                          index + 1
                        }
                      </td>

                      <td className="px-4 py-3 align-top">
                        <a
                          href={
                            link.url
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(event) =>
                            openHttpLink(
                              event,
                              link.url
                            )
                          }
                          className="inline-flex max-w-full items-start gap-1 break-all text-xs font-medium leading-5 text-blue-600 hover:text-blue-700"
                        >
                          <span>
                            {
                              link.url
                            }
                          </span>

                          <ExternalLink
                            size={11}
                            className="mt-0.5 shrink-0"
                          />
                        </a>
                      </td>

                      <td className="w-[240px] max-w-[240px] px-4 py-3 align-top text-xs font-medium leading-5 text-slate-700">
                        <span className="block max-w-[240px] whitespace-pre-wrap break-words">
                          {
                            wrapLinkName(
                              link.link_name
                            )
                          }
                        </span>
                      </td>

                      <td className="w-[160px] px-4 py-3 align-top">
                        <span
                          className={[
                            "inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide",
                            link.link_type ===
                            "Internal"
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-violet-50 text-violet-700",
                          ].join(" ")}
                        >
                          {
                            link.link_type
                          }
                        </span>
                      </td>
                    </tr>
                  )
                )
              )
              : (
                <tr>
                  <td
                    colSpan={4}
                    className="px-5 py-10 text-center text-sm text-slate-500"
                  >
                    No links match the selected filter.
                  </td>
                </tr>
              )
            }
          </tbody>
        </table>
      </div>
    </section>
  );
}


export default function PageLinkListReport({
  report,
  result,
}) {
  const links =
    result.page_links
    ||
    [];

  const internalCount =
    links.filter(
      (link) =>
        link.link_type ===
        "Internal"
    ).length;

  const externalCount =
    links.filter(
      (link) =>
        link.link_type ===
        "External"
    ).length;


  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                <Link2
                  size={19}
                />
              </span>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  Link Inventory Report
                </p>

                <h2 className="mt-0.5 text-lg font-semibold text-slate-950">
                  Page Link List - {
                    report.page?.title
                    ||
                    "Website"
                  }
                </h2>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
              <span>
                Total HTML Links: {
                  links.length
                }
              </span>

              <span>
                Internal: {
                  internalCount
                }
              </span>

              <span>
                External: {
                  externalCount
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
      </div>

      <PageLinkTable
        links={
          links
        }
      />
    </section>
  );
}
