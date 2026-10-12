```javascript
// ================================================
// LUA HUB LAUNCHER
// app.js | Navigation & UI
// ================================================

"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const navButtons = document.querySelectorAll("[data-page]");
  const pages = document.querySelectorAll(".page");
  const pageTitle = document.getElementById("page-title");
  const yearElement = document.getElementById("year");

  const pageTitles = {
    home: "Dashboard",
    apps: "Aplikasi",
    about: "Tentang LUA HUB"
  };

  // Update copyright year
  if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
  }

  // Show selected page
  function showPage(pageName) {
    if (!Object.prototype.hasOwnProperty.call(pageTitles, pageName)) {
      pageName = "home";
    }

    pages.forEach((page) => {
      page.classList.toggle("active", page.id === pageName);
    });

    navButtons.forEach((button) => {
      const active = button.dataset.page === pageName;

      button.classList.toggle("active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    });

    if (pageTitle) {
      pageTitle.textContent = pageTitles[pageName];
    }

    // Update URL hash without reloading the website
    if (window.location.hash !== `#${pageName}`) {
      history.replaceState(null, "", `#${pageName}`);
    }
  }

  // Sidebar navigation
  navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      showPage(button.dataset.page);
    });
  });

  // Buttons and links that navigate to a page
  document.querySelectorAll("[data-goto]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      showPage(link.dataset.goto);
    });
  });

  // Support browser back/forward navigation
  window.addEventListener("hashchange", () => {
    showPage(window.location.hash.slice(1) || "home");
  });

  // Open the page specified by the URL hash
  showPage(window.location.hash.slice(1) || "home");

  console.log("LUA HUB Launcher initialized.");
});
```
