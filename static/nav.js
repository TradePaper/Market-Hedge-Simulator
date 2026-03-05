(function () {
  var styles = `
    .site-nav {
      background: #050911;
      border-bottom: 1px solid #111d30;
      height: 44px;
      display: flex;
      align-items: center;
      padding: 0 24px;
      gap: 0;
      position: sticky;
      top: 0;
      z-index: 200;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    .site-nav-logo {
      font-size: 12px;
      font-weight: 700;
      color: #3b82f6;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      margin-right: 28px;
      white-space: nowrap;
    }
    .site-nav-links {
      display: flex;
      align-items: center;
      gap: 2px;
      flex: 1;
    }
    .site-nav-link {
      font-size: 12px;
      font-weight: 500;
      color: #5e7a9a;
      text-decoration: none;
      padding: 5px 12px;
      border-radius: 5px;
      letter-spacing: 0.3px;
      transition: color .15s, background .15s;
      white-space: nowrap;
    }
    .site-nav-link:hover {
      color: #c8d6e8;
      background: #0d1520;
    }
    .site-nav-link.active {
      color: #e2eaf4;
      background: #0f1e36;
      font-weight: 600;
    }
  `;

  var styleEl = document.createElement('style');
  styleEl.textContent = styles;
  document.head.appendChild(styleEl);

  var nav = document.createElement('nav');
  nav.className = 'site-nav';
  nav.innerHTML = `
    <span class="site-nav-logo">ProbEdge</span>
    <div class="site-nav-links">
      <a class="site-nav-link" href="/event-markets">Event Markets Intelligence</a>
      <a class="site-nav-link" href="/hedging-simulator">Sportsbook Hedge Simulator</a>
      <a class="site-nav-link" href="/probability-gap">Probability Gap Dashboard</a>
      <a class="site-nav-link" href="/contract-library">Event Contract Library</a>
    </div>
  `;

  if (document.body) {
    document.body.insertBefore(nav, document.body.firstChild);
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      document.body.insertBefore(nav, document.body.firstChild);
    });
  }

  var path = window.location.pathname.replace(/\/$/, '');
  nav.querySelectorAll('.site-nav-link').forEach(function (link) {
    var href = link.getAttribute('href').replace(/\/$/, '');
    if (href === path) link.classList.add('active');
  });

  var analyticsScript = document.createElement('script');
  analyticsScript.src = '/static/analytics.js';
  document.head.appendChild(analyticsScript);
})();
