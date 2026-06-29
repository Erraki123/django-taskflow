/**
 * Theme switcher (dark / light mode).
 * Persists the choice in a cookie so the context processor on the
 * server can render the correct `data-theme` attribute on <html> on
 * the very first paint — avoiding a flash of the wrong theme.
 */
(function () {
  'use strict';

  const COOKIE_NAME = 'theme';
  const COOKIE_DAYS = 365;

  function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('.theme-toggle-switch').forEach((el) => {
      el.setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');
    });
    document.querySelectorAll('[data-theme-icon]').forEach((el) => {
      el.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    });
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    setCookie(COOKIE_NAME, next, COOKIE_DAYS);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
      btn.addEventListener('click', toggleTheme);
    });
    // Sync the switch's visual state with whatever the server rendered.
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current);
  });
})();
