import {
  jsPDF,
} from "jspdf";

import autoTable from "jspdf-autotable";


export const LINK_NAME_MAX_LINE_CHARS = 40;


export function wrapLinkName(
  value
) {
  const text = (
    String(
      value
      ||
      ""
    )
      .replace(
        /\s+/g,
        " "
      )
      .trim()
    ||
    "(No link name)"
  );

  if (
    text.length
    <=
    LINK_NAME_MAX_LINE_CHARS
  ) {
    return text;
  }

  const words =
    text.split(
      " "
    );

  const lines = [];
  let current = "";

  function pushChunk(
    chunk
  ) {
    for (
      let index = 0;
      index < chunk.length;
      index +=
        LINK_NAME_MAX_LINE_CHARS
    ) {
      lines.push(
        chunk.slice(
          index,
          index +
          LINK_NAME_MAX_LINE_CHARS
        )
      );
    }
  }

  for (
    const word of
    words
  ) {
    if (!current) {
      if (
        word.length
        <=
        LINK_NAME_MAX_LINE_CHARS
      ) {
        current = word;
      } else {
        pushChunk(
          word
        );
      }

      continue;
    }

    if (
      (
        current.length
        +
        1
        +
        word.length
      )
      <=
      LINK_NAME_MAX_LINE_CHARS
    ) {
      current =
        `${current} ${word}`;

      continue;
    }

    lines.push(
      current
    );

    if (
      word.length
      <=
      LINK_NAME_MAX_LINE_CHARS
    ) {
      current = word;
    } else {
      current = "";
      pushChunk(
        word
      );
    }
  }

  if (current) {
    lines.push(
      current
    );
  }

  return lines.join(
    "\n"
  );
}


