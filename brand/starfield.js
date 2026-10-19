/* ============================================================
   wyo.town / starfield

   The one thing that moves. A Windows 95 style starfield: flat
   pixel stars on fixed rays flying forward past the viewer, as
   if the field is being travelled through. Each star carries its
   own depth, so a star's screen position is a perspective divide:
   the further out it flies, the faster it moves and the bigger
   it gets.

   Two things keep the field steady rather than pulsing:
     - every star runs at its own speed, so no two travel as a
       shell and fade in together;
     - a recycled star is reborn at a jittered depth, so the far
       plane stays a haze instead of refilling in one ring.

   Inks are drawn from the house sixteen. The whole thing stills
   under prefers-reduced-motion, per the brand memo.
   ============================================================ */

(function () {
  "use strict";

  var canvas = document.querySelector("[data-starfield]");
  if (!canvas || !canvas.getContext) {
    return;
  }

  var ctx = canvas.getContext("2d");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* snow mostly, a little sky and chrome: the night, catalogued */
  var INKS = ["#F6F5F0", "#F6F5F0", "#F6F5F0", "#88CCEE", "#88CCEE", "#BFBFBF"];

  var NEAR = 0.03;      /* a star below this depth recycles to the far plane */
  var SPEED = 0.00016;  /* baseline depth per millisecond */
  var DRIFT = 0.0011;   /* extra speed as a star approaches the viewer */
  var SPREAD = 0.9;     /* per-star speed spread, so nothing moves in unison */

  var w = 0;
  var h = 0;
  var cx = 0;
  var cy = 0;
  var focal = 1;
  var maxR = 1;   /* half the diagonal: a star's run to the edge, for scale */
  var stars = [];
  var raf = 0;
  var last = 0;

  function makeStar(initial) {
    return {
      /* the ray this star travels along, fixed in screen space */
      x: Math.random() * 2 - 1,
      y: Math.random() * 2 - 1,
      /* reborn near the far plane, but at its own depth in the haze */
      z: initial ? NEAR + Math.random() * (1 - NEAR) : 0.9 + Math.random() * 0.1,
      speed: 1 - SPREAD / 2 + Math.random() * SPREAD,
      ink: INKS[(Math.random() * INKS.length) | 0],
    };
  }

  function populate() {
    var target = Math.round((w * h) / 11000);
    var count = Math.max(110, Math.min(340, target));
    stars = [];
    for (var i = 0; i < count; i += 1) {
      stars.push(makeStar(true));
    }
  }

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = window.innerWidth;
    h = window.innerHeight;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
    cx = w / 2;
    cy = h / 2;
    focal = Math.min(w, h) * 0.45;
    maxR = Math.hypot(w, h) * 0.5;
    populate();
  }

  function paint() {
    ctx.clearRect(0, 0, w, h);

    for (var i = 0; i < stars.length; i += 1) {
      var s = stars[i];
      var k = focal / s.z; /* perspective: the divide is the whole trick */
      var sx = Math.round(cx + s.x * k);
      var sy = Math.round(cy + s.y * k);

      if (sx < -6 || sx > w + 6 || sy < -6 || sy > h + 6) {
        continue; /* off the field, but still travelling */
      }

      /* Size keys off distance from centre, not depth: perspective makes a
         star leave the screen while at only moderate depth, so a depth-keyed
         size never reaches its upper tiers. Screen distance keeps growing all
         the way to the edge, so the stars grow all the way out. */
      var dx = sx - cx;
      var dy = sy - cy;
      var growth = Math.min(1, Math.sqrt(dx * dx + dy * dy) / maxR);

      var size = growth > 0.78 ? 5 : growth > 0.55 ? 4 : growth > 0.3 ? 3 : 2;

      ctx.globalAlpha = Math.min(1, 0.32 + growth * 1.05);
      ctx.fillStyle = s.ink;
      ctx.fillRect(sx - (size >> 1), sy - (size >> 1), size, size);
    }

    ctx.globalAlpha = 1;
  }

  function step(now) {
    var dt = last ? Math.min(50, now - last) : 16;
    last = now;

    for (var i = 0; i < stars.length; i += 1) {
      var s = stars[i];
      s.z -= (SPEED + DRIFT * (1 - s.z)) * s.speed * dt;
      if (s.z <= NEAR) {
        stars[i] = makeStar(false);
      }
    }

    paint();
    raf = window.requestAnimationFrame(step);
  }

  function start() {
    if (raf) {
      return;
    }
    last = 0;
    raf = window.requestAnimationFrame(step);
  }

  function stop() {
    if (!raf) {
      return;
    }
    window.cancelAnimationFrame(raf);
    raf = 0;
    last = 0;
  }

  function applyMotion() {
    if (reduce.matches) {
      stop();
    } else {
      start();
    }
    paint(); /* always lay down a field, motion or not */
  }

  window.addEventListener("resize", resize, { passive: true });

  if (reduce.addEventListener) {
    reduce.addEventListener("change", applyMotion);
  } else if (reduce.addListener) {
    reduce.addListener(applyMotion);
  }

  resize();
  applyMotion();
})();
