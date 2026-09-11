import {
  ExternalLink,
  Files,
} from "lucide-react";


export default function WebsitePageList({
  pages = [],
}) {
  if (!pages.length) {
    return null;
  }

  return (
    <section className="mt-4 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
      <div className="flex flex-col gap-2 border-b border-slate-200 bg-slate-50 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
            <Files size={18} />
          </span>

          <div>
            <h2 className="font-display text-base font-bold text-slate-950">
              Website Page List
            </h2>

            <p className="mt-0.5 text-[11px] text-slate-500">
              HTML pages discovered on this website. CSS, JavaScript and other asset files are excluded.
            </p>
          </div>
        </div>

        <span className="w-fit rounded-full bg-blue-50 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-blue-700">
          {pages.length} page{pages.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-950 text-white">
              <th className="w-[90px] px-4 py-3 text-center text-[10px] font-bold uppercase tracking-[0.14em]">
                Page No.
              </th>

              <th className="w-[280px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                Page Title
              </th>

              <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.14em]">
                URL
              </th>
            </tr>
          </thead>

          <tbody>
            {pages.map(
              (page, index) => (
                <tr
                  key={`${page.url}-${index}`}
                  className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                >
                  <td className="px-4 py-3 text-center text-xs font-bold text-slate-500">
                    {page.page_no ?? index + 1}
                  </td>

                  <td className="px-4 py-3 text-xs font-semibold text-slate-800">
                    {page.title || "Untitled page"}
                  </td>

                  <td className="px-4 py-3">
                    <a
                      href={page.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-start gap-1.5 break-all text-xs font-medium leading-5 text-blue-600 hover:text-blue-800"
                    >
                      <span>{page.url}</span>
                      <ExternalLink
                        size={12}
                        className="mt-1 shrink-0"
                      />
                    </a>
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