function cleanFilename(
  value
) {
  return (
    String(
      value
      ||
      "Website QA Report"
    )
      .trim()
      .replace(
        /[<>:"/\\|?*\x00-\x1F]/g,
        "-"
      )
      .replace(
        /\s+/g,
        " "
      )
      .slice(
        0,
        110
      )
    ||
    "Website QA Report"
  );
}


function cleanWebsiteName(
  report
) {
  const rawTitle =
    (
      report?.page?.title
      ||
      ""
    ).trim();

  if (rawTitle) {
    const withoutHome =
      rawTitle.replace(
        /^home\s*[-|:]\s*/i,
        ""
      );

    const parts =
      withoutHome
        .split(
          /\s+\|\s+|\s+-\s+/
        )
        .map(
          (part) =>
            part.trim()
        )
        .filter(
          Boolean
        );

    if (
      parts.length > 1
    ) {
      return parts[
        parts.length - 1
      ];
    }

    if (
      parts.length === 1
    ) {
      return parts[0];
    }
  }

  try {
    const hostname =
      new URL(
        report?.page?.final_url
        ||
        report?.page?.requested_url
      ).hostname;

    return hostname.replace(
      /^www\./i,
      ""
    );

  } catch {
    return "Website";
  }
}


export function buildDefaultReportName(
  report
) {
  const websiteName =
    cleanWebsiteName(
      report
    );

  const results =
    report?.results
    ||
    [];

  if (
    results.length === 1
  ) {
    return (
      `${results[0].label} - ${websiteName}`
    );
  }

  return websiteName;
}


function statusLabel(
  status
) {
  return String(
    status
    ||
    "info"
  ).toUpperCase();
}


function statusTextColor(
  status
) {
  if (
    status ===
    "pass"
  ) {
    return [
      5,
      150,
      105,
    ];
  }

  if (
    status ===
    "warning"
  ) {
    return [
      217,
      119,
      6,
    ];
  }

  if (
    status ===
    "fail"
  ) {
    return [
      225,
      29,
      72,
    ];
  }

  return [
    2,
    132,
    199,
  ];
}



function downloadFocusedPageSpeedPdf(
  report,
  result,
  reportName
) {
  const data =
    result.page_speed_data
    ||
    {};

  const doc =
    new jsPDF({
      unit:
        "pt",
      format:
        "a4",
    });

  const pageWidth =
    doc.internal.pageSize.getWidth();

  const pageHeight =
    doc.internal.pageSize.getHeight();

  const margin = 36;

  let currentY = 42;


  function ensureSpace(
    needed = 60
  ) {
    if (
      currentY + needed
      >
      pageHeight - 42
    ) {
      doc.addPage();
      currentY = 42;
    }
  }


  function addText(
    text,
    {
      size = 10,
      bold = false,
      gap = 6,
    } = {}
  ) {
    ensureSpace(
      size * 2
    );

    doc.setFont(
      "helvetica",
      bold
        ? "bold"
        : "normal"
    );

    doc.setFontSize(
      size
    );

    doc.setTextColor(
      15,
      23,
      42
    );

    const lines =
      doc.splitTextToSize(
        String(
          text
          ||
          ""
        ),
        pageWidth - margin * 2
      );

    for (
      const line of lines
    ) {
      doc.text(
        line,
        margin,
        currentY
      );

      currentY +=
        size + 3;
    }

    currentY += gap;
  }


  addText(
    reportName,
    {
      size:
        18,
      bold:
        true,
      gap:
        5,
    }
  );

  addText(
    "Focused Page Speed QA Report",
    {
      size:
        10,
      bold:
        true,
      gap:
        10,
    }
  );


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Page Speed Overview",
          "Value",
        ],
      ],

      body: [
        [
          "Website",
          report.page?.final_url
          ||
          "",
        ],
        [
          "Page Title",
          report.page?.title
          ||
          "",
        ],
        [
          "HTTP Status",
          String(
            report.page?.http_status
            ??
            "-"
          ),
        ],
        [
          "QA Performance Health",
          `${data.score ?? "-"} / 100 - ${data.score_label || ""}`,
        ],
        [
          "Total Requests",
          String(
            data.total_requests
            ??
            0
          ),
        ],
        [
          "Total Transfer Size",
          data.total_transfer_display
          ||
          "-",
        ],
        [
          "HTML Size",
          data.html_size_display
          ||
          "-",
        ],
      ],

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          8.5,
        cellPadding:
          5,
        valign:
          "top",
      },

      headStyles: {
        fillColor: [
          15,
          23,
          42,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },

      columnStyles: {
        0: {
          cellWidth:
            145,
          fontStyle:
            "bold",
        },
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    18;


  addText(
    "Performance Metrics",
    {
      size:
        12,
      bold:
        true,
      gap:
        5,
    }
  );


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Metric",
          "Result",
          "Status",
          "Target",
          "Meaning",
        ],
      ],

      body:
        (
          data.metrics
          ||
          []
        ).map(
          (metric) => [
            metric.label,
            metric.display,
            String(
              metric.status
              ||
              "info"
            ).toUpperCase(),
            metric.target,
            metric.description,
          ]
        ),

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          7.2,
        cellPadding:
          4,
        valign:
          "top",
        overflow:
          "linebreak",
      },

      headStyles: {
        fillColor: [
          30,
          41,
          59,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },

      columnStyles: {
        0: {
          cellWidth:
            110,
        },
        1: {
          cellWidth:
            72,
        },
        2: {
          cellWidth:
            58,
        },
        3: {
          cellWidth:
            90,
        },
        4: {
          cellWidth:
            "auto",
        },
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    18;


  addText(
    "Page Weight & Requests",
    {
      size:
        12,
      bold:
        true,
      gap:
        5,
    }
  );


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Resource Type",
          "Requests",
          "Transfer Size",
          "Status",
        ],
      ],

      body:
        (
          data.resource_summary
          ||
          []
        ).map(
          (resource) => [
            resource.type,
            resource.count,
            resource.size_display,
            String(
              resource.status
              ||
              "info"
            ).toUpperCase(),
          ]
        ),

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          8,
        cellPadding:
          5,
      },

      headStyles: {
        fillColor: [
          30,
          41,
          59,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    18;


  if (
    (
      data.recommendations
      ||
      []
    ).length
  ) {
    addText(
      "What Needs Attention",
      {
        size:
          12,
        bold:
          true,
        gap:
          5,
      }
    );


    autoTable(
      doc,
      {
        startY:
          currentY,

        head: [
          [
            "Priority",
            "Area",
            "Recommendation",
          ],
        ],

        body:
          data.recommendations.map(
            (item) => [
              item.priority,
              item.title,
              item.recommendation,
            ]
          ),

        margin: {
          left:
            margin,
          right:
            margin,
        },

        theme:
          "grid",

        styles: {
          fontSize:
            7.5,
          cellPadding:
            5,
          valign:
            "top",
          overflow:
            "linebreak",
        },

        headStyles: {
          fillColor: [
            146,
            64,
            14,
          ],
          textColor: [
            255,
            255,
            255,
          ],
          fontStyle:
            "bold",
        },

        columnStyles: {
          0: {
            cellWidth:
              60,
          },
          1: {
            cellWidth:
              130,
          },
        },
      }
    );


    currentY =
      doc.lastAutoTable.finalY
      +
      18;
  }


  if (
    (
      data.slow_resources
      ||
      []
    ).length
  ) {
    addText(
      "Slowest Resources",
      {
        size:
          12,
        bold:
          true,
        gap:
          5,
      }
    );


    autoTable(
      doc,
      {
        startY:
          currentY,

        head: [
          [
            "Resource URL",
            "Type",
            "Duration",
            "Size",
            "Status",
          ],
        ],

        body:
          data.slow_resources.map(
            (resource) => [
              resource.url,
              resource.type,
              resource.duration_ms >= 1000
                ? `${(resource.duration_ms / 1000).toFixed(2)} s`
                : `${Math.round(resource.duration_ms)} ms`,
              resource.size_kb >= 1024
                ? `${(resource.size_kb / 1024).toFixed(2)} MB`
                : `${resource.size_kb.toFixed(2)} KB`,
              String(
                resource.status
                ||
                "warning"
              ).toUpperCase(),
            ]
          ),

        margin: {
          left:
            margin,
          right:
            margin,
        },

        theme:
          "grid",

        styles: {
          fontSize:
            6.7,
          cellPadding:
            4,
          valign:
            "top",
          overflow:
            "linebreak",
        },

        headStyles: {
          fillColor: [
            30,
            41,
            59,
          ],
          textColor: [
            255,
            255,
            255,
          ],
          fontStyle:
            "bold",
        },

        columnStyles: {
          0: {
            cellWidth:
              270,
          },
          1: {
            cellWidth:
              60,
          },
          2: {
            cellWidth:
              60,
          },
          3: {
            cellWidth:
              60,
          },
          4: {
            cellWidth:
              55,
          },
        },
      }
    );


    currentY =
      doc.lastAutoTable.finalY
      +
      18;
  }


  addText(
    data.note
    ||
    (
      "QA Performance Health is a local Playwright lab score, "
      +
      "not a Google Lighthouse/PageSpeed Insights score."
    ),
    {
      size:
        7.5,
      gap:
        4,
    }
  );


  const totalPages =
    doc.getNumberOfPages();

  for (
    let pageNumber = 1;
    pageNumber <= totalPages;
    pageNumber += 1
  ) {
    doc.setPage(
      pageNumber
    );

    doc.setFont(
      "helvetica",
      "normal"
    );

    doc.setFontSize(
      8
    );

    doc.setTextColor(
      100,
      116,
      139
    );

    doc.text(
      (
        `${reportName} - `
        +
        `${pageNumber}/${totalPages}`
      ),
      margin,
      pageHeight - 22
    );
  }


  doc.save(
    `${cleanFilename(reportName)}.pdf`
  );
}


function downloadFocusedImagePdf(
  report,
  result,
  reportName
) {
  const assets =
    result.image_assets
    ||
    [];


  const doc =
    new jsPDF({
      unit:
        "pt",
      format:
        "a4",
      orientation:
        "landscape",
    });


  const pageWidth =
    doc.internal.pageSize.getWidth();

  const pageHeight =
    doc.internal.pageSize.getHeight();

  const margin =
    34;

  let currentY =
    40;


  function safe(
    value
  ) {
    return String(
      value
      ??
      ""
    )
      .replace(
        /\u2013|\u2014/g,
        "-"
      )
      .replace(
        /[^\x20-\x7E]/g,
        " "
      )
      .replace(
        /\s+/g,
        " "
      )
      .trim();
  }


  function countStatus(
    status
  ) {
    return assets.filter(
      (item) =>
        item.status ===
        status
    ).length;
  }


  function countWhere(
    predicate
  ) {
    return assets.filter(
      predicate
    ).length;
  }


  const pass =
    countStatus(
      "pass"
    );

  const warning =
    countStatus(
      "warning"
    );

  const fail =
    countStatus(
      "fail"
    );

  const info =
    countStatus(
      "info"
    );


  doc.setFont(
    "helvetica",
    "bold"
  );

  doc.setFontSize(
    18
  );

  doc.setTextColor(
    15,
    23,
    42
  );

  doc.text(
    safe(
      reportName
    ),
    margin,
    currentY
  );

  currentY +=
    20;


  doc.setFont(
    "helvetica",
    "normal"
  );

  doc.setFontSize(
    8
  );

  doc.setTextColor(
    100,
    116,
    139
  );

  doc.text(
    safe(
      report.page?.final_url
      ||
      ""
    ),
    margin,
    currentY
  );

  currentY +=
    16;


  // =====================================
  // IMAGE-LEVEL SUMMARY
  // =====================================

  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Total Images",
          "Pass",
          "Warning",
          "Fail",
          "Info",
        ],
      ],

      body: [
        [
          assets.length,
          pass,
          warning,
          fail,
          info,
        ],
      ],

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          9,
        cellPadding:
          6,
        halign:
          "center",
      },

      headStyles: {
        fillColor: [
          15,
          23,
          42,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    14;


  // =====================================
  // ISSUE OVERVIEW
  // =====================================

  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Issue",
          "Images",
        ],
      ],

      body: [
        [
          "Images > 300 KB",
          countWhere(
            (item) =>
              item.size_kb !== null
              &&
              item.size_kb !== undefined
              &&
              item.size_kb > 300
          ),
        ],

        [
          "Missing ALT",
          countWhere(
            (item) =>
              item.alt_state ===
              "Missing"
          ),
        ],

        [
          "Empty ALT",
          countWhere(
            (item) =>
              item.alt_state ===
              "Empty"
          ),
        ],

        [
          "Oversized",
          countWhere(
            (item) =>
              item.oversized
          ),
        ],

        [
          "Non-Lazy Below Fold",
          countWhere(
            (item) =>
              item.non_lazy_below_fold
          ),
        ],

        [
          "Hidden",
          countWhere(
            (item) =>
              item.hidden
          ),
        ],

        [
          "Broken / HTTP Error",
          countWhere(
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
        ],

        [
          "Unknown Size",
          countWhere(
            (item) =>
              item.size_bytes === null
              ||
              item.size_bytes === undefined
          ),
        ],
      ],

      margin: {
        left:
          margin,
        right:
          pageWidth - margin - 265,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          8,
        cellPadding:
          4,
      },

      headStyles: {
        fillColor: [
          71,
          85,
          105,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },

      columnStyles: {
        0: {
          cellWidth:
            190,
        },

        1: {
          cellWidth:
            65,
          halign:
            "center",
        },
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    14;


  // =====================================
  // ALL IMAGES
  // =====================================

  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "#",
          "Image URL",
          "Format",
          "File Size",
          "ALT",
          "Actual Dim.",
          "Displayed Dim.",
          "Loading",
          "Status",
          "Issue",
        ],
      ],

      body:
        assets.map(
          (
            item,
            index
          ) => [
            item.index
            ??
            index + 1,

            safe(
              item.url
              ||
              "No URL"
            ),

            safe(
              item.format
              ||
              "UNKNOWN"
            ),

            safe(
              item.size_label
              ||
              "Unknown"
            ),

            safe(
              item.alt_state
              ||
              "-"
            ),

            safe(
              item.natural_dimensions
              ||
              "Unknown"
            ),

            safe(
              item.display_dimensions
              ||
              "Unknown"
            ),

            safe(
              item.loading
              ||
              "default"
            ),

            safe(
              (
                (
                  item.oversized
                  &&
                  (
                    item.status === "pass"
                    ||
                    item.status === "info"
                  )
                )
                  ? "warning"
                  : (
                      item.status
                      ||
                      "info"
                    )
              ).toUpperCase()
            ),

            safe(
              (
                item.oversized
                &&
                !String(
                  item.issue_text
                  ||
                  ""
                ).includes(
                  "Oversized dimensions"
                )
              )
                ? (
                    item.issue_text
                    &&
                    item.issue_text !==
                      "No detected issue"
                      ? `Oversized dimensions; ${item.issue_text}`
                      : "Oversized dimensions"
                  )
                : (
                    item.issue_text
                    ||
                    "No detected issue"
                  )
            ),
          ]
        ),

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          6.6,
        cellPadding:
          3.5,
        valign:
          "top",
        overflow:
          "linebreak",
      },

      headStyles: {
        fillColor: [
          15,
          23,
          42,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },

      columnStyles: {
        0: {
          cellWidth:
            26,
          halign:
            "center",
        },

        1: {
          cellWidth:
            300,
        },

        2: {
          cellWidth:
            50,
          halign:
            "center",
        },

        3: {
          cellWidth:
            62,
          halign:
            "right",
        },

        4: {
          cellWidth:
            55,
        },

        5: {
          cellWidth:
            56,
        },

        6: {
          cellWidth:
            58,
          halign:
            "center",
          fontStyle:
            "bold",
        },

        7: {
          cellWidth:
            "auto",
        },
      },

      rowPageBreak:
        "avoid",

      showHead:
        "everyPage",
    }
  );


  const totalPages =
    doc.getNumberOfPages();


  for (
    let pageNumber = 1;
    pageNumber <= totalPages;
    pageNumber += 1
  ) {
    doc.setPage(
      pageNumber
    );

    doc.setFont(
      "helvetica",
      "normal"
    );

    doc.setFontSize(
      7.5
    );

    doc.setTextColor(
      100,
      116,
      139
    );

    doc.text(
      safe(
        reportName
      ),
      margin,
      pageHeight - 18
    );

    doc.text(
      `${pageNumber} / ${totalPages}`,
      pageWidth - margin,
      pageHeight - 18,
      {
        align:
          "right",
      }
    );
  }


  doc.save(
    `${cleanFilename(reportName)}.pdf`
  );
}



