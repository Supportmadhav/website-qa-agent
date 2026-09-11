import {
  Download,
  ExternalLink,
  FileText,
  Newspaper,
} from "lucide-react";

import StatusBadge from "./StatusBadge";

import {
  downloadPdfReport,
} from "../utils/report";


function InfoRow({
  label,
  children,
}) {
  return (
    <tr className="border-b border-slate-100 last:border-b-0">
      <td className="w-[190px] bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700">
        {label}
      </td>

      <td className="px-4 py-3 text-xs text-slate-700">
        {children}
      </td>
    </tr>
  );
}


export default function BlogPageReport({
  report,
  result,
}) {
  const data =
    result.blog_data
    ||
    {};

  const posts =
    data.posts
    ||
    [];

  const detected =
    Boolean(
      data.detected
      &&
      data.blog_url
    );


  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                <Newspaper
                  size={19}
                />
              </span>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  Blog Page Report
                </p>

                <h2 className="mt-0.5 text-lg font-semibold text-slate-950">
                  Blog Page - {
                    report.page?.title
                    ||
                    "Website"
                  }
                </h2>
              </div>
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


        <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="bg-slate-950 text-white">
                <th className="w-[190px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                  Blog Information
                </th>

                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                  Value
                </th>
              </tr>
            </thead>

            <tbody>
              <InfoRow
                label="Website"
              >
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
                    size={11}
                  />
                </a>
              </InfoRow>

              <InfoRow
                label="Blog Page URL"
              >
                {
                  detected
                  ? (
                    <a
                      href={
                        data.blog_url
                      }
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-700"
                    >
                      {
                        data.blog_url
                      }

                      <ExternalLink
                        size={11}
                      />
                    </a>
                  )
                  : (
                    <span className="font-medium text-slate-500">
                      Not detected
                    </span>
                  )
                }
              </InfoRow>

              <InfoRow
                label="Detection Method"
              >
                {
                  data.detection_source
                  ||
                  "—"
                }
              </InfoRow>

              <InfoRow
                label="Blog HTTP Status"
              >
                {
                  data.http_status
                  ??
                  "—"
                }
              </InfoRow>

              <InfoRow
                label="Blog Page Title"
              >
                {
                  data.page_title
                  ||
                  "—"
                }
              </InfoRow>

              <InfoRow
                label="Blog H1"
              >
                {
                  data.h1
                  ||
                  "Not detected"
                }
              </InfoRow>

              <InfoRow
                label="Posts Detected"
              >
                {
                  posts.length
                }
              </InfoRow>
            </tbody>
          </table>
        </div>
      </div>


      {
        posts.length > 0
        &&
        (
          <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
              <h3 className="text-sm font-semibold text-slate-950">
                Detected Blog Posts
              </h3>

              <p className="mt-1 text-[11px] text-slate-500">
                Post links and featured-image information found on the blog archive.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[1000px] border-collapse text-left">
                <thead>
                  <tr className="bg-slate-950 text-white">
                    <th className="w-[55px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      #
                    </th>

                    <th className="w-[280px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Post Title
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Post URL
                    </th>

                    <th className="w-[105px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Image
                    </th>

                    <th className="w-[105px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Image ALT
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {
                    posts.map(
                      (
                        post,
                        index
                      ) => (
                        <tr
                          key={
                            `${post.url}-${index}`
                          }
                          className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                        >
                          <td className="px-4 py-3 align-top text-xs font-semibold text-slate-400">
                            {
                              index + 1
                            }
                          </td>

                          <td className="px-4 py-3 align-top text-xs font-semibold leading-5 text-slate-800">
                            {
                              post.title
                              ||
                              "—"
                            }
                          </td>

                          <td className="px-4 py-3 align-top">
                            <a
                              href={
                                post.url
                              }
                              target="_blank"
                              rel="noreferrer"
                              className="break-all text-xs font-medium leading-5 text-blue-600 hover:text-blue-700"
                            >
                              {
                                post.url
                              }
                            </a>
                          </td>

                          <td className="px-4 py-3 align-top">
                            <StatusBadge
                              status={
                                post.image_url
                                  ? "pass"
                                  : "warning"
                              }
                              compact
                            />
                          </td>

                          <td className="px-4 py-3 align-top">
                            {
                              post.image_type ===
                              "IMG"
                                ? (
                                    <StatusBadge
                                      status={
                                        (
                                          post.image_alt
                                          ||
                                          ""
                                        ).trim()
                                          ? "pass"
                                          : "warning"
                                      }
                                      compact
                                    />
                                  )
                                : (
                                    <span className="text-[10px] font-semibold text-slate-400">
                                      N/A
                                    </span>
                                  )
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
        )
      }


      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-50 px-5 py-4">
          <FileText
            size={16}
            className="text-blue-600"
          />

          <h3 className="text-sm font-semibold text-slate-950">
            Blog QA Findings
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] border-collapse text-left">
            <thead>
              <tr className="bg-slate-950 text-white">
                <th className="w-[105px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                  Status
                </th>

                <th className="w-[240px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                  Check
                </th>

                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                  Result
                </th>
              </tr>
            </thead>

            <tbody>
              {
                (
                  result.findings
                  ||
                  []
                ).map(
                  (
                    finding,
                    index
                  ) => (
                    <tr
                      key={
                        `${finding.title}-${index}`
                      }
                      className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                    >
                      <td className="px-4 py-3 align-top">
                        <StatusBadge
                          status={
                            finding.status
                          }
                          compact
                        />
                      </td>

                      <td className="px-4 py-3 align-top text-xs font-semibold text-slate-800">
                        {
                          finding.title
                        }
                      </td>

                      <td className="px-4 py-3 align-top text-xs leading-5 text-slate-600">
                        {
                          finding.message
                          ||
                          "—"
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
    </section>
  );
}
