(function () {
  // Göreli zaman: "12 dk önce"
  var now = Date.now();
  document.querySelectorAll("time[data-rel]").forEach(function (t) {
    var d = Date.parse(t.getAttribute("datetime"));
    if (!d) return;
    var m = Math.round((now - d) / 60000);
    var s = m < 1 ? "az önce" : m < 60 ? m + " dk önce" : m < 1440 ? Math.round(m / 60) + " saat önce" : m < 10080 ? Math.round(m / 1440) + " gün önce" : null;
    if (s) { t.title = t.textContent; t.textContent = s; }
  });

  // Yatay şerit okları
  document.querySelectorAll(".arrows").forEach(function (box) {
    var rail = document.getElementById(box.getAttribute("data-rail"));
    if (!rail) return;
    var btns = box.querySelectorAll("button");
    function update() {
      btns[0].disabled = rail.scrollLeft < 8;
      btns[1].disabled = rail.scrollLeft + rail.clientWidth > rail.scrollWidth - 8;
    }
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        var card = rail.firstElementChild;
        var step = card ? card.getBoundingClientRect().width + 20 : 300;
        rail.scrollBy({ left: step * (+b.getAttribute("data-dir")) * 2, behavior: "smooth" });
      });
    });
    rail.addEventListener("scroll", update, { passive: true });
    update();
  });

  // Bağlantıyı kopyala
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var label = b.textContent;
      try {
        navigator.clipboard.writeText(b.getAttribute("data-copy")).then(function () {
          b.textContent = "Kopyalandı";
          setTimeout(function () { b.textContent = label; }, 1600);
        });
      } catch (e) {}
    });
  });

  // Menü: bir bağlantıya basınca kapansın
  document.querySelectorAll(".menu-panel a").forEach(function (a) {
    a.addEventListener("click", function () { var m = a.closest("details"); if (m) m.open = false; });
  });
})();
