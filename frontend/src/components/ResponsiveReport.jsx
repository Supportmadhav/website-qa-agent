import {
  Download,
  ExternalLink,
  Laptop,
  LoaderCircle,
  Monitor,
  RefreshCw,
  Smartphone,
  Tablet,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import StatusBadge from "./StatusBadge";

import {
  downloadPdfReport,
} from "../utils/report";


const DEVICE_OPTIONS = [
  {
    id: "desktop",
    label: "Desktop",
    rangeLabel:
      "1920px to 1440px",
    minWidth: 1440,
    maxWidth: 1920,
    icon: Monitor,
    presets: [
      {
        label:
          "1920 × 1080",
        width: 1920,
        height: 1080,
      },
      {
        label:
          "1680 × 1050",
        width: 1680,
        height: 1050,
      },
      {
        label:
          "1600 × 900",
        width: 1600,
        height: 900,
      },
      {
        label:
          "1440 × 900",
        width: 1440,
        height: 900,
      },
    ],
  },
  {
    id: "laptop",
    label: "Laptop",
    rangeLabel:
      "1439px to 1024px",
    minWidth: 1024,
    maxWidth: 1439,
    icon: Laptop,
    presets: [
      {
        label:
          "1366 × 768",
        width: 1366,
        height: 768,
      },
      {
        label:
          "1280 × 800",
        width: 1280,
        height: 800,
      },
      {
        label:
          "1280 × 720",
        width: 1280,
        height: 720,
      },
      {
        label:
          "1024 × 768",
        width: 1024,
        height: 768,
      },
    ],
  },
  {
    id: "tablet",
    label: "Tablet",
    rangeLabel:
      "1023px to 768px",
    minWidth: 768,
    maxWidth: 1023,
    icon: Tablet,
    presets: [
      {
        label:
          "912 × 1368",
        width: 912,
        height: 1368,
      },
      {
        label:
          "834 × 1194",
        width: 834,
        height: 1194,
      },
      {
        label:
          "820 × 1180",
        width: 820,
        height: 1180,
      },
      {
        label:
          "768 × 1024",
        width: 768,
        height: 1024,
      },
    ],
  },
  {
    id: "mobile",
    label: "Mobile",
    rangeLabel:
      "767px to 324px",
    minWidth: 324,
    maxWidth: 767,
    icon: Smartphone,
    presets: [
      {
        label:
          "430 × 932",
        width: 430,
        height: 932,
      },
      {
        label:
          "412 × 915",
        width: 412,
        height: 915,
      },
      {
        label:
          "390 × 844",
        width: 390,
        height: 844,
      },
      {
        label:
          "375 × 812",
        width: 375,
        height: 812,
      },
      {
        label:
          "360 × 800",
        width: 360,
        height: 800,
      },
      {
        label:
          "324 × 700",
        width: 324,
        height: 700,
      },
    ],
  },
];


function DeviceCard({
  device,
  selected,
  onClick,
}) {
  const Icon =
    device.icon;

  return (
    <button
      type="button"
      onClick={
        onClick
      }
      className={[
        "rounded-2xl border p-4 text-left transition",
        selected
          ? "border-blue-500 bg-blue-50 ring-4 ring-blue-50"
          : "border-slate-200 bg-white hover:border-blue-300 hover:bg-slate-50",
      ].join(" ")}
    >
      <div className="flex items-center gap-3">
        <span
          className={[
            "flex h-9 w-9 items-center justify-center rounded-xl",
            selected
              ? "bg-blue-600 text-white"
              : "bg-slate-100 text-slate-600",
          ].join(" ")}
        >
          <Icon
            size={17}
          />
        </span>

        <div>
          <p className="text-sm font-semibold text-slate-950">
            {
              device.label
            }
          </p>

          <p className="mt-0.5 text-[10px] font-medium text-slate-500">
            {
              device.rangeLabel
            }
          </p>
        </div>
      </div>
    </button>
  );
}


export default function ResponsiveReport({
  report,
  result,
}) {
  const auditData =
    result.responsive_data
    ||
    {};

  const auditViewports =
    auditData.audit_viewports
    ||
    [];

  const [
    selectedDeviceId,
    setSelectedDeviceId,
  ] = useState(
    "desktop"
  );

  const selectedDevice =
    useMemo(
      () =>
        DEVICE_OPTIONS.find(
          (device) =>
            device.id ===
            selectedDeviceId
        )
        ||
        DEVICE_OPTIONS[
          0
        ],
      [
        selectedDeviceId,
      ]
    );

  const [
    width,
    setWidth,
  ] = useState(
    1920
  );

  const [
    height,
    setHeight,
  ] = useState(
    1080
  );

  const [
    preview,
    setPreview,
  ] = useState(
    null
  );

  const [
    loading,
    setLoading,
  ] = useState(
    false
  );

  const [
    error,
    setError,
  ] = useState(
    ""
  );


  function selectDevice(
    device
  ) {
    setSelectedDeviceId(
      device.id
    );

    const preset =
      device.presets[
        0
      ];

    setWidth(
      preset.width
    );

    setHeight(
      preset.height
    );

    setPreview(
      null
    );

    setError(
      ""
    );
  }


  function selectPreset(
    value
  ) {
    const preset =
      selectedDevice.presets.find(
        (item) =>
          (
            `${item.width}x${item.height}`
            ===
            value
          )
      );

    if (!preset) {
      return;
    }

    setWidth(
      preset.width
    );

    setHeight(
      preset.height
    );

    setPreview(
      null
    );

    setError(
      ""
    );
  }


  const widthValid =
    (
      width >=
      selectedDevice.minWidth
      &&
      width <=
      selectedDevice.maxWidth
    );

  const heightValid =
    (
      height >= 480
      &&
      height <= 2160
    );


  async function generatePreview() {
    if (
      !widthValid
      ||
      !heightValid
      ||
      loading
    ) {
      return;
    }

    setLoading(
      true
    );

    setError(
      ""
    );

    try {
      const response =
        await fetch(
          "http://127.0.0.1:8000/api/responsive-preview",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                url:
                  report.page?.final_url
                  ||
                  report.page?.requested_url,

                width:
                  Number(
                    width
                  ),

                height:
                  Number(
                    height
                  ),
              }),
          }
        );

      const body =
        await response.json();

      if (!response.ok) {
        throw new Error(
          body.detail
          ||
          "Responsive preview failed."
        );
      }

      setPreview(
        body
      );

    } catch (
      caughtError
    ) {
      setError(
        caughtError.message
        ||
        "Responsive preview failed."
      );

    } finally {
      setLoading(
        false
      );
    }
  }


  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
              Responsive Report
            </p>

            <h2 className="mt-1 text-lg font-semibold text-slate-950">
              Responsive - {
                report.page?.title
                ||
                "Website"
              }
            </h2>

            <a
              href={
                report.page?.final_url
              }
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1 break-all text-xs font-medium text-blue-600 hover:text-blue-700"
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


      {
        auditViewports.length > 0
        &&
        (
          <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
              <h3 className="text-sm font-semibold text-slate-950">
                Responsive Audit
              </h3>

              <p className="mt-1 text-[11px] text-slate-500">
                Representative viewport tested automatically for each screen range.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] border-collapse text-left">
                <thead>
                  <tr className="bg-slate-950 text-white">
                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Screen
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Range
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Tested Resolution
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Overflow
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Outside Elements
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Overlaps
                    </th>

                    <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                      Status
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {
                    auditViewports.map(
                      (item) => (
                        <tr
                          key={
                            item.id
                          }
                          className="border-b border-slate-100 last:border-b-0"
                        >
                          <td className="px-4 py-3 text-xs font-semibold text-slate-800">
                            {
                              item.label
                            }
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {
                              item.range
                            }
                          </td>

                          <td className="px-4 py-3 text-xs font-medium text-slate-700">
                            {
                              item.width
                            }
                            ×
                            {
                              item.height
                            }
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {
                              item.horizontal_overflow
                                ? "Yes"
                                : "No"
                            }
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {
                              item.outside_count
                            }
                          </td>

                          <td className="px-4 py-3 text-xs text-slate-600">
                            {
                              item.overlap_count
                            }
                          </td>

                          <td className="px-4 py-3">
                            <StatusBadge
                              status={
                                item.status
                              }
                              compact
                            />
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


      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">
            Virtual Responsive Environment
          </h3>

          <p className="mt-1 text-[11px] leading-5 text-slate-500">
            Choose a screen category, select a normal resolution or enter a custom resolution within that category, then generate the page preview.
          </p>
        </div>


        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {
            DEVICE_OPTIONS.map(
              (device) => (
                <DeviceCard
                  key={
                    device.id
                  }
                  device={
                    device
                  }
                  selected={
                    selectedDeviceId ===
                    device.id
                  }
                  onClick={() =>
                    selectDevice(
                      device
                    )
                  }
                />
              )
            )
          }
        </div>


        <div className="mt-5 grid gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 lg:grid-cols-[1.3fr_0.7fr_0.7fr_auto] lg:items-end">
          <label className="block">
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
              Normal Resolution
            </span>

            <select
              value={
                `${width}x${height}`
              }
              onChange={
                (
                  event
                ) =>
                  selectPreset(
                    event.target.value
                  )
              }
              className="mt-2 min-h-[44px] w-full rounded-xl border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            >
              {
                selectedDevice.presets.map(
                  (preset) => (
                    <option
                      key={
                        `${preset.width}x${preset.height}`
                      }
                      value={
                        `${preset.width}x${preset.height}`
                      }
                    >
                      {
                        preset.label
                      }
                    </option>
                  )
                )
              }
            </select>
          </label>


          <label className="block">
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
              Width
            </span>

            <input
              type="number"
              min={
                selectedDevice.minWidth
              }
              max={
                selectedDevice.maxWidth
              }
              value={
                width
              }
              onChange={
                (
                  event
                ) =>
                  setWidth(
                    Number(
                      event.target.value
                    )
                  )
              }
              className={[
                "mt-2 min-h-[44px] w-full rounded-xl border bg-white px-3 text-xs font-medium outline-none focus:ring-4",
                widthValid
                  ? "border-slate-200 text-slate-700 focus:border-blue-500 focus:ring-blue-100"
                  : "border-rose-300 text-rose-700 focus:border-rose-500 focus:ring-rose-100",
              ].join(" ")}
            />

            <span className="mt-1 block text-[10px] text-slate-400">
              {
                selectedDevice.minWidth
              }
              –
              {
                selectedDevice.maxWidth
              }
              px
            </span>
          </label>


          <label className="block">
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
              Height
            </span>

            <input
              type="number"
              min="480"
              max="2160"
              value={
                height
              }
              onChange={
                (
                  event
                ) =>
                  setHeight(
                    Number(
                      event.target.value
                    )
                  )
              }
              className={[
                "mt-2 min-h-[44px] w-full rounded-xl border bg-white px-3 text-xs font-medium outline-none focus:ring-4",
                heightValid
                  ? "border-slate-200 text-slate-700 focus:border-blue-500 focus:ring-blue-100"
                  : "border-rose-300 text-rose-700 focus:border-rose-500 focus:ring-rose-100",
              ].join(" ")}
            />
          </label>


          <button
            type="button"
            disabled={
              loading
              ||
              !widthValid
              ||
              !heightValid
            }
            onClick={
              generatePreview
            }
            className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {
              loading
                ? (
                    <LoaderCircle
                      size={15}
                      className="animate-spin"
                    />
                  )
                : (
                    <RefreshCw
                      size={15}
                    />
                  )
            }

            {
              loading
                ? "Generating..."
                : "Generate Preview"
            }
          </button>
        </div>


        {
          error
          &&
          (
            <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-medium text-rose-700">
              {error}
            </div>
          )
        }


        {
          preview
          &&
          (
            <div className="mt-5 overflow-hidden rounded-3xl border border-slate-300 bg-slate-900 shadow-xl">
              <div className="flex flex-col gap-2 border-b border-slate-700 bg-slate-950 px-4 py-3 text-white sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-semibold">
                    {
                      selectedDevice.label
                    }
                    {" "}
                    Virtual Preview
                  </p>

                  <p className="mt-0.5 text-[10px] text-slate-400">
                    Rendered at {
                      preview.viewport?.width
                    }
                    ×
                    {
                      preview.viewport?.height
                    }
                    px
                    {" "}
                    · full page {
                      preview.document_width
                    }
                    ×
                    {
                      preview.document_height
                    }
                    px
                  </p>
                </div>

                <div className="flex items-center gap-3 text-[10px] text-slate-400">
                  <span>
                    HTTP {
                      preview.http_status
                      ??
                      "—"
                    }
                  </span>

                  <span>
                    {
                      preview.generation_seconds
                    }
                    s
                  </span>

                  <a
                    href={
                      preview.final_url
                    }
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-semibold text-blue-300 hover:text-blue-200"
                  >
                    Open live page

                    <ExternalLink
                      size={11}
                    />
                  </a>
                </div>
              </div>


              <div className="bg-[linear-gradient(45deg,#eef2f7_25%,transparent_25%),linear-gradient(-45deg,#eef2f7_25%,transparent_25%),linear-gradient(45deg,transparent_75%,#eef2f7_75%),linear-gradient(-45deg,transparent_75%,#eef2f7_75%)] bg-[length:18px_18px] bg-[position:0_0,0_9px,9px_-9px,-9px_0px] p-4">
                <div className="mx-auto max-h-[720px] overflow-auto rounded-xl border border-slate-300 bg-white shadow-2xl">
                  <img
                    src={
                      `data:${preview.image_mime};base64,${preview.image_base64}`
                    }
                    alt={
                      `${selectedDevice.label} responsive preview`
                    }
                    className="block h-auto max-w-none"
                    style={{
                      width:
                        `${preview.viewport?.width}px`,
                    }}
                  />
                </div>
              </div>
            </div>
          )
        }
      </section>


      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
          <h3 className="text-sm font-semibold text-slate-950">
            Responsive QA Findings
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-left">
            <thead>
              <tr className="bg-slate-950 text-white">
                <th className="w-[110px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
                  Status
                </th>

                <th className="w-[260px] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.13em]">
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
                      className="border-b border-slate-100 last:border-b-0"
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
