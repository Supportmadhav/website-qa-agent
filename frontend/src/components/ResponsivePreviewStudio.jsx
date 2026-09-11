import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  Download,
  ExternalLink,
  Globe2,
  ImageDown,
  Laptop,
  LoaderCircle,
  Monitor,
  RefreshCw,
  Smartphone,
  Tablet,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";


const API_BASE =
  "http://127.0.0.1:8000";


const DEVICE_GROUPS = [
  {
    id: "desktop",
    label: "Desktop",
    range: "1920px to 1440px",
    minWidth: 1440,
    maxWidth: 1920,
    icon: Monitor,
    accent: "from-blue-600 to-indigo-600",
    presets: [
      { label: "1920 × 1080", width: 1920, height: 1080 },
      { label: "1680 × 1050", width: 1680, height: 1050 },
      { label: "1600 × 900", width: 1600, height: 900 },
      { label: "1440 × 900", width: 1440, height: 900 },
    ],
  },
  {
    id: "laptop",
    label: "Laptop",
    range: "1439px to 1024px",
    minWidth: 1024,
    maxWidth: 1439,
    icon: Laptop,
    accent: "from-violet-600 to-purple-600",
    presets: [
      { label: "1366 × 768", width: 1366, height: 768 },
      { label: "1280 × 800", width: 1280, height: 800 },
      { label: "1280 × 720", width: 1280, height: 720 },
      { label: "1024 × 768", width: 1024, height: 768 },
    ],
  },
  {
    id: "tablet",
    label: "Tablet",
    range: "1023px to 768px",
    minWidth: 768,
    maxWidth: 1023,
    icon: Tablet,
    accent: "from-cyan-600 to-blue-600",
    presets: [
      { label: "912 × 1368", width: 912, height: 1368 },
      { label: "834 × 1194", width: 834, height: 1194 },
      { label: "820 × 1180", width: 820, height: 1180 },
      { label: "768 × 1024", width: 768, height: 1024 },
    ],
  },
  {
    id: "mobile",
    label: "Mobile",
    range: "767px to 324px",
    minWidth: 324,
    maxWidth: 767,
    icon: Smartphone,
    accent: "from-emerald-600 to-teal-600",
    presets: [
      { label: "430 × 932", width: 430, height: 932 },
      { label: "412 × 915", width: 412, height: 915 },
      { label: "390 × 844", width: 390, height: 844 },
      { label: "375 × 812", width: 375, height: 812 },
      { label: "360 × 800", width: 360, height: 800 },
      { label: "324 × 700", width: 324, height: 700 },
    ],
  },
];


const SPECIAL_KEYS = new Set([
  "Enter",
  "Tab",
  "Backspace",
  "Delete",
  "Escape",
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "Home",
  "End",
  "PageUp",
  "PageDown",
]);


function DeviceSelector({
  device,
  active,
  onSelect,
}) {
  const Icon =
    device.icon;

  return (
    <button
      type="button"
      onClick={
        onSelect
      }
      className={[
        "group relative overflow-hidden rounded-2xl border p-4 text-left transition-all",
        active
          ? "border-blue-500 bg-white shadow-[0_14px_38px_rgba(37,99,235,0.12)] ring-4 ring-blue-50"
          : "border-slate-200 bg-white hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg",
      ].join(" ")}
    >
      <div
        className={[
          "absolute inset-x-0 top-0 h-1 bg-gradient-to-r transition-opacity",
          device.accent,
          active
            ? "opacity-100"
            : "opacity-0 group-hover:opacity-60",
        ].join(" ")}
      />

      <div className="flex items-center gap-3">
        <span
          className={[
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition",
            active
              ? `bg-gradient-to-br ${device.accent} text-white shadow-lg`
              : "bg-slate-100 text-slate-600 group-hover:bg-slate-200",
          ].join(" ")}
        >
          <Icon
            size={18}
          />
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-bold text-slate-950">
              {
                device.label
              }
            </p>

            {
              active
              &&
              (
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-white">
                  <Check
                    size={12}
                  />
                </span>
              )
            }
          </div>

          <p className="mt-1 text-[11px] font-medium text-slate-500">
            {
              device.range
            }
          </p>
        </div>
      </div>
    </button>
  );
}


