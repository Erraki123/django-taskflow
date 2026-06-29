/**
 * Minimal toast notification system used by every AJAX interaction
 * (task delete, status change, etc.) to give the user feedback
 * without a full page reload or a jarring browser alert().
 */
window.TFToast = (function () {
  'use strict';

  function ensureStack() {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    return stack;
  }

  const ICONS = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    info: 'fa-circle-info',
    warning: 'fa-triangle-exclamation',
  };

  const COLORS = {
    success: 'var(--tf-success)',
    error: 'var(--tf-danger)',
    info: 'var(--tf-info)',
    warning: 'var(--tf-warning)',
  };

  function show(message, type = 'success', duration = 3500) {
    const stack = ensureStack();
    const toast = document.createElement('div');
    toast.className = 'tf-card';
    toast.style.cssText = `
      display:flex; align-items:center; gap:12px; padding:14px 18px;
      min-width:280px; max-width:360px; border-left:4px solid ${COLORS[type] || COLORS.info};
      animation: tf-fade-up 0.25s ease both;
    `;
    toast.innerHTML = `
      <i class="fa-solid ${ICONS[type] || ICONS.info}" style="color:${COLORS[type] || COLORS.info}; font-size:1.1rem;"></i>
      <span style="font-size:0.88rem; color:var(--tf-text-primary); flex:1;">${message}</span>
      <button type="button" style="background:none;border:none;color:var(--tf-text-muted);cursor:pointer;font-size:0.9rem;" aria-label="Dismiss">
        <i class="fa-solid fa-xmark"></i>
      </button>
    `;
    stack.appendChild(toast);

    const dismiss = () => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.2s ease';
      setTimeout(() => toast.remove(), 200);
    };

    toast.querySelector('button').addEventListener('click', dismiss);
    setTimeout(dismiss, duration);
  }

  return {
    success: (msg, d) => show(msg, 'success', d),
    error: (msg, d) => show(msg, 'error', d),
    info: (msg, d) => show(msg, 'info', d),
    warning: (msg, d) => show(msg, 'warning', d),
  };
})();
