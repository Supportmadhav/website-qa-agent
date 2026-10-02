const API_URL =
  (import.meta.env.PUBLIC_API_URL || import.meta.env.VITE_API_URL)
  ||
  "http://127.0.0.1:8000";


export async function runSelectedScan(
  url,
  checks
) {
  const response = await fetch(
    `${API_URL}/api/scan`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        url,
        checks,
      }),
    }
  );

  const data =
    await response.json();

  if (!response.ok) {
    throw new Error(
      data?.detail
      ||
      "Unable to run the scan."
    );
  }

  return data;
}


export async function runWebsiteAudit(
  url
) {
  const response = await fetch(
    `${API_URL}/api/audit`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        url,
      }),
    }
  );

  let data = null;

  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(
      data?.detail
      ||
      "Unable to complete the website audit."
    );
  }

  return data;
}
