/* morkit docs — version selector (vanilla, no deps).
 * Reads data-docs-root from its own <script> tag (relative path to the real
 * docs/ root), fetches docs/versions.json, renders a <select> into the header
 * (.version-mount, else .nav-actions / .crumbs), and navigates between version
 * roots on change. See docs/_scaffolder/RELEASING.md for the release ritual. */
(function () {
  var s = document.currentScript || document.querySelector('script[data-docs-root]');
  var root = (s && s.getAttribute('data-docs-root')) || '.';

  function join(a, b) {
    a = a.replace(/\/+$/, '');
    b = b.replace(/^\/+/, '');
    return b ? a + '/' + b : a;
  }

  fetch(join(root, 'versions.json'))
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var versions = (data && data.versions) || [];
      if (!versions.length) return;

      var path = location.pathname;
      var current = data.latest;
      versions.forEach(function (v) {
        if (v.path !== '.' && path.indexOf('/' + v.path + '/') !== -1) current = v.version;
      });

      var sel = document.createElement('select');
      sel.className = 'version-select';
      sel.title = 'Phiên bản tài liệu';
      sel.style.cssText = 'background:var(--bg-elev,#fff);color:var(--fg,#1a1a1a);' +
        'border:1px solid var(--border,#ccc);border-radius:6px;padding:4px 8px;' +
        'font-size:12px;cursor:pointer;margin-right:8px;font-family:inherit;';

      versions.forEach(function (v) {
        var o = document.createElement('option');
        o.value = v.path;
        o.textContent = 'v' + v.version + (v.label ? ' (' + v.label + ')' : '');
        if (v.version === current) o.selected = true;
        sel.appendChild(o);
      });

      sel.addEventListener('change', function () {
        var p = this.value;
        var base = (p === '.' || p === '') ? root : join(root, p);
        window.location.href = join(base, 'index.html');
      });

      var mount = document.querySelector('.version-mount');
      if (mount) { mount.appendChild(sel); return; }
      var host = document.querySelector('.nav-actions') || document.querySelector('.crumbs');
      if (host) host.insertBefore(sel, host.firstChild);
    })
    .catch(function () { /* offline / file:// — selector simply absent */ });
})();
