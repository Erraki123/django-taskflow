/**
 * Dashboard charts (Chart.js) + the animated completion ring +
 * periodic AJAX refresh of counters/charts without a page reload.
 */
(function () {
  'use strict';

  let statusChart, priorityChart, monthlyChart;

  function themeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      text: isDark ? '#ABA8C7' : '#6E6A86',
      grid: isDark ? '#2C2A4A' : '#E7E5F3',
      success: '#2ED9A3',
      warning: '#FFA73B',
      danger: '#FF6B6B',
      info: '#4FB6F0',
      primary: '#6C5DD3',
      primaryLight: '#8B7FE8',
    };
  }

  function renderStatusChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    const c = themeColors();
    return new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: chartData.labels,
        datasets: [{
          data: chartData.data,
          backgroundColor: [c.warning, c.info, c.success],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        cutout: '68%',
        plugins: {
          legend: { position: 'bottom', labels: { color: c.text, padding: 16, font: { family: 'Inter', size: 12 } } },
        },
        animation: { animateScale: true, duration: 900 },
      },
    });
  }

  function renderPriorityChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    const c = themeColors();
    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: chartData.labels,
        datasets: [{
          label: 'Tasks',
          data: chartData.data,
          backgroundColor: [c.success, c.warning, c.danger],
          borderRadius: 8,
          maxBarThickness: 46,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: c.text, font: { family: 'Inter' } } },
          y: { beginAtZero: true, ticks: { color: c.text, precision: 0 }, grid: { color: c.grid } },
        },
        animation: { duration: 900 },
      },
    });
  }

  function renderMonthlyChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    const c = themeColors();
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, 'rgba(108, 93, 211, 0.35)');
    gradient.addColorStop(1, 'rgba(108, 93, 211, 0)');

    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets: [{
          label: 'Tasks created',
          data: chartData.data,
          borderColor: c.primary,
          backgroundColor: gradient,
          borderWidth: 3,
          pointBackgroundColor: '#fff',
          pointBorderColor: c.primary,
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: c.text, font: { family: 'Inter' } } },
          y: { beginAtZero: true, ticks: { color: c.text, precision: 0 }, grid: { color: c.grid } },
        },
        animation: { duration: 900 },
      },
    });
  }

  function animateRing(percentage) {
    const fg = document.querySelector('.completion-ring-fg');
    const label = document.querySelector('.completion-ring-label .pct');
    if (!fg) return;
    const radius = fg.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    fg.style.strokeDasharray = `${circumference} ${circumference}`;
    fg.style.strokeDashoffset = circumference;

    requestAnimationFrame(() => {
      const offset = circumference - (percentage / 100) * circumference;
      fg.style.strokeDashoffset = offset;
    });

    if (label) {
      let current = 0;
      const target = Math.round(percentage);
      const step = Math.max(1, Math.round(target / 40));
      const interval = setInterval(() => {
        current = Math.min(current + step, target);
        label.textContent = `${current}%`;
        if (current >= target) clearInterval(interval);
      }, 20);
    }
  }

  function animateCounter(el, target) {
    if (!el) return;
    const duration = 800;
    const start = performance.now();
    const startVal = 0;
    function frame(now) {
      const progress = Math.min((now - start) / duration, 1);
      const value = Math.floor(startVal + (target - startVal) * progress);
      el.textContent = value;
      if (progress < 1) requestAnimationFrame(frame);
      else el.textContent = target;
    }
    requestAnimationFrame(frame);
  }

  function refreshDashboard() {
    const apiUrl = document.body.dataset.dashboardApi;
    if (!apiUrl) return;

    fetch(apiUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then((res) => res.json())
      .then((data) => {
        // Update counters
        Object.entries(data.counters).forEach(([key, value]) => {
          const el = document.querySelector(`[data-counter="${key}"]`);
          if (el && key !== 'completion_rate') animateCounter(el, value);
        });
        animateRing(data.counters.completion_rate);

        // Update charts in place
        if (statusChart) {
          statusChart.data.labels = data.status_chart.labels;
          statusChart.data.datasets[0].data = data.status_chart.data;
          statusChart.update();
        }
        if (priorityChart) {
          priorityChart.data.datasets[0].data = data.priority_chart.data;
          priorityChart.update();
        }
        if (monthlyChart) {
          monthlyChart.data.labels = data.monthly_chart.labels;
          monthlyChart.data.datasets[0].data = data.monthly_chart.data;
          monthlyChart.update();
        }
      })
      .catch(() => { /* silent: dashboard refresh is best-effort */ });
  }

  document.addEventListener('DOMContentLoaded', function () {
    const statusEl = document.getElementById('statusChart');
    const priorityEl = document.getElementById('priorityChart');
    const monthlyEl = document.getElementById('monthlyChart');
    if (!statusEl && !priorityEl && !monthlyEl) return;

    const statusData = JSON.parse(document.getElementById('status-chart-data').textContent);
    const priorityData = JSON.parse(document.getElementById('priority-chart-data').textContent);
    const monthlyData = JSON.parse(document.getElementById('monthly-chart-data').textContent);
    const completionRate = parseFloat(document.body.dataset.completionRate || '0');

    statusChart = renderStatusChart('statusChart', statusData);
    priorityChart = renderPriorityChart('priorityChart', priorityData);
    monthlyChart = renderMonthlyChart('monthlyChart', monthlyData);
    animateRing(completionRate);

    document.querySelectorAll('[data-counter]').forEach((el) => {
      const target = parseInt(el.textContent, 10) || 0;
      animateCounter(el, target);
    });

    // Refresh automatically every 60s so the dashboard stays current
    // if the user has it open in a background tab while working
    // elsewhere in the app.
    setInterval(refreshDashboard, 60000);

    // Re-render with theme-correct colors after a dark/light toggle.
    document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
      btn.addEventListener('click', function () {
        setTimeout(() => {
          [statusChart, priorityChart, monthlyChart].forEach((c) => c && c.destroy());
          statusChart = renderStatusChart('statusChart', statusData);
          priorityChart = renderPriorityChart('priorityChart', priorityData);
          monthlyChart = renderMonthlyChart('monthlyChart', monthlyData);
        }, 260);
      });
    });
  });
})();
