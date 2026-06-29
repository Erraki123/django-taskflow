/**
 * Sidebar behavior: desktop collapse/expand (persisted in
 * localStorage — this is a real Django static file served to a real
 * browser, not a Claude.ai artifact, so localStorage is fine here)
 * and a mobile slide-in drawer with a backdrop overlay.
 */
(function () {
  'use strict';

  const STORAGE_KEY = 'taskflow_sidebar_collapsed';

  function getStoredState() {
    try {
      return localStorage.getItem(STORAGE_KEY) === '1';
    } catch (e) {
      return false;
    }
  }

  function setStoredState(collapsed) {
    try {
      localStorage.setItem(STORAGE_KEY, collapsed ? '1' : '0');
    } catch (e) {
      /* ignore quota / privacy-mode errors */
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.querySelector('.sidebar');
    const mainColumn = document.querySelector('.main-column');
    const collapseBtn = document.querySelector('[data-sidebar-collapse]');
    const mobileToggle = document.querySelector('[data-sidebar-mobile-toggle]');
    const overlay = document.querySelector('[data-sidebar-overlay]');

    if (!sidebar) return;

    if (getStoredState() && window.innerWidth > 991) {
      sidebar.classList.add('is-collapsed');
      mainColumn && mainColumn.classList.add('is-expanded');
    }

    if (collapseBtn) {
      collapseBtn.addEventListener('click', function () {
        const collapsed = sidebar.classList.toggle('is-collapsed');
        mainColumn && mainColumn.classList.toggle('is-expanded', collapsed);
        setStoredState(collapsed);
      });
    }

    function openMobileSidebar() {
      sidebar.classList.add('is-mobile-open');
      overlay && overlay.classList.add('is-visible');
      document.body.style.overflow = 'hidden';
    }

    function closeMobileSidebar() {
      sidebar.classList.remove('is-mobile-open');
      overlay && overlay.classList.remove('is-visible');
      document.body.style.overflow = '';
    }

    if (mobileToggle) {
      mobileToggle.addEventListener('click', openMobileSidebar);
    }
    if (overlay) {
      overlay.addEventListener('click', closeMobileSidebar);
    }
    // Close the drawer automatically when a nav link is tapped.
    sidebar.querySelectorAll('.nav-item-link').forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 991) closeMobileSidebar();
      });
    });
  });
})();
