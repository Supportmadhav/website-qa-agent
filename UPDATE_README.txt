WEBSITE QA AGENT - LIVE RESPONSIVE BROWSER V26
===============================================

MAJOR CHANGE
------------

Responsive Studio is no longer only a static screenshot preview.

It now runs a persistent REAL CHROMIUM browser session on the backend and
mirrors the actual browser viewport inside the Responsive Studio.


LIVE BROWSER FUNCTIONS
----------------------

Inside the virtual browser you can now:

Click links
Click buttons
Open menus
Scroll the page
Type into focused fields
Use Enter / Tab / Backspace / Escape / Arrow keys
Navigate to another URL
Go Back
Go Forward
Reload
Review dynamic JavaScript content
Review lazy-loaded content while scrolling
Follow same-window navigation
Switch to a newly opened browser tab/window automatically


LIVE SCREEN
-----------

The virtual screen displays the CURRENT browser viewport, not one giant static
full-page screenshot.

The backend browser is refreshed on screen approximately once per second and
immediately after interactions.

This avoids the previous problem where a full-page screenshot could capture
temporary lazy-load, animation or oversized-section states.


RESPONSIVE RESOLUTIONS
----------------------

Desktop
1920px to 1440px

Laptop
1439px to 1024px

Tablet
1023px to 768px

Mobile
767px to 324px


SCREENSHOT DOWNLOADS
--------------------

Two screenshot downloads are available for the CURRENT selected resolution:

Viewport PNG
- captures exactly what is currently visible in the virtual browser

Full Page PNG
- scrolls through the page first to trigger lazy-loaded sections
- restores the browser's current scroll position
- then captures a full-page PNG

Example:

vrishal.wpdeep.in-1920x1080-viewport.png
vrishal.wpdeep.in-1920x1080-full-page.png


NORMAL BROWSER TOOLBAR
----------------------

The virtual browser includes:

Back
Forward
Reload
Editable URL bar
Open in normal browser


IMPORTANT TECHNICAL NOTE
------------------------

This is a remote/mirrored local Chromium session.

It behaves interactively like a browser, but it is not literally embedding the
target website in an iframe.

That is intentional because many websites block iframe embedding using:

X-Frame-Options
Content-Security-Policy frame-ancestors

The browser screen is mirrored as live frames from Playwright, which lets the
tool work with many more websites.

Video and high-frame-rate animations will not appear as smoothly as a native
Chrome window because the virtual screen is refreshed periodically.


INSTALL
-------

Extract directly into:

E:\website-qa-agent

Choose:

Replace the files in the destination


FILES REPLACED
--------------

app.py
frontend\src\components\ResponsivePreviewStudio.jsx


NO npm INSTALL REQUIRED.
NO NEW PYTHON PACKAGE REQUIRED.

Playwright is already part of the Website QA Agent.


RESTART
-------

Restart Website QA Agent after replacing the files.

If using the one-click launcher:

1. Stop Website QA Agent.bat
2. Start Website QA Agent.bat
