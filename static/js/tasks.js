/**
 * AJAX interactions for the task list page:
 *  - live search + filters (debounced, no page reload)
 *  - inline status / priority change via dropdown
 *  - delete with a confirmation modal, then an animated row removal
 *
 * Every fetch() call sends the Django CSRF token, read from the
 * cookie Django sets automatically (csrftoken), per Django's
 * documented AJAX pattern.
 */
(function () {
  'use strict';

  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match.pop()) : '';
  }

  const csrftoken = getCookie('csrftoken');

  function debounce(fn, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  const state = {
    listUrl: null,
  };

  function buildQuery(form) {
    const params = new URLSearchParams();
    const data = new FormData(form);
    for (const [key, value] of data.entries()) {
      if (value) params.append(key, value);
    }
    return params.toString();
  }

  function refreshTaskList(pushUrl = true) {
    const form = document.getElementById('task-filter-form');
    const container = document.getElementById('task-list-container');
    if (!form || !container) return;

    const query = buildQuery(form);
    const url = `${state.listUrl}?${query}`;

    container.style.opacity = '0.5';

    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then((res) => res.json())
      .then((data) => {
        container.innerHTML = data.html;
        container.style.opacity = '1';
        const countEl = document.getElementById('task-result-count');
        if (countEl) countEl.textContent = data.count;
        if (pushUrl) {
          history.replaceState(null, '', `${window.location.pathname}?${query}`);
        }
        attachRowHandlers();
      })
      .catch(() => {
        container.style.opacity = '1';
        window.TFToast && window.TFToast.error('Could not refresh the task list. Please try again.');
      });
  }

  function attachRowHandlers() {
    // --- Status quick-change ---
    document.querySelectorAll('[data-status-select]').forEach((select) => {
      select.addEventListener('change', function () {
        const taskId = this.dataset.taskId;
        const newStatus = this.value;
        fetch(`/tasks/${taskId}/status/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: `status=${encodeURIComponent(newStatus)}`,
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              window.TFToast.success(data.message);
              const badge = document.querySelector(`[data-status-badge="${taskId}"]`);
              if (badge) {
                badge.className = `tf-badge b-${data.status_color}`;
                badge.innerHTML = `<span class="dot"></span> ${data.status_display}`;
              }
            } else {
              window.TFToast.error(data.message || 'Could not update status.');
            }
          })
          .catch(() => window.TFToast.error('Network error while updating status.'));
      });
    });

    // --- Priority quick-change ---
    document.querySelectorAll('[data-priority-select]').forEach((select) => {
      select.addEventListener('change', function () {
        const taskId = this.dataset.taskId;
        const newPriority = this.value;
        fetch(`/tasks/${taskId}/priority/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: `priority=${encodeURIComponent(newPriority)}`,
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              window.TFToast.success(data.message);
              const badge = document.querySelector(`[data-priority-badge="${taskId}"]`);
              if (badge) {
                badge.className = `tf-badge b-${data.priority_color}`;
                badge.innerHTML = `<span class="dot"></span> ${data.priority_display}`;
              }
            } else {
              window.TFToast.error(data.message || 'Could not update priority.');
            }
          })
          .catch(() => window.TFToast.error('Network error while updating priority.'));
      });
    });

    // --- Delete (opens confirmation modal first) ---
    document.querySelectorAll('[data-delete-task]').forEach((btn) => {
      btn.addEventListener('click', function () {
        const taskId = this.dataset.taskId;
        const taskTitle = this.dataset.taskTitle;
        openDeleteModal(taskId, taskTitle);
      });
    });
  }

  function openDeleteModal(taskId, taskTitle) {
    const modalEl = document.getElementById('deleteConfirmModal');
    if (!modalEl) return;
    modalEl.querySelector('[data-modal-task-name]').textContent = taskTitle;
    modalEl.dataset.pendingTaskId = taskId;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  function performDelete(taskId) {
    const row = document.querySelector(`[data-task-row="${taskId}"]`);
    fetch(`/tasks/${taskId}/delete/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          window.TFToast.success(data.message);
          if (row) {
            row.classList.add('row-removing');
            setTimeout(() => refreshTaskList(false), 220);
          } else {
            refreshTaskList(false);
          }
        } else {
          window.TFToast.error(data.message || 'Could not delete task.');
        }
      })
      .catch(() => window.TFToast.error('Network error while deleting task.'));
  }

  document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('task-list-container');
    if (!container) return;

    state.listUrl = document.body.dataset.taskListUrl || window.location.pathname;

    const form = document.getElementById('task-filter-form');
    if (form) {
      const searchInput = form.querySelector('[name="q"]');
      if (searchInput) {
        searchInput.addEventListener('input', debounce(() => refreshTaskList(), 380));
      }
      form.querySelectorAll('select[name="status"], select[name="priority"], select[name="category"], select[name="sort"]').forEach((select) => {
        select.addEventListener('change', () => refreshTaskList());
      });
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        refreshTaskList();
      });
    }

    // Pagination links inside the AJAX-loaded partial
    container.addEventListener('click', function (e) {
      const link = e.target.closest('[data-page-link]');
      if (!link) return;
      e.preventDefault();
      const page = link.dataset.pageLink;
      const hiddenPageInput = form.querySelector('input[name="page"]');
      if (hiddenPageInput) {
        hiddenPageInput.value = page;
      } else {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'page';
        input.value = page;
        form.appendChild(input);
      }
      refreshTaskList();
    });

    attachRowHandlers();

    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', function () {
        const modalEl = document.getElementById('deleteConfirmModal');
        const taskId = modalEl.dataset.pendingTaskId;
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        if (taskId) performDelete(taskId);
      });
    }
  });
})();