function downloadFocusedPageLinkPdf(
  report,
  result,
  reportName
) {
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


  const doc =
    new jsPDF({
      unit:
        "pt",
      format:
        "a4",
      orientation:
        "landscape",
    });


  const pageWidth =
    doc.internal.pageSize.getWidth();

  const pageHeight =
    doc.internal.pageSize.getHeight();

  const margin =
    34;

  let currentY =
    40;


  function safe(
    value
  ) {
    return String(
      value
      ??
      ""
    )
      .replace(
        /\u2013|\u2014/g,
        "-"
      )
      .replace(
        /[^\x20-\x7E]/g,
        " "
      )
      .replace(
        /\s+/g,
        " "
      )
      .trim();
  }


  doc.setFont(
    "helvetica",
    "bold"
  );

  doc.setFontSize(
    18
  );

  doc.setTextColor(
    15,
    23,
    42
  );

  doc.text(
    safe(
      reportName
    ),
    margin,
    currentY
  );

  currentY +=
    20;


  doc.setFont(
    "helvetica",
    "normal"
  );

  doc.setFontSize(
    8
  );

  doc.setTextColor(
    100,
    116,
    139
  );

  doc.text(
    safe(
      report.page?.final_url
      ||
      ""
    ),
    margin,
    currentY
  );

  currentY +=
    16;


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Total HTML Links",
          "Internal",
          "External",
        ],
      ],

      body: [
        [
          links.length,
          internalCount,
          externalCount,
        ],
      ],

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          9,
        cellPadding:
          6,
        halign:
          "center",
      },

      headStyles: {
        fillColor: [
          15,
          23,
          42,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    16;


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "No.",
          "URL",
          "Link Name",
          "Internal / External",
        ],
      ],

      body:
        links.map(
          (
            link,
            index
          ) => [
            link.no
            ??
            index + 1,

            safe(
              link.url
            ),

            wrapLinkName(
              safe(
                link.link_name
              )
            ),

            safe(
              link.link_type
            ),
          ]
        ),

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          7.2,
        cellPadding:
          4,
        valign:
          "top",
        overflow:
          "linebreak",
      },

      headStyles: {
        fillColor: [
          30,
          41,
          59,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },

      columnStyles: {
        0: {
          cellWidth:
            38,
          halign:
            "center",
        },

        1: {
          cellWidth:
            360,
        },

        2: {
          cellWidth:
            230,
        },

        3: {
          cellWidth:
            120,
          halign:
            "center",
        },
      },

      rowPageBreak:
        "avoid",

      showHead:
        "everyPage",
    }
  );


  const totalPages =
    doc.getNumberOfPages();


  for (
    let pageNumber = 1;
    pageNumber <= totalPages;
    pageNumber += 1
  ) {
    doc.setPage(
      pageNumber
    );

    doc.setFont(
      "helvetica",
      "normal"
    );

    doc.setFontSize(
      7.5
    );

    doc.setTextColor(
      100,
      116,
      139
    );

    doc.text(
      safe(
        reportName
      ),
      margin,
      pageHeight - 18
    );

    doc.text(
      `${pageNumber} / ${totalPages}`,
      pageWidth - margin,
      pageHeight - 18,
      {
        align:
          "right",
      }
    );
  }


  doc.save(
    `${cleanFilename(reportName)}.pdf`
  );
}



