// Lobpreis: client-side title search on the index page.
(function () {
  var input = document.getElementById('q');
  var list = document.getElementById('songlist');
  var noResults = document.getElementById('noresults');
  if (!input || !list || !window.SONGS) return;

  // Strip combining diacritical marks (U+0300..U+036F) and lowercase.
  var COMBINING = /[̀-ͯ]/g;
  function fold(s) {
    return s.normalize('NFD').replace(COMBINING, '').toLowerCase();
  }

  // Pre-fold all titles once for fast filtering.
  var prepped = window.SONGS.map(function (s) {
    return { title: s.title, href: s.href, key: fold(s.title) };
  });

  function render(query) {
    var q = fold(query.trim());
    var matches = q ? prepped.filter(function (s) { return s.key.indexOf(q) !== -1; }) : prepped;

    if (matches.length === 0) {
      list.innerHTML = '';
      noResults.hidden = false;
      return;
    }
    noResults.hidden = true;

    var groups = {};
    var order = [];
    for (var i = 0; i < matches.length; i++) {
      var letter = (matches[i].key.charAt(0) || '#').toUpperCase();
      if (!groups[letter]) { groups[letter] = []; order.push(letter); }
      groups[letter].push(matches[i]);
    }

    var html = '';
    for (var j = 0; j < order.length; j++) {
      var L = order[j];
      html += '<section class="letter"><h2>' + escapeHtml(L) + '</h2><ul>';
      for (var k = 0; k < groups[L].length; k++) {
        var s = groups[L][k];
        html += '<li><a href="' + escapeAttr(s.href) + '">' + escapeHtml(s.title) + '</a></li>';
      }
      html += '</ul></section>';
    }
    list.innerHTML = html;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>]/g, function (c) {
      return c === '&' ? '&amp;' : c === '<' ? '&lt;' : '&gt;';
    });
  }
  function escapeAttr(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return c === '&' ? '&amp;' : c === '<' ? '&lt;' : c === '>' ? '&gt;' : c === '"' ? '&quot;' : '&#39;';
    });
  }

  var t;
  input.addEventListener('input', function () {
    clearTimeout(t);
    t = setTimeout(function () { render(input.value); }, 30);
  });

  // Initial render via JS (overrides server-rendered list with the same content).
  render('');
})();
