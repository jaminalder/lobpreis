// Lobpreis: theme / font-size / chord-toggle, persisted in localStorage.
(function () {
  var d = document.documentElement;
  var LS = {
    get: function (k) { try { return localStorage.getItem('lobpreis.' + k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem('lobpreis.' + k, v); } catch (e) {} },
    rm:  function (k) { try { localStorage.removeItem('lobpreis.' + k); } catch (e) {} }
  };

  // ---- theme: system -> light -> dark -> system
  var themeBtn = document.getElementById('theme-toggle');
  function currentTheme() {
    var t = LS.get('theme');
    return (t === 'light' || t === 'dark') ? t : 'system';
  }
  function applyTheme(t) {
    if (t === 'system') {
      d.removeAttribute('data-theme');
      LS.rm('theme');
    } else {
      d.setAttribute('data-theme', t);
      LS.set('theme', t);
    }
    if (themeBtn) themeBtn.textContent = t === 'light' ? '☀' : t === 'dark' ? '☾' : '◐';
  }
  applyTheme(currentTheme());
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var t = currentTheme();
    applyTheme(t === 'system' ? 'light' : t === 'light' ? 'dark' : 'system');
  });

  // ---- font size
  var MIN = 0.8, MAX = 1.8, STEP = 0.1, DEFAULT = 1.1;
  function currentSize() {
    var v = parseFloat(LS.get('fontSize'));
    return isFinite(v) ? v : DEFAULT;
  }
  function applySize(v) {
    v = Math.round(v * 10) / 10;
    if (v < MIN) v = MIN;
    if (v > MAX) v = MAX;
    d.style.setProperty('--lyrics-size', v + 'rem');
    LS.set('fontSize', String(v));
  }
  applySize(currentSize());
  var fd = document.getElementById('font-down');
  var fu = document.getElementById('font-up');
  if (fd) fd.addEventListener('click', function () { applySize(currentSize() - STEP); });
  if (fu) fu.addEventListener('click', function () { applySize(currentSize() + STEP); });

  // ---- chord visibility (currently disabled — chord placement needs fixing)
  d.classList.add('no-chords');
  var chordBtn = document.getElementById('chord-toggle');
  if (chordBtn) {
    chordBtn.disabled = true;
    chordBtn.setAttribute('aria-pressed', 'false');
    chordBtn.title = 'Akkorde zurzeit deaktiviert';
  }
})();