function downloadFocusedBrowserCompatibilityPdf(
  report,
  result,
  reportName
) {
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

  const doc =
    new jsPDF({
      unit:
        "pt",
      format:
        "a4",
      orientation:
        "landscape",
    });

  const pageWidth =
    doc.internal.pageSize.getWidth();

  const pageHeight =
    doc.internal.pageSize.getHeight();

  const margin =
    28;

  let currentY =
    36;


  function safe(
    value
  ) {
    return String(
      value
      ??
      ""
    )
      .replace(
        /\u2013|\u2014/g,
        "-"
      )
      .replace(
        /[^\x20-\x7E]/g,
        " "
      )
      .replace(
        /\s+/g,
        " "
      )
      .trim();
  }


  function cellText(
    cell
  ) {
    const status =
      String(
        cell?.status
        ||
        "info"
      ).toUpperCase();

    const detail =
      safe(
        cell?.detail
        ||
        ""
      );

    return (
      status
      +
      (
        detail
          ? `\n${detail}`
          : ""
      )
    );
  }


  function addTitle(
    title
  ) {
    if (
      currentY >
      pageHeight - 90
    ) {
      doc.addPage();
      currentY =
        36;
    }

    doc.setFont(
      "helvetica",
      "bold"
    );

    doc.setFontSize(
      12
    );

    doc.setTextColor(
      15,
      23,
      42
    );

    doc.text(
      safe(
        title
      ),
      margin,
      currentY
    );

    currentY +=
      8;
  }


  doc.setFont(
    "helvetica",
    "bold"
  );

  doc.setFontSize(
    17
  );

  doc.setTextColor(
    15,
    23,
    42
  );

  doc.text(
    safe(
      reportName
    ),
    margin,
    currentY
  );

  currentY +=
    18;


  doc.setFont(
    "helvetica",
    "normal"
  );

  doc.setFontSize(
    8
  );

  doc.setTextColor(
    100,
    116,
    139
  );

  doc.text(
    safe(
      report.page?.final_url
      ||
      ""
    ),
    margin,
    currentY
  );

  currentY +=
    18;


  const browserHeaders =
    browsers.map(
      (browser) =>
        (
          browser.name
          +
          (
            browser.version
              ? ` v${browser.version}`
              : ""
          )
        )
    );


  addTitle(
    "Browser Overview"
  );


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Criteria",
          ...browserHeaders,
        ],
      ],

      body:
        overviewRows.map(
          (row) => [
            safe(
              row.label
            ),

            ...browsers.map(
              (browser) =>
                cellText(
                  browser.summary?.[
                    row.id
                  ]
                )
            ),
          ]
        ),

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        fontSize:
          6.6,
        cellPadding:
          4,
        valign:
          "top",
        overflow:
          "linebreak",
      },

      headStyles: {
        fillColor: [
          15,
          23,
          42,
        ],
        textColor: [
          255,
          255,
          255,
        ],
        fontStyle:
          "bold",
      },

      columnStyles: {
        0: {
          cellWidth:
            125,
          fontStyle:
            "bold",
        },
        1: {
          cellWidth:
            155,
        },
        2: {
          cellWidth:
            155,
        },
        3: {
          cellWidth:
            155,
        },
        4: {
          cellWidth:
            155,
        },
      },

      rowPageBreak:
        "avoid",

      showHead:
        "everyPage",
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    18;


  const groups = [];

  for (
    const criterion of
    criteria
  ) {
    let group =
      groups.find(
        item =>
          item.name ===
          criterion.group
      );

    if (!group) {
      group = {
        name:
          criterion.group,

        rows:
          [],
      };

      groups.push(
        group
      );
    }

    group.rows.push(
      criterion
    );
  }


  for (
    const group of
    groups
  ) {
    addTitle(
      group.name
    );

    autoTable(
      doc,
      {
        startY:
          currentY,

        head: [
          [
            "Criteria",
            ...browserHeaders,
          ],
        ],

        body:
          group.rows.map(
            (row) => [
              safe(
                row.label
              ),

              ...browsers.map(
                (browser) =>
                  cellText(
                    browser.criteria?.[
                      row.id
                    ]
                  )
              ),
            ]
          ),

        margin: {
          left:
            margin,
          right:
            margin,
        },

        theme:
          "grid",

        styles: {
          fontSize:
            6.3,
          cellPadding:
            4,
          valign:
            "top",
          overflow:
            "linebreak",
        },

        headStyles: {
          fillColor: [
            30,
            41,
            59,
          ],
          textColor: [
            255,
            255,
            255,
          ],
          fontStyle:
            "bold",
        },

        columnStyles: {
          0: {
            cellWidth:
              125,
            fontStyle:
              "bold",
          },
          1: {
            cellWidth:
              155,
          },
          2: {
            cellWidth:
              155,
          },
          3: {
            cellWidth:
              155,
          },
          4: {
            cellWidth:
              155,
          },
        },

        rowPageBreak:
          "avoid",

        showHead:
          "everyPage",
      }
    );

    currentY =
      doc.lastAutoTable.finalY
      +
      18;
  }


  if (
    (
      data.notes
      ||
      []
    ).length
  ) {
    addTitle(
      "Important Notes"
    );

    autoTable(
      doc,
      {
        startY:
          currentY,

        head: [
          [
            "Notes",
          ],
        ],

        body:
          data.notes.map(
            note => [
              safe(
                note
              ),
            ]
          ),

        margin: {
          left:
            margin,
          right:
            margin,
        },

        theme:
          "grid",

        styles: {
          fontSize:
            7,
          cellPadding:
            5,
          valign:
            "top",
        },

        headStyles: {
          fillColor: [
            71,
            85,
            105,
          ],
          textColor: [
            255,
            255,
            255,
          ],
          fontStyle:
            "bold",
        },
      }
    );
  }


  const totalPages =
    doc.getNumberOfPages();


  for (
    let pageNumber = 1;
    pageNumber <= totalPages;
    pageNumber += 1
  ) {
    doc.setPage(
      pageNumber
    );

    doc.setFont(
      "helvetica",
      "normal"
    );

    doc.setFontSize(
      7
    );

    doc.setTextColor(
      100,
      116,
      139
    );

    doc.text(
      safe(
        reportName
      ),
      margin,
      pageHeight - 16
    );

    doc.text(
      `${pageNumber} / ${totalPages}`,
      pageWidth - margin,
      pageHeight - 16,
      {
        align:
          "right",
      }
    );
  }


  doc.save(
    `${cleanFilename(reportName)}.pdf`
  );
}



