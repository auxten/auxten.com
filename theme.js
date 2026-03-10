// Theme toggle
(function() {
  const toggle = document.getElementById('themeToggle');
  const html = document.documentElement;

  // Check saved preference or system preference
  const saved = localStorage.getItem('theme');
  if (saved) {
    html.setAttribute('data-theme', saved);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    html.setAttribute('data-theme', 'dark');
  } else {
    html.setAttribute('data-theme', 'light');
  }

  if (toggle) {
    toggle.addEventListener('click', function() {
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    if (!localStorage.getItem('theme')) {
      html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
  });
})();
