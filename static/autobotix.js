(function () {
  'use strict';
  const preference = localStorage.getItem('autobotix-theme') || 'system';
  function applyTheme(value) {
    const dark = value === 'dark' || (value === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.documentElement.dataset.themePreference = value;
    document.documentElement.classList.toggle('dark', dark);
  }
  window.AutoBotixTheme = { set(value) { localStorage.setItem('autobotix-theme', value); applyTheme(value); } };
  applyTheme(preference);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if ((localStorage.getItem('autobotix-theme') || 'system') === 'system') applyTheme('system');
  });
  function csrfToken() { return window.__csrfToken || ''; }
  function protectForms(root) {
    (root || document).querySelectorAll('form[method="post" i], form:not([method])').forEach((form) => {
      let input = form.querySelector('input[name="csrf_token"]');
      if (!input) { input = document.createElement('input'); input.type = 'hidden'; input.name = 'csrf_token'; form.prepend(input); }
      input.value = csrfToken();
    });
  }
  document.addEventListener('DOMContentLoaded', () => {
    protectForms();
    document.querySelectorAll('[data-theme-choice]').forEach((el) => el.addEventListener('click', () => window.AutoBotixTheme.set(el.dataset.themeChoice)));
    if (window.jQuery) window.jQuery.ajaxPrefilter((options, _original, xhr) => {
      if (['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.type || 'GET').toUpperCase())) xhr.setRequestHeader('X-CSRF-Token', csrfToken());
    });
  });
  const nativeFetch = window.fetch;
  window.fetch = function (input, init) {
    init = init || {};
    const method = (init.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      init.headers = new Headers(init.headers || {});
      init.headers.set('X-CSRF-Token', csrfToken());
    }
    return nativeFetch(input, init);
  };
  window.AutoBotixCSRF = { protectForms };
}());