function pdfSafeV29(
  value
) {
  return String(
    value
    ??
    ""
  )
    .replace(/\u2264/g, "<=")
    .replace(/\u2265/g, ">=")
    .replace(/\u2013|\u2014/g, "-")
    .replace(/\u2018|\u2019/g, "'")
    .replace(/\u201c|\u201d/g, '"')
    .replace(/\u2192/g, "->")
    .replace(/\u00b7/g, "-")
    .replace(/\u00a0/g, " ")
    .replace(/[^\x20-\x7E]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}


function recommendationForPdfV29(
  resultId,
  finding
) {
  const status =
    finding?.status
    ||
    "info";

  if (status === "pass") {
    return "No action required.";
  }

  if (status === "info") {
    return "Information only. Review if relevant.";
  }

  const text =
    `${finding?.title || ""} ${finding?.message || ""}`
      .toLowerCase();

  const rules = [
    [/small buttons|cta/, "Increase the clickable area/padding if required."],
    [/small text|font size/, "Increase the affected text size."],
    [/clipping|clipped/, "Review overflow, fixed heights and wrapping."],
    [/line height/, "Increase line-height or remove conflicting fixed heights."],
    [/wide paragraph/, "Use a readable max-width."],
    [/image distortion/, "Preserve the source aspect ratio."],
    [/reduced motion/, "Add or verify prefers-reduced-motion handling."],
    [/animation duration|transition duration/, "Reduce unusually long timing unless intentional."],
    [/broken|404/, "Replace or remove the broken destination."],
    [/unverified/, "Review the URL manually."],
    [/spelling/, "Confirm the word in context before applying the suggestion."],
    [/grammar/, "Review the full sentence before changing it."],
  ];

  for (
    const [
      pattern,
      recommendation,
    ] of rules
  ) {
    if (pattern.test(text)) {
      return recommendation;
    }
  }

  if (resultId === "css_animation") {
    return "Review animation duration, repetition and accessibility.";
  }

  if (resultId === "layout_design") {
    return "Review the affected layout element and correct it if visibly required.";
  }

  return "Review this finding and correct it if the behavior is not intentional.";
}


function downloadPageSpeedPdfV29(
  report,
  result,
  reportName
) {
  const data =
    result.page_speed_data
    ||
    {};

  const doc =
    new jsPDF({
      unit: "pt",
      format: "a4",
    });

  const margin = 34;
  const pageHeight =
    doc.internal.pageSize.getHeight();

  let y = 38;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(17);
  doc.setTextColor(15, 23, 42);
  doc.text(
    pdfSafeV29(reportName),
    margin,
    y
  );

  y += 18;

  autoTable(
    doc,
    {
      startY: y,
      head: [[
        "Website",
        "HTTP",
      ]],
      body: [[
        pdfSafeV29(
          report.page?.final_url
          ||
          ""
        ),
        String(
          report.page?.http_status
          ??
          "-"
        ),
      ]],
      margin: {
        left: margin,
        right: margin,
      },
      theme: "grid",
      styles: {
        fontSize: 8,
        cellPadding: 5,
        valign: "top",
      },
      headStyles: {
        fillColor: [15, 23, 42],
        textColor: [255, 255, 255],
      },
    }
  );

  y =
    doc.lastAutoTable.finalY
    +
    16;

  if (!data.available) {
    autoTable(
      doc,
      {
        startY: y,
        head: [[
          "Status",
          "Details",
        ]],
        body: [[
          "FAIL",
          "Google PageSpeed Insights and Local Lighthouse could not produce a result. No score was invented.",
        ]],
        margin: {
          left: margin,
          right: margin,
        },
        theme: "grid",
        styles: {
          fontSize: 8,
          cellPadding: 5,
        },
        headStyles: {
          fillColor: [30, 41, 59],
          textColor: [255, 255, 255],
        },
      }
    );
  }

  for (
    const strategy of
    ["mobile", "desktop"]
  ) {
    const active =
      data.strategies?.[strategy];

    if (!active) {
      continue;
    }

    if (
      y >
      pageHeight - 100
    ) {
      doc.addPage();
      y = 38;
    }

    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.text(
      `${
        strategy.charAt(0).toUpperCase()
        +
        strategy.slice(1)
      } Performance`,
      margin,
      y
    );

    y += 8;

    autoTable(
      doc,
      {
        startY: y,
        head: [[
          "Source",
          "Score",
          "Status",
          "Lighthouse Version",
        ]],
        body: [[
          pdfSafeV29(
            active.source_label
            ||
            (
              active.source === "local_lighthouse"
                ? "Local Lighthouse"
                : "Google PageSpeed Insights"
            )
          ),
          `${active.score ?? "-"} / 100`,
          statusLabel(
            active.overall_status
          ),
          pdfSafeV29(
            active.lighthouse_version
            ||
            "-"
          ),
        ]],
        margin: {
          left: margin,
          right: margin,
        },
        theme: "grid",
        styles: {
          fontSize: 8,
          cellPadding: 5,
        },
        headStyles: {
          fillColor: [30, 41, 59],
          textColor: [255, 255, 255],
        },
      }
    );

    y =
      doc.lastAutoTable.finalY
      +
      10;

    autoTable(
      doc,
      {
        startY: y,
        head: [[
          "Metric",
          "Result",
          "Status",
          "Target",
          "Meaning",
        ]],
        body:
          (active.metrics || []).map(
            (metric) => [
              pdfSafeV29(metric.label),
              pdfSafeV29(metric.display),
              statusLabel(metric.status),
              pdfSafeV29(metric.target),
              pdfSafeV29(metric.description),
            ]
          ),
        margin: {
          left: margin,
          right: margin,
        },
        theme: "grid",
        styles: {
          fontSize: 7,
          cellPadding: 4,
          valign: "top",
          overflow: "linebreak",
        },
        headStyles: {
          fillColor: [15, 23, 42],
          textColor: [255, 255, 255],
        },
        columnStyles: {
          0: { cellWidth: 115 },
          1: { cellWidth: 72 },
          2: { cellWidth: 55 },
          3: { cellWidth: 80 },
        },
        rowPageBreak: "avoid",
        showHead: "everyPage",
      }
    );

    y =
      doc.lastAutoTable.finalY
      +
      12;

    const issues =
      (active.opportunities || []).filter(
        (item) =>
          item.status === "warning"
          ||
          item.status === "fail"
      );

    if (issues.length) {
      autoTable(
        doc,
        {
          startY: y,
          head: [[
            "Status",
            "What Needs Attention",
            "Measured Detail",
          ]],
          body:
            issues.map(
              (item) => [
                statusLabel(item.status),
                pdfSafeV29(item.title),
                pdfSafeV29(
                  item.display
                  ||
                  item.description
                ),
              ]
            ),
          margin: {
            left: margin,
            right: margin,
          },
          theme: "grid",
          styles: {
            fontSize: 7,
            cellPadding: 4,
            valign: "top",
          },
          headStyles: {
            fillColor: [71, 85, 105],
            textColor: [255, 255, 255],
          },
          columnStyles: {
            0: { cellWidth: 55 },
            1: { cellWidth: 190 },
          },
          rowPageBreak: "avoid",
        }
      );

      y =
        doc.lastAutoTable.finalY
        +
        16;
    }
  }

  if (
    (data.resource_summary || []).length
  ) {
    if (
      y >
      pageHeight - 100
    ) {
      doc.addPage();
      y = 38;
    }

    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.text(
      "Local Page Weight & Requests",
      margin,
      y
    );

    y += 8;

    autoTable(
      doc,
      {
        startY: y,
        head: [[
          "Resource Type",
          "Requests",
          "Transfer Size",
        ]],
        body:
          data.resource_summary.map(
            (row) => [
              row.type,
              row.count,
              row.size_display,
            ]
          ),
        margin: {
          left: margin,
          right: margin,
        },
        theme: "grid",
        styles: {
          fontSize: 8,
          cellPadding: 5,
        },
        headStyles: {
          fillColor: [15, 23, 42],
          textColor: [255, 255, 255],
        },
      }
    );
  }

  const pages =
    doc.getNumberOfPages();

  for (
    let pageNumber = 1;
    pageNumber <= pages;
    pageNumber += 1
  ) {
    doc.setPage(pageNumber);
    doc.setFontSize(7);
    doc.setTextColor(100, 116, 139);
    doc.text(
      `${pdfSafeV29(reportName)} - ${pageNumber}/${pages}`,
      margin,
      pageHeight - 18
    );
  }

  doc.save(
    `${cleanFilename(reportName)}.pdf`
  );
}


function downloadContentPdfV29(
  report,
  result,
  reportName
) {
  const doc =
    new jsPDF({
      unit: "pt",
      format: "a4",
      orientation: "landscape",
    });

  const margin = 28;
  const pageHeight =
    doc.internal.pageSize.getHeight();

  let y = 38;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(17);
  doc.setTextColor(15, 23, 42);
  doc.text(
    pdfSafeV29(reportName),
    margin,
    y
  );

  y += 18;

  autoTable(
    doc,
    {
      startY: y,
      head: [[
        "Website",
        "Page Title",
        "HTTP",
      ]],
      body: [[
        pdfSafeV29(
          report.page?.final_url
          ||
          ""
        ),
        pdfSafeV29(
          report.page?.title
          ||
          ""
        ),
        String(
          report.page?.http_status
          ??
          "-"
        ),
      ]],
      margin: {
        left: margin,
        right: margin,
      },
      theme: "grid",
      styles: {
        fontSize: 7.5,
        cellPadding: 5,
        valign: "top",
      },
      headStyles: {
        fillColor: [15, 23, 42],
        textColor: [255, 255, 255],
      },
    }
  );

  y =
    doc.lastAutoTable.finalY
    +
    14;

  const counts =
    result.counts
    ||
    {};

  autoTable(
    doc,
    {
      startY: y,
      head: [[
        "Pass",
        "Warning",
        "Fail",
        "Info",
      ]],
      body: [[
        counts.pass || 0,
        counts.warning || 0,
        counts.fail || 0,
        counts.info || 0,
      ]],
      margin: {
        left: margin,
        right: margin,
      },
      theme: "grid",
      styles: {
        fontSize: 9,
        halign: "center",
        cellPadding: 5,
      },
      headStyles: {
        fillColor: [71, 85, 105],
        textColor: [255, 255, 255],
      },
    }
  );

  y =
    doc.lastAutoTable.finalY
    +
    14;

  const issues =
    result.content_issues
    ||
    [];

  if (issues.length) {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.text(
      "Detailed Spelling & Grammar Issues",
      margin,
      y
    );

    y += 8;

    autoTable(
      doc,
      {
        startY: y,
        head: [[
          "Status",
          "Type",
          "Incorrect",
          "Suggestion",
          "Location",
          "Rule",
          "Website Content",
        ]],
        body:
          issues.map(
            (issue) => [
              statusLabel(
                issue.status
                ||
                "warning"
              ),
              pdfSafeV29(issue.type),
              pdfSafeV29(issue.incorrect),
              pdfSafeV29(
                issue.suggestion
                ||
                "Review manually"
              ),
              pdfSafeV29(issue.location),
              pdfSafeV29(issue.rule),
              pdfSafeV29(issue.context),
            ]
          ),
        margin: {
          left: margin,
          right: margin,
        },
        theme: "grid",
        styles: {
          fontSize: 6.5,
          cellPadding: 4,
          valign: "top",
          overflow: "linebreak",
        },
        headStyles: {
          fillColor: [15, 23, 42],
          textColor: [255, 255, 255],
        },
        columnStyles: {
          0: { cellWidth: 55 },
          1: { cellWidth: 55 },
          2: { cellWidth: 90 },
          3: { cellWidth: 95 },
          4: { cellWidth: 90 },
          5: { cellWidth: 120 },
        },
        rowPageBreak: "avoid",
        showHead: "everyPage",
      }
    );

    y =
      doc.lastAutoTable.finalY
      +
      14;
  }

  const summaryFindings =
    (result.findings || []).filter(
      (finding) =>
        !/^(Spelling|Grammar)\s*:/i.test(
          finding.title
          ||
          ""
        )
    );

  if (summaryFindings.length) {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.text(
      "Content Check Summary",
      margin,
      y
    );

    y += 8;

    autoTable(
      doc,
      {
        startY: y,
        head: [[
          "Status",
          "Check / Item",
          "Result / Details",
        ]],
        body:
          summaryFindings.map(
            (finding) => [
              statusLabel(finding.status),
              pdfSafeV29(finding.title),
              pdfSafeV29(finding.message),
            ]
          ),
        margin: {
          left: margin,
          right: margin,
        },
        theme: "grid",
        styles: {
          fontSize: 7.5,
          cellPadding: 5,
          valign: "top",
        },
        headStyles: {
          fillColor: [30, 41, 59],
          textColor: [255, 255, 255],
        },
        columnStyles: {
          0: { cellWidth: 65 },
          1: { cellWidth: 190 },
        },
        rowPageBreak: "avoid",
      }
    );
  }

  const pages =
    doc.getNumberOfPages();

  for (
    let pageNumber = 1;
    pageNumber <= pages;
    pageNumber += 1
  ) {
    doc.setPage(pageNumber);
    doc.setFontSize(7);
    doc.setTextColor(100, 116, 139);
    doc.text(
      `${pdfSafeV29(reportName)} - ${pageNumber}/${pages}`,
      margin,
      pageHeight - 16
    );
  }

  doc.save(
    `${cleanFilename(reportName)}.pdf`
  );
}


export function downloadPdfReport(
  report
) {
  if (!report) {
    return;
  }

  const pageSpeedOnly =
    (
      report.results
      ||
      []
    ).length === 1
    &&
    report.results[0]?.id ===
      "page_speed"
    &&
    report.results[0]?.page_speed_data;


  const contentOnly =
    (
      report.results
      ||
      []
    ).length === 1
    &&
    report.results[0]?.id ===
      "content";


  const imageOnly =
    (
      report.results
      ||
      []
    ).length === 1
    &&
    report.results[0]?.id ===
      "images";


  const pageLinkOnly =
    (
      report.results
      ||
      []
    ).length === 1
    &&
    report.results[0]?.id ===
      "page_link_list";


  const browserCompatibilityOnly =
    (
      report.results
      ||
      []
    ).length === 1
    &&
    report.results[0]?.id ===
      "browser_compatibility"
    &&
    report.results[0]?.browser_compatibility_data;


  const reportName =
    buildDefaultReportName(
      report
    );


  if (
    contentOnly
  ) {
    downloadContentPdfV29(
      report,
      report.results[0],
      reportName
    );

    return;
  }


  if (
    browserCompatibilityOnly
  ) {
    downloadFocusedBrowserCompatibilityPdf(
      report,
      report.results[0],
      reportName
    );

    return;
  }


  if (
    pageLinkOnly
  ) {
    downloadFocusedPageLinkPdf(
      report,
      report.results[0],
      reportName
    );

    return;
  }


  if (
    imageOnly
  ) {
    downloadFocusedImagePdf(
      report,
      report.results[0],
      reportName
    );

    return;
  }


  if (
    pageSpeedOnly
  ) {
    downloadPageSpeedPdfV29(
      report,
      report.results[0],
      reportName
    );

    return;
  }


  const doc =
    new jsPDF({
      unit:
        "pt",
      format:
        "a4",
    });

  const pageWidth =
    doc.internal.pageSize.getWidth();

  const pageHeight =
    doc.internal.pageSize.getHeight();

  const margin = 36;

  let currentY = 42;


  function ensureSpace(
    needed = 60
  ) {
    if (
      currentY
      +
      needed
      >
      pageHeight
      -
      42
    ) {
      doc.addPage();

      currentY = 42;
    }
  }


  function addText(
    text,
    {
      size = 10,
      bold = false,
      gap = 6,
    } = {}
  ) {
    ensureSpace(
      size * 2
    );

    doc.setFont(
      "helvetica",
      bold
        ? "bold"
        : "normal"
    );

    doc.setFontSize(
      size
    );

    doc.setTextColor(
      15,
      23,
      42
    );

    const lines =
      doc.splitTextToSize(
        String(
          text
          ||
          ""
        ),
        pageWidth
        -
        margin * 2
      );

    for (
      const line of
      lines
    ) {
      doc.text(
        line,
        margin,
        currentY
      );

      currentY +=
        size + 3;
    }

    currentY += gap;
  }


  addText(
    reportName,
    {
      size:
        18,
      bold:
        true,
      gap:
        10,
    }
  );


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Report Information",
          "Value",
        ],
      ],

      body: [
        [
          "Website",
          report.page?.final_url
          ||
          "",
        ],
        [
          "Page Title",
          report.page?.title
          ||
          "",
        ],
        [
          "HTTP Status",
          String(
            report.page?.http_status
            ??
            "-"
          ),
        ],
        [
          "Checks Scanned",
          String(
            report.check_summary?.total
            ??
            report.total_selected
            ??
            0
          ),
        ],
      ],

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        font:
          "helvetica",
        fontSize:
          8.5,
        cellPadding:
          5,
        valign:
          "top",
        overflow:
          "linebreak",
      },

      headStyles: {
        fontStyle:
          "bold",
        textColor: [
          255,
          255,
          255,
        ],
        fillColor: [
          15,
          23,
          42,
        ],
      },

      columnStyles: {
        0: {
          cellWidth:
            110,
          fontStyle:
            "bold",
        },
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    18;


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


  autoTable(
    doc,
    {
      startY:
        currentY,

      head: [
        [
          "Total Findings",
          "Pass",
          "Warning",
          "Fail",
          "Info",
        ],
      ],

      body: [
        [
          findingSummary.total
          ??
          0,

          findingSummary.pass
          ??
          0,

          findingSummary.warning
          ??
          0,

          findingSummary.fail
          ??
          0,

          findingSummary.info
          ??
          0,
        ],
      ],

      margin: {
        left:
          margin,
        right:
          margin,
      },

      theme:
        "grid",

      styles: {
        font:
          "helvetica",
        fontSize:
          9,
        halign:
          "center",
        cellPadding:
          6,
      },

      headStyles: {
        fontStyle:
          "bold",
        textColor: [
          255,
          255,
          255,
        ],
        fillColor: [
          71,
          85,
          105,
        ],
      },
    }
  );


  currentY =
    doc.lastAutoTable.finalY
    +
    20;


  if (
    (
      report.website_pages
      ||
      []
    ).length
  ) {
    ensureSpace(
      90
    );

    addText(
      "Website Page List",
      {
        size:
          13,
        bold:
          true,
        gap:
          5,
      }
    );

    autoTable(
      doc,
      {
        startY:
          currentY,

        head: [
          [
            "Page No.",
            "Page Title",
            "URL",
          ],
        ],

        body:
          report.website_pages.map(
            (
              page,
              index
            ) => [
              page.page_no
              ??
              index + 1,

              pdfSafeV29(
                page.title
                ||
                "Untitled page"
              ),

              pdfSafeV29(
                page.url
                ||
                ""
              ),
            ]
          ),

        margin: {
          left:
            margin,
          right:
            margin,
        },

        theme:
          "grid",

        styles: {
          font:
            "helvetica",
          fontSize:
            7.2,
          cellPadding:
            4,
          valign:
            "top",
          overflow:
            "linebreak",
        },

        headStyles: {
          fontStyle:
            "bold",
          textColor: [
            255,
            255,
            255,
          ],
          fillColor: [
            15,
            23,
            42,
          ],
        },

        columnStyles: {
          0: {
            cellWidth:
              50,
            halign:
              "center",
          },

          1: {
            cellWidth:
              175,
          },

          2: {
            cellWidth:
              "auto",
          },
        },

        rowPageBreak:
          "avoid",

        showHead:
          "everyPage",
      }
    );

    currentY =
      doc.lastAutoTable.finalY
      +
      20;
  }


  for (
    const result of
    report.results
    ||
    []
  ) {
    ensureSpace(
      90
    );

    addText(
      result.label,
      {
        size:
          13,
        bold:
          true,
        gap:
          2,
      }
    );

    addText(
      (
        `${result.category} | Overall: `
        +
        statusLabel(
          result.status
        )
      ),
      {
        size:
          8.5,
        gap:
          7,
      }
    );


    // =================================
    // FULL IMAGE ASSET TABLE
    // =================================

    if (
      result.id ===
      "images"
      &&
      (
        result.image_assets
        ||
        []
      ).length
    ) {
      addText(
        "All Images",
        {
          size:
            11,
          bold:
            true,
          gap:
            4,
        }
      );

      addText(
        "Warning threshold: file size greater than 300 KB.",
        {
          size:
            8,
          gap:
            5,
        }
      );

      autoTable(
        doc,
        {
          startY:
            currentY,

          head: [
            [
              "#",
              "Image URL",
              "Format",
              "File Size",
              "Status",
            ],
          ],

          body:
            result.image_assets.map(
              (
                asset,
                index
              ) => [
                asset.index
                ??
                index + 1,

                asset.url
                ||
                "",

                asset.format
                ||
                "UNKNOWN",

                asset.size_label
                ||
                "Unknown",

                statusLabel(
                  asset.status
                ),
              ]
            ),

          margin: {
            left:
              margin,
            right:
              margin,
          },

          theme:
            "grid",

          styles: {
            font:
              "helvetica",
            fontSize:
              7,
            cellPadding:
              4,
            valign:
              "top",
            overflow:
              "linebreak",
          },

          headStyles: {
            fontStyle:
              "bold",
            textColor: [
              255,
              255,
              255,
            ],
            fillColor: [
              15,
              23,
              42,
            ],
          },

          columnStyles: {
            0: {
              cellWidth:
                26,
              halign:
                "center",
            },

            1: {
              cellWidth:
                292,
            },

            2: {
              cellWidth:
                52,
              halign:
                "center",
            },

            3: {
              cellWidth:
                65,
              halign:
                "right",
            },

            4: {
              cellWidth:
                62,
              halign:
                "center",
              fontStyle:
                "bold",
            },
          },

          didParseCell:
            (hookData) => {
              if (
                hookData.section ===
                "body"
                &&
                hookData.column.index ===
                4
              ) {
                const asset =
                  result.image_assets[
                    hookData.row.index
                  ];

                if (
                  asset?.status
                ) {
                  hookData.cell.styles.textColor =
                    statusTextColor(
                      asset.status
                    );
                }
              }
            },
        }
      );

      currentY =
        doc.lastAutoTable.finalY
        +
        16;
    }



    // =================================
    // CONTENT & SPELLING DETAIL TABLE
    // =================================

    if (
      result.id ===
      "content"
      &&
      (
        result.content_issues
        ||
        []
      ).length
    ) {
      addText(
        "Detailed Content Issues",
        {
          size:
            11,
          bold:
            true,
          gap:
            4,
        }
      );

      autoTable(
        doc,
        {
          startY:
            currentY,

          head: [
            [
              "Type",
              "Incorrect",
              "Suggestion",
              "Location",
              "Rule",
              "Website Content",
            ],
          ],

          body:
            result.content_issues.map(
              (issue) => [
                issue.type,
                issue.incorrect,
                issue.suggestion
                ||
                "Review manually",
                issue.location,
                issue.rule,
                issue.context,
              ]
            ),

          margin: {
            left:
              margin,
            right:
              margin,
          },

          theme:
            "grid",

          styles: {
            font:
              "helvetica",
            fontSize:
              6.7,
            cellPadding:
              4,
            valign:
              "top",
            overflow:
              "linebreak",
          },

          headStyles: {
            fontStyle:
              "bold",
            textColor: [
              255,
              255,
              255,
            ],
            fillColor: [
              15,
              23,
              42,
            ],
          },

          columnStyles: {
            0: {
              cellWidth:
                48,
            },

            1: {
              cellWidth:
                72,
            },

            2: {
              cellWidth:
                78,
            },

            3: {
              cellWidth:
                75,
            },

            4: {
              cellWidth:
                85,
            },

            5: {
              cellWidth:
                "auto",
            },
          },

          rowPageBreak:
            "avoid",

          showHead:
            "everyPage",
        }
      );

      currentY =
        doc.lastAutoTable.finalY
        +
        16;
    }



    // =================================
    // PAGE LINK LIST TABLE
    // =================================

    if (
      result.id ===
      "page_link_list"
      &&
      (
        result.page_links
        ||
        []
      ).length
    ) {
      addText(
        "Page Link List",
        {
          size:
            11,
          bold:
            true,
          gap:
            4,
        }
      );

      autoTable(
        doc,
        {
          startY:
            currentY,

          head: [
            [
              "No.",
              "URL",
              "Link Name",
              "Internal / External",
            ],
          ],

          body:
            result.page_links.map(
              (
                link,
                index
              ) => [
                link.no
                ??
                index + 1,

                link.url,

                wrapLinkName(
                  link.link_name
                ),

                link.link_type,
              ]
            ),

          margin: {
            left:
              margin,
            right:
              margin,
          },

          theme:
            "grid",

          styles: {
            font:
              "helvetica",
            fontSize:
              6.8,
            cellPadding:
              4,
            valign:
              "top",
            overflow:
              "linebreak",
          },

          headStyles: {
            fontStyle:
              "bold",
            textColor: [
              255,
              255,
              255,
            ],
            fillColor: [
              15,
              23,
              42,
            ],
          },

          columnStyles: {
            0: {
              cellWidth:
                30,
              halign:
                "center",
            },

            1: {
              cellWidth:
                245,
            },

            2: {
              cellWidth:
                145,
            },

            3: {
              cellWidth:
                95,
            },
          },

          rowPageBreak:
            "avoid",

          showHead:
            "everyPage",
        }
      );

      currentY =
        doc.lastAutoTable.finalY
        +
        16;
    }


    // =================================
    // NORMAL QA FINDINGS TABLE
    // =================================

    const bodyRows =
      (
        result.findings
        ||
        []
      ).map(
        (finding) => [
          statusLabel(
            finding.status
          ),

          pdfSafeV29(
            finding.title
            ||
            result.label
          ),

          pdfSafeV29(
            finding.message
            ||
            ""
          ),

          pdfSafeV29(
            recommendationForPdfV29(
              result.id,
              finding
            )
          ),
        ]
      );


    autoTable(
      doc,
      {
        startY:
          currentY,

        head: [
          [
            "Status",
            "Check / Item",
            "Result / Details",
            "Recommendation",
          ],
        ],

        body:
          bodyRows.length
            ? bodyRows
            : [
                [
                  "INFO",
                  result.label,
                  "No structured findings.",
                  "Information only.",
                ],
              ],

        margin: {
          left:
            margin,
          right:
            margin,
        },

        theme:
          "grid",

        styles: {
          font:
            "helvetica",
          fontSize:
            8,
          cellPadding:
            5,
          valign:
            "top",
          overflow:
            "linebreak",
        },

        headStyles: {
          fontStyle:
            "bold",
          textColor: [
            255,
            255,
            255,
          ],
          fillColor: [
            30,
            41,
            59,
          ],
        },

        columnStyles: {
          0: {
            cellWidth:
              55,
            fontStyle:
              "bold",
          },

          1: {
            cellWidth:
              115,
          },

          2: {
            cellWidth:
              165,
          },

          3: {
            cellWidth:
              "auto",
          },
        },

        didParseCell:
          (hookData) => {
            if (
              hookData.section ===
              "body"
              &&
              hookData.column.index ===
              0
            ) {
              const finding =
                (
                  result.findings
                  ||
                  []
                )[
                  hookData.row.index
                ];

              if (
                finding?.status
              ) {
                hookData.cell.styles.textColor =
                  statusTextColor(
                    finding.status
                  );
              }
            }
          },
      }
    );


    currentY =
      doc.lastAutoTable.finalY
      +
      18;
  }


  const totalPages =
    doc.getNumberOfPages();

  for (
    let pageNumber = 1;
    pageNumber <= totalPages;
    pageNumber += 1
  ) {
    doc.setPage(
      pageNumber
    );

    doc.setFont(
      "helvetica",
      "normal"
    );

    doc.setFontSize(
      8
    );

    doc.setTextColor(
      100,
      116,
      139
    );

    doc.text(
      (
        `${reportName} - `
        +
        `${pageNumber}/${totalPages}`
      ),
      margin,
      pageHeight - 22
    );
  }


  doc.save(
    `${cleanFilename(reportName)}.pdf`
  );
}