function downloadBase64(
  body
) {
  if (
    !body?.image_base64
  ) {
    return;
  }

  const anchor =
    document.createElement(
      "a"
    );

  anchor.href =
    `data:${body.image_mime};base64,${body.image_base64}`;

  anchor.download =
    body.filename
    ||
    "responsive-screenshot.png";

  document.body.appendChild(
    anchor
  );

  anchor.click();
  anchor.remove();
}


export default function ResponsivePreviewStudio() {
  const [
    url,
    setUrl,
  ] = useState("");

  const [
    browserUrl,
    setBrowserUrl,
  ] = useState("");

  const [
    deviceId,
    setDeviceId,
  ] = useState(
    "desktop"
  );

  const device =
    useMemo(
      () =>
        DEVICE_GROUPS.find(
          (item) =>
            item.id ===
            deviceId
        )
        ||
        DEVICE_GROUPS[
          0
        ],
      [
        deviceId,
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
    presetKey,
    setPresetKey,
  ] = useState(
    "1920x1080"
  );

  const [
    sessionId,
    setSessionId,
  ] = useState(
    ""
  );

  const [
    frame,
    setFrame,
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
    interacting,
    setInteracting,
  ] = useState(
    false
  );

  const [
    error,
    setError,
  ] = useState(
    ""
  );

  const [
    downloading,
    setDownloading,
  ] = useState(
    ""
  );

  const screenRef =
    useRef(
      null
    );

  const actionBusyRef =
    useRef(
      false
    );

  const textBufferRef =
    useRef(
      ""
    );

  const textTimerRef =
    useRef(
      null
    );

  const wheelDeltaRef =
    useRef(
      0
    );

  const wheelTimerRef =
    useRef(
      null
    );


  const widthValid =
    (
      Number.isFinite(
        width
      )
      &&
      width >=
        device.minWidth
      &&
      width <=
        device.maxWidth
    );

  const heightValid =
    (
      Number.isFinite(
        height
      )
      &&
      height >= 480
      &&
      height <= 2160
    );

  const canStart =
    (
      url.trim()
      &&
      widthValid
      &&
      heightValid
      &&
      !loading
    );


  async function closeSession(
    id
  ) {
    if (!id) {
      return;
    }

    try {
      await fetch(
        `${API_BASE}/api/responsive-browser/session/${id}`,
        {
          method:
            "DELETE",
        }
      );

    } catch (
      caughtError
    ) {
      // Session cleanup is best-effort.
    }
  }


  useEffect(
    () => {
      return () => {
        if (
          sessionId
        ) {
          closeSession(
            sessionId
          );
        }

        if (
          textTimerRef.current
        ) {
          clearTimeout(
            textTimerRef.current
          );
        }

        if (
          wheelTimerRef.current
        ) {
          clearTimeout(
            wheelTimerRef.current
          );
        }
      };
    },
    [
      sessionId,
    ]
  );


  useEffect(
    () => {
      if (
        !sessionId
      ) {
        return undefined;
      }

      const interval =
        window.setInterval(
          async () => {
            if (
              actionBusyRef.current
            ) {
              return;
            }

            try {
              const response =
                await fetch(
                  `${API_BASE}/api/responsive-browser/frame/${sessionId}`
                );

              if (!response.ok) {
                return;
              }

              const body =
                await response.json();

              setFrame(
                body
              );

              setBrowserUrl(
                body.url
                ||
                ""
              );

            } catch (
              caughtError
            ) {
              // Periodic live refresh should not interrupt the user.
            }
          },
          900
        );

      return () =>
        window.clearInterval(
          interval
        );
    },
    [
      sessionId,
    ]
  );


  function selectDevice(
    nextDevice
  ) {
    const first =
      nextDevice.presets[
        0
      ];

    setDeviceId(
      nextDevice.id
    );

    setWidth(
      first.width
    );

    setHeight(
      first.height
    );

    setPresetKey(
      `${first.width}x${first.height}`
    );

    setError(
      ""
    );
  }


  function selectPreset(
    value
  ) {
    setPresetKey(
      value
    );

    const preset =
      device.presets.find(
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
  }


  function changeWidth(
    value
  ) {
    setWidth(
      Number(
        value
      )
    );

    setPresetKey(
      "custom"
    );
  }


  function changeHeight(
    value
  ) {
    setHeight(
      Number(
        value
      )
    );

    setPresetKey(
      "custom"
    );
  }


  async function startLiveBrowser(
    event
  ) {
    if (event) {
      event.preventDefault();
    }

    if (!canStart) {
      return;
    }

    setLoading(
      true
    );

    setError(
      ""
    );

    const oldSession =
      sessionId;

    try {
      if (
        oldSession
      ) {
        await closeSession(
          oldSession
        );
      }

      const response =
        await fetch(
          `${API_BASE}/api/responsive-browser/session`,
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
                  url.trim(),

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
          "Could not start the live responsive browser."
        );
      }

      setSessionId(
        body.session_id
      );

      setFrame(
        body
      );

      setBrowserUrl(
        body.url
        ||
        url.trim()
      );

      window.setTimeout(
        () =>
          screenRef.current?.focus(),
        100
      );

    } catch (
      caughtError
    ) {
      setSessionId(
        ""
      );

      setFrame(
        null
      );

      setError(
        caughtError.message
        ||
        "Could not start the live responsive browser."
      );

    } finally {
      setLoading(
        false
      );
    }
  }


  async function sendAction(
    action,
    data = {},
    {
      quiet = false,
    } = {}
  ) {
    if (
      !sessionId
      ||
      actionBusyRef.current
    ) {
      return null;
    }

    actionBusyRef.current =
      true;

    if (!quiet) {
      setInteracting(
        true
      );
    }

    try {
      const response =
        await fetch(
          `${API_BASE}/api/responsive-browser/action`,
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                session_id:
                  sessionId,

                action,
                ...data,
              }),
          }
        );

      const body =
        await response.json();

      if (!response.ok) {
        throw new Error(
          body.detail
          ||
          "Live browser interaction failed."
        );
      }

      setFrame(
        body
      );

      setBrowserUrl(
        body.url
        ||
        browserUrl
      );

      return body;

    } catch (
      caughtError
    ) {
      if (!quiet) {
        setError(
          caughtError.message
          ||
          "Live browser interaction failed."
        );
      }

      return null;

    } finally {
      actionBusyRef.current =
        false;

      if (!quiet) {
        setInteracting(
          false
        );
      }
    }
  }


  async function navigateBrowser(
    event
  ) {
    if (event) {
      event.preventDefault();
    }

    if (
      !browserUrl.trim()
    ) {
      return;
    }

    await sendAction(
      "navigate",
      {
        url:
          browserUrl.trim(),
      }
    );

    screenRef.current?.focus();
  }


  async function handleScreenClick(
    event
  ) {
    if (
      !frame
      ||
      !sessionId
    ) {
      return;
    }

    const rect =
      event.currentTarget
      .getBoundingClientRect();

    const x =
      (
        event.clientX
        -
        rect.left
      )
      *
      (
        frame.viewport.width
        /
        rect.width
      );

    const y =
      (
        event.clientY
        -
        rect.top
      )
      *
      (
        frame.viewport.height
        /
        rect.height
      );

    screenRef.current?.focus();

    await sendAction(
      "click",
      {
        x,
        y,
      }
    );
  }


  function flushTextBuffer() {
    if (
      !textBufferRef.current
    ) {
      return;
    }

    const text =
      textBufferRef.current;

    textBufferRef.current =
      "";

    sendAction(
      "text",
      {
        text,
      },
      {
        quiet:
          true,
      }
    );
  }


  function handleScreenKeyDown(
    event
  ) {
    if (
      !sessionId
      ||
      event.ctrlKey
      ||
      event.metaKey
      ||
      event.altKey
    ) {
      return;
    }

    if (
      SPECIAL_KEYS.has(
        event.key
      )
    ) {
      event.preventDefault();

      flushTextBuffer();

      sendAction(
        "key",
        {
          key:
            event.key,
        },
        {
          quiet:
            true,
        }
      );

      return;
    }

    if (
      event.key.length ===
      1
    ) {
      event.preventDefault();

      textBufferRef.current +=
        event.key;

      if (
        textTimerRef.current
      ) {
        clearTimeout(
          textTimerRef.current
        );
      }

      textTimerRef.current =
        window.setTimeout(
          flushTextBuffer,
          90
        );
    }
  }


  function handleScreenWheel(
    event
  ) {
    if (
      !sessionId
    ) {
      return;
    }

    // Keep wheel movement inside the virtual browser.
    // Do not allow the Website QA Agent page itself to scroll
    // while the pointer is over the virtual screen.
    event.preventDefault();
    event.stopPropagation();

    if (
      event.nativeEvent
      &&
      typeof event.nativeEvent.stopImmediatePropagation ===
        "function"
    ) {
      event.nativeEvent.stopImmediatePropagation();
    }

    wheelDeltaRef.current +=
      event.deltaY;

    if (
      wheelTimerRef.current
    ) {
      clearTimeout(
        wheelTimerRef.current
      );
    }

    wheelTimerRef.current =
      window.setTimeout(
        () => {
          const delta =
            wheelDeltaRef.current;

          wheelDeltaRef.current =
            0;

          sendAction(
            "scroll",
            {
              delta_y:
                delta,
            },
            {
              quiet:
                true,
            }
          );
        },
        55
      );
  }


  function scrollVirtualBrowserTo(
    targetY
  ) {
    if (
      !frame
      ||
      !sessionId
    ) {
      return;
    }

    const currentY =
      Number(
        frame.scroll_y
        ||
        0
      );

    const maxScroll =
      Math.max(
        0,
        Number(
          frame.document_height
          ||
          frame.viewport.height
        )
        -
        Number(
          frame.viewport.height
          ||
          0
        )
      );

    const clampedTarget =
      Math.max(
        0,
        Math.min(
          maxScroll,
          targetY
        )
      );

    const delta =
      clampedTarget
      -
      currentY;

    if (
      Math.abs(
        delta
      )
      <
      1
    ) {
      return;
    }

    sendAction(
      "scroll",
      {
        delta_y:
          delta,
      },
      {
        quiet:
          true,
      }
    );
  }


  function handleVirtualScrollbarClick(
    event
  ) {
    if (
      !frame
      ||
      !sessionId
    ) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    const track =
      event.currentTarget
      .getBoundingClientRect();

    const clickRatio =
      Math.max(
        0,
        Math.min(
          1,
          (
            event.clientY
            -
            track.top
          )
          /
          track.height
        )
      );

    const maxScroll =
      Math.max(
        0,
        Number(
          frame.document_height
          ||
          frame.viewport.height
        )
        -
        Number(
          frame.viewport.height
          ||
          0
        )
      );

    scrollVirtualBrowserTo(
      maxScroll
      *
      clickRatio
    );
  }


  async function downloadScreenshot(
    fullPage
  ) {
    if (
      !sessionId
    ) {
      return;
    }

    setDownloading(
      fullPage
        ? "full"
        : "viewport"
    );

    setError(
      ""
    );

    try {
      const response =
        await fetch(
          `${API_BASE}/api/responsive-browser/screenshot`,
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                session_id:
                  sessionId,

                full_page:
                  fullPage,
              }),
          }
        );

      const body =
        await response.json();

      if (!response.ok) {
        throw new Error(
          body.detail
          ||
          "Could not generate the screenshot."
        );
      }

      downloadBase64(
        body
      );

    } catch (
      caughtError
    ) {
      setError(
        caughtError.message
        ||
        "Could not generate the screenshot."
      );

    } finally {
      setDownloading(
        ""
      );
    }
  }


  const displayWidth =
    frame
      ? Math.min(
          frame.viewport.width,
          1180
        )
      : 1080;

  const displayScale =
    frame
      ? (
          displayWidth
          /
          frame.viewport.width
        )
      : 1;

  const displayHeight =
    frame
      ? Math.min(
          720,
          Math.max(
            420,
            Math.round(
              frame.viewport.height
              *
              displayScale
            )
          )
        )
      : 620;


  const virtualMaxScroll =
    frame
      ? Math.max(
          0,
          Number(
            frame.document_height
            ||
            frame.viewport.height
          )
          -
          Number(
            frame.viewport.height
            ||
            0
          )
        )
      : 0;


  const virtualThumbHeightPercent =
    frame
      ? Math.max(
          8,
          Math.min(
            100,
            (
              Number(
                frame.viewport.height
                ||
                1
              )
              /
              Math.max(
                Number(
                  frame.document_height
                  ||
                  frame.viewport.height
                  ||
                  1
                ),
                1
              )
            )
            *
            100
          )
        )
      : 100;


  const virtualThumbTopPercent =
    (
      frame
      &&
      virtualMaxScroll > 0
    )
      ? (
          (
            Number(
              frame.scroll_y
              ||
              0
            )
            /
            virtualMaxScroll
          )
          *
          (
            100
            -
            virtualThumbHeightPercent
          )
        )
      : 0;


  return (
    <div className="mx-auto max-w-[1500px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <section className="relative overflow-hidden rounded-[30px] border border-slate-800 bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.28),transparent_35%),linear-gradient(135deg,#020617_0%,#0f172a_48%,#172554_100%)] p-6 text-white shadow-[0_28px_80px_rgba(15,23,42,0.22)] sm:p-8">
        <div className="relative z-10 grid gap-7 xl:grid-cols-[1fr_1.08fr] xl:items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-200">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
              Live Responsive Browser
            </span>

            <h1 className="mt-5 max-w-2xl font-display text-3xl font-bold tracking-[-0.035em] text-white sm:text-4xl">
              Use a real browser inside the responsive virtual screen
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              The virtual screen now runs a real Chromium page session. Click links, scroll, type into fields, use menus, navigate pages, go back/forward, reload, and review dynamic content at the exact selected resolution.
            </p>
          </div>


          <form
            onSubmit={
              startLiveBrowser
            }
            className="rounded-2xl border border-white/10 bg-white/10 p-3 shadow-2xl backdrop-blur-xl"
          >
            <label className="text-[10px] font-bold uppercase tracking-[0.13em] text-blue-100/70">
              Website URL
            </label>

            <div className="mt-2 flex flex-col gap-3 sm:flex-row">
              <div className="relative min-w-0 flex-1">
                <Globe2
                  size={16}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  value={
                    url
                  }
                  onChange={
                    (
                      event
                    ) =>
                      setUrl(
                        event.target.value
                      )
                  }
                  disabled={
                    loading
                  }
                  placeholder="https://example.com"
                  className="h-12 w-full rounded-xl border border-white/10 bg-white pl-11 pr-4 text-sm font-medium text-slate-950 outline-none transition placeholder:text-slate-400 focus:ring-4 focus:ring-blue-300/20 disabled:opacity-60"
                />
              </div>

              <button
                type="submit"
                disabled={
                  !canStart
                }
                className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-bold text-white shadow-[0_12px_28px_rgba(37,99,235,0.35)] transition hover:-translate-y-0.5 hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0"
              >
                {
                  loading
                    ? (
                        <LoaderCircle
                          size={16}
                          className="animate-spin"
                        />
                      )
                    : (
                        <Monitor
                          size={16}
                        />
                      )
                }

                {
                  loading
                    ? "Starting..."
                    : sessionId
                      ? "Restart Live Browser"
                      : "Start Live Browser"
                }
              </button>
            </div>
          </form>
        </div>
      </section>


      <section className="mt-6 rounded-[26px] border border-slate-200 bg-white p-5 shadow-[0_14px_48px_rgba(15,23,42,0.06)] sm:p-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-blue-600">
              Screen Setup
            </p>

            <h2 className="mt-1 text-lg font-bold tracking-tight text-slate-950">
              Choose device range and exact resolution
            </h2>
          </div>

          <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-500">
            {
              device.label
            }
            {" · "}
            {
              device.range
            }
          </div>
        </div>


        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {
            DEVICE_GROUPS.map(
              (
                item
              ) => (
                <DeviceSelector
                  key={
                    item.id
                  }
                  device={
                    item
                  }
                  active={
                    item.id ===
                    deviceId
                  }
                  onSelect={() =>
                    selectDevice(
                      item
                    )
                  }
                />
              )
            )
          }
        </div>


        <div className="mt-6 grid gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 xl:grid-cols-[1.3fr_0.7fr_0.7fr]">
          <label className="block">
            <span className="text-[10px] font-bold uppercase tracking-[0.13em] text-slate-500">
              Normal Resolution
            </span>

            <div className="relative mt-2">
              <select
                value={
                  presetKey
                }
                onChange={
                  (
                    event
                  ) =>
                    selectPreset(
                      event.target.value
                    )
                }
                disabled={
                  loading
                }
                className="h-12 w-full appearance-none rounded-xl border border-slate-200 bg-white px-4 pr-10 text-xs font-semibold text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              >
                {
                  device.presets.map(
                    (
                      preset
                    ) => (
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

                <option
                  value="custom"
                  disabled
                >
                  Custom resolution
                </option>
              </select>

              <ChevronDown
                size={16}
                className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
            </div>
          </label>


          <label className="block">
            <span className="text-[10px] font-bold uppercase tracking-[0.13em] text-slate-500">
              Width
            </span>

            <input
              type="number"
              min={
                device.minWidth
              }
              max={
                device.maxWidth
              }
              value={
                width
              }
              onChange={
                (
                  event
                ) =>
                  changeWidth(
                    event.target.value
                  )
              }
              className={[
                "mt-2 h-12 w-full rounded-xl border bg-white px-4 text-xs font-bold outline-none transition focus:ring-4",
                widthValid
                  ? "border-slate-200 text-slate-700 focus:border-blue-500 focus:ring-blue-100"
                  : "border-rose-300 text-rose-700 focus:border-rose-500 focus:ring-rose-100",
              ].join(" ")}
            />

            <p className="mt-1.5 text-[10px] text-slate-400">
              Allowed {
                device.minWidth
              }
              –
              {
                device.maxWidth
              }
              px
            </p>
          </label>


          <label className="block">
            <span className="text-[10px] font-bold uppercase tracking-[0.13em] text-slate-500">
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
                  changeHeight(
                    event.target.value
                  )
              }
              className={[
                "mt-2 h-12 w-full rounded-xl border bg-white px-4 text-xs font-bold outline-none transition focus:ring-4",
                heightValid
                  ? "border-slate-200 text-slate-700 focus:border-blue-500 focus:ring-blue-100"
                  : "border-rose-300 text-rose-700 focus:border-rose-500 focus:ring-rose-100",
              ].join(" ")}
            />
          </label>
        </div>

        {
          sessionId
          &&
          (
            <p className="mt-3 text-[11px] font-medium text-amber-600">
              Resolution changes apply when you click Restart Live Browser.
            </p>
          )
        }
      </section>


      {
        error
        &&
        (
          <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
            {error}
          </div>
        )
      }


      <section className="mt-6 overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_20px_65px_rgba(15,23,42,0.09)]">
        <div className="flex flex-col gap-4 border-b border-slate-200 bg-white px-5 py-5 sm:px-6 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold tracking-tight text-slate-950">
                Virtual Browser
              </h2>

              {
                sessionId
                ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.1em] text-emerald-700">
                      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                      Live
                    </span>
                  )
                : (
                    <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.1em] text-slate-500">
                      Not started
                    </span>
                  )
              }
            </div>

            <p className="mt-1 text-xs text-slate-500">
              Click inside the browser to interact. Mouse-wheel scrolling is now locked to the virtual browser, and the scrollbar on the right controls only the website inside the virtual screen.
            </p>
          </div>


          {
            sessionId
            &&
            (
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={
                    downloading !==
                    ""
                  }
                  onClick={() =>
                    downloadScreenshot(
                      false
                    )
                  }
                  className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-xs font-semibold text-slate-700 transition hover:border-blue-300 hover:text-blue-700 disabled:opacity-50"
                >
                  {
                    downloading ===
                    "viewport"
                      ? (
                          <LoaderCircle
                            size={14}
                            className="animate-spin"
                          />
                        )
                      : (
                          <ImageDown
                            size={14}
                          />
                        )
                  }
                  Viewport PNG
                </button>

                <button
                  type="button"
                  disabled={
                    downloading !==
                    ""
                  }
                  onClick={() =>
                    downloadScreenshot(
                      true
                    )
                  }
                  className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-xs font-semibold text-white transition hover:bg-blue-600 disabled:opacity-50"
                >
                  {
                    downloading ===
                    "full"
                      ? (
                          <LoaderCircle
                            size={14}
                            className="animate-spin"
                          />
                        )
                      : (
                          <Download
                            size={14}
                          />
                        )
                  }
                  Full Page PNG
                </button>
              </div>
            )
          }
        </div>


        {
          sessionId
          &&
          frame
            ? (
                <>
                  <div className="border-b border-slate-800 bg-slate-950 p-3 sm:p-4">
                    <form
                      onSubmit={
                        navigateBrowser
                      }
                      className="mx-auto flex max-w-[1240px] items-center gap-2"
                    >
                      <button
                        type="button"
                        onClick={() =>
                          sendAction(
                            "back"
                          )
                        }
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-300 transition hover:bg-slate-800 hover:text-white"
                        title="Back"
                      >
                        <ArrowLeft
                          size={16}
                        />
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          sendAction(
                            "forward"
                          )
                        }
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-300 transition hover:bg-slate-800 hover:text-white"
                        title="Forward"
                      >
                        <ArrowRight
                          size={16}
                        />
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          sendAction(
                            "reload"
                          )
                        }
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-300 transition hover:bg-slate-800 hover:text-white"
                        title="Reload"
                      >
                        <RefreshCw
                          size={15}
                        />
                      </button>


                      <div className="relative min-w-0 flex-1">
                        <Globe2
                          size={14}
                          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                        />

                        <input
                          value={
                            browserUrl
                          }
                          onChange={
                            (
                              event
                            ) =>
                              setBrowserUrl(
                                event.target.value
                              )
                          }
                          className="h-9 w-full rounded-lg border border-slate-700 bg-slate-900 pl-9 pr-3 text-xs font-medium text-slate-200 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                        />
                      </div>

                      <a
                        href={
                          frame.url
                        }
                        target="_blank"
                        rel="noreferrer"
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-300 transition hover:bg-slate-800 hover:text-white"
                        title="Open in normal browser"
                      >
                        <ExternalLink
                          size={15}
                        />
                      </a>
                    </form>
                  </div>


                  <div className="grid gap-2 border-b border-slate-200 bg-slate-50 px-4 py-3 sm:grid-cols-2 lg:grid-cols-5 sm:px-6">
                    <div className="text-[10px] text-slate-500">
                      <span className="font-bold text-slate-700">
                        Device:
                      </span>
                      {" "}
                      {
                        device.label
                      }
                    </div>

                    <div className="text-[10px] text-slate-500">
                      <span className="font-bold text-slate-700">
                        Viewport:
                      </span>
                      {" "}
                      {
                        frame.viewport.width
                      }
                      ×
                      {
                        frame.viewport.height
                      }
                    </div>

                    <div className="text-[10px] text-slate-500">
                      <span className="font-bold text-slate-700">
                        HTTP:
                      </span>
                      {" "}
                      {
                        frame.http_status
                        ??
                        "—"
                      }
                    </div>

                    <div className="text-[10px] text-slate-500">
                      <span className="font-bold text-slate-700">
                        Scroll:
                      </span>
                      {" "}
                      {
                        Math.round(
                          frame.scroll_y
                          ||
                          0
                        )
                      }
                      px
                    </div>

                    <div className="truncate text-[10px] text-slate-500">
                      <span className="font-bold text-slate-700">
                        Page:
                      </span>
                      {" "}
                      {
                        frame.title
                        ||
                        "Untitled"
                      }
                    </div>
                  </div>


                  <div className="overflow-auto bg-[radial-gradient(circle_at_center,#cbd5e1_1px,transparent_1px)] bg-[size:18px_18px] p-4 sm:p-7">
                    <div
                      className="mx-auto overflow-hidden rounded-[22px] border-[7px] border-slate-950 bg-slate-950 shadow-[0_32px_90px_rgba(15,23,42,0.28)]"
                      style={{
                        width:
                          `${displayWidth}px`,
                      }}
                    >
                      <div className="flex h-8 items-center justify-between border-b border-slate-800 bg-slate-950 px-3">
                        <div className="flex items-center gap-1.5">
                          <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
                          <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                        </div>

                        <span className="text-[9px] font-bold text-slate-500">
                          {
                            frame.viewport.width
                          }
                          ×
                          {
                            frame.viewport.height
                          }
                        </span>
                      </div>


                      <div
                        ref={
                          screenRef
                        }
                        tabIndex={0}
                        role="application"
                        aria-label="Live responsive browser"
                        onKeyDown={
                          handleScreenKeyDown
                        }
                        onWheelCapture={
                          handleScreenWheel
                        }
                        className="group relative cursor-default overflow-hidden bg-white outline-none ring-blue-500/40 focus:ring-4"
                        style={{
                          height:
                            `${displayHeight}px`,

                          overscrollBehavior:
                            "contain",

                          touchAction:
                            "none",
                        }}
                      >
                        <img
                          src={
                            `data:${frame.image_mime};base64,${frame.image_base64}`
                          }
                          alt="Live browser viewport"
                          draggable="false"
                          onClick={
                            handleScreenClick
                          }
                          className="block h-full w-full select-none object-fill"
                        />


                        {
                          virtualMaxScroll > 0
                          &&
                          (
                            <div
                              onMouseDown={
                                handleVirtualScrollbarClick
                              }
                              className="absolute bottom-2 right-1.5 top-2 z-20 w-3 cursor-pointer rounded-full bg-slate-950/15 p-[2px] backdrop-blur-sm"
                              title="Virtual browser scrollbar"
                            >
                              <div
                                className="absolute left-[2px] right-[2px] rounded-full bg-slate-700/75 shadow-sm transition-[top] duration-150 hover:bg-slate-800"
                                style={{
                                  height:
                                    `${virtualThumbHeightPercent}%`,

                                  top:
                                    `${virtualThumbTopPercent}%`,
                                }}
                              />
                            </div>
                          )
                        }


                        <div className="pointer-events-none absolute bottom-2 left-1/2 z-20 -translate-x-1/2 rounded-full bg-slate-950/75 px-2.5 py-1 text-[9px] font-semibold text-white/90 opacity-0 shadow-lg transition group-hover:opacity-100">
                          Scroll inside this screen
                        </div>


                        {
                          interacting
                          &&
                          (
                            <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-slate-950/10">
                              <span className="inline-flex items-center gap-2 rounded-full bg-slate-950/90 px-3 py-2 text-[10px] font-bold text-white shadow-lg">
                                <LoaderCircle
                                  size={13}
                                  className="animate-spin"
                                />
                                Updating browser
                              </span>
                            </div>
                          )
                        }
                      </div>
                    </div>
                  </div>


                  <div className="flex flex-col gap-3 border-t border-slate-200 bg-white px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
                    <div>
                      <p className="text-xs font-bold text-slate-800">
                        Real interactive Chromium session
                      </p>

                      <p className="mt-1 text-[10px] leading-5 text-slate-500">
                        Supports page navigation, links, scrolling, text entry, keyboard keys, dynamic UI, back/forward and reload. The screen is mirrored from the backend browser approximately once per second and immediately after interactions.
                      </p>
                    </div>

                    <div className="shrink-0 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[10px] font-bold text-emerald-700">
                      Session active
                    </div>
                  </div>
                </>
              )
            : (
                <div className="flex min-h-[560px] items-center justify-center bg-[radial-gradient(circle_at_center,#e2e8f0_1px,transparent_1px)] bg-[size:18px_18px] p-8">
                  <div className="max-w-md text-center">
                    <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-200 bg-white text-blue-600 shadow-lg">
                      <Monitor
                        size={28}
                      />
                    </span>

                    <h3 className="mt-5 text-lg font-bold text-slate-950">
                      Start the live browser
                    </h3>

                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      Enter a website URL, select the responsive resolution and click Start Live Browser. The page will load here as an interactive browser instead of a static full-page screenshot.
                    </p>
                  </div>
                </div>
              )
        }
      </section>
    </div>
  );
}
