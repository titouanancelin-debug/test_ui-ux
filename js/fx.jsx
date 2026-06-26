/* FX : boîte à outils d'animations — scroll-reveal, parallax, rideau, spotlight.
   Tout respecte prefers-reduced-motion (dégradation gracieuse vers statique). */

const { useRef, useEffect, useState, useCallback } = React;

/* Détecte la préférence système OU la classe .anim-off posée par le panneau Tweaks */
const prefersReduced = () =>
  window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  || document.body.classList.contains("anim-off");

/* ---- useReveal : révèle un élément quand il entre dans le viewport ---- */
const useReveal = ({ delay = 0, threshold = 0.15, once = true } = {}) => {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (prefersReduced()) { el.classList.add("is-visible"); return; }
    el.style.transitionDelay = `${delay}ms`;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          el.classList.add("is-visible");
          if (once) io.unobserve(el);
        } else if (!once) {
          el.classList.remove("is-visible");
        }
      });
    }, { threshold, rootMargin: "0px 0px -8% 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, [delay, threshold, once]);
  return ref;
};

/* ---- Reveal : wrapper déclaratif ---- */
const Reveal = ({ as = "div", variant = "up", delay = 0, className = "", style = {}, children, ...rest }) => {
  const ref = useReveal({ delay });
  const Tag = as;
  return (
    <Tag ref={ref} className={`reveal reveal-${variant} ${className}`} style={style} {...rest}>
      {children}
    </Tag>
  );
};

/* ---- useParallax : translation verticale douce selon le scroll ----
   speed négatif = monte plus vite que le scroll ; positif = traîne. */
const useParallax = (speed = 0.15, maxShift = 120) => {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || prefersReduced()) return;
    let raf = null;
    const update = () => {
      raf = null;
      const rect = el.getBoundingClientRect();
      const vh = window.innerHeight;
      // progression -1 (sous le pli) → 1 (au-dessus du pli)
      const progress = (rect.top + rect.height / 2 - vh / 2) / (vh / 2 + rect.height / 2);
      const shift = Math.max(-maxShift, Math.min(maxShift, progress * speed * 100));
      el.style.transform = `translate3d(0, ${shift.toFixed(1)}px, 0)`;
    };
    const onScroll = () => { if (raf == null) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [speed, maxShift]);
  return ref;
};

/* ---- useMagnetic : bouton qui suit légèrement le curseur (desktop) ---- */
const useMagnetic = (strength = 0.25) => {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || prefersReduced() || window.matchMedia("(hover: none)").matches) return;
    const onMove = (e) => {
      const r = el.getBoundingClientRect();
      const x = (e.clientX - (r.left + r.width / 2)) * strength;
      const y = (e.clientY - (r.top + r.height / 2)) * strength;
      el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
    };
    const reset = () => { el.style.transform = "translate(0,0)"; };
    el.addEventListener("mousemove", onMove);
    el.addEventListener("mouseleave", reset);
    return () => { el.removeEventListener("mousemove", onMove); el.removeEventListener("mouseleave", reset); };
  }, [strength]);
  return ref;
};

/* ---- KineticTitle : titre dont les lignes montent en cascade derrière un masque ---- */
const KineticTitle = ({ lines, className = "", style = {}, lineDelay = 90, baseDelay = 0 }) => {
  const reduced = prefersReduced();
  return (
    <span className={className} style={style}>
      {lines.map((ln, i) => (
        <span key={i} className="kinetic-line">
          <span
            className={reduced ? "" : "kinetic-inner"}
            style={reduced ? {} : { animationDelay: `${baseDelay + i * lineDelay}ms` }}
          >
            {ln}
          </span>
          {i < lines.length - 1 && <br />}
        </span>
      ))}
    </span>
  );
};

/* ---- initFX : rideau d'intro + barre de progression (vanilla, lancé une fois) ---- */
let __fxInit = false;
const initFX = () => {
  if (__fxInit) return;
  __fxInit = true;
  initCursor();

  // --- Barre de progression de lecture ---
  const bar = document.getElementById("scroll-progress");
  if (bar) {
    let raf = null;
    const update = () => {
      raf = null;
      const h = document.documentElement.scrollHeight - window.innerHeight;
      const p = h > 0 ? window.scrollY / h : 0;
      bar.style.transform = `scaleX(${p.toFixed(4)})`;
    };
    window.addEventListener("scroll", () => { if (raf == null) raf = requestAnimationFrame(update); }, { passive: true });
    update();
  }

  // --- Floraison botanique (une fois par session) ---
  const curtain = document.getElementById("curtain");
  if (!curtain) return;
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const seen = sessionStorage.getItem("rt-curtain-seen");

  if (seen || reduced) {
    curtain.remove();
    return;
  }
  document.body.classList.add("curtain-active");

  // --- Physalis qui pousse : tige + branches + lanternes au rAF ---
  // Récupère les éléments SVG
  const gpStem = document.getElementById("gp-stem");
  const gpBranches = [1,2,3,4].map(i => document.getElementById(`gp-b${i}`));
  const gpLanterns = [1,2,3,4,5].map(i => document.getElementById(`gp-l${i}`));

  if (!gpStem) return;

  // Mémorise les longueurs (après premier paint)
  const initLengths = () => {
    const stemLen = gpStem.getTotalLength();
    gpStem.style.strokeDasharray = stemLen;
    gpStem.style.strokeDashoffset = stemLen;
    const bLens = gpBranches.map(b => {
      const l = b.getTotalLength();
      b.style.strokeDasharray = l;
      b.style.strokeDashoffset = l;
      return l;
    });

    const TOTAL = 3000;    // durée totale de l'animation (ms)
    const startT = performance.now();
    const ease = t => t < 0.5 ? 2*t*t : -1+(4-2*t)*t;  // ease-in-out
    // Segments : [progressStart, progressEnd]
    // Tige : 0 → 0.72 | branches : décalées en chevauchant la tige
    const segments = [
      { el: gpStem,       len: stemLen, s: 0,    e: 0.72 },
      { el: gpBranches[0], len: bLens[0], s: 0.20, e: 0.42 },
      { el: gpBranches[1], len: bLens[1], s: 0.36, e: 0.56 },
      { el: gpBranches[2], len: bLens[2], s: 0.50, e: 0.68 },
      { el: gpBranches[3], len: bLens[3], s: 0.62, e: 0.80 },
    ];
    // Lanternes révélées à la fin de chaque branche/tige
    const reveals = [
      { at: 0.44, el: gpLanterns[0] },   // bout branche 1
      { at: 0.58, el: gpLanterns[1] },   // bout branche 2
      { at: 0.70, el: gpLanterns[2] },   // bout branche 3
      { at: 0.82, el: gpLanterns[3] },   // bout branche 4
      { at: 0.74, el: gpLanterns[4] },   // sommet tige
    ];
    const revealed = new Set();

    const tick = (now) => {
      const rawP = (now - startT) / TOTAL;
      const p = Math.min(rawP, 1);
      const ep = ease(p);

      // Animer chaque segment
      segments.forEach(seg => {
        if (ep < seg.s) return;
        const sp = Math.min((ep - seg.s) / (seg.e - seg.s), 1);
        seg.el.style.strokeDashoffset = seg.len * (1 - sp);
      });

      // Révéler les lanternes aux seuils
      reveals.forEach(r => {
        if (ep >= r.at && !revealed.has(r.at)) {
          revealed.add(r.at);
          r.el.classList.add("gp-in");
        }
      });

      if (p < 1) { requestAnimationFrame(tick); return; }

      // Plante complète — pause courte puis clip-path monte
      window.setTimeout(() => {
        curtain.classList.add("curtain-exit");
        document.body.classList.remove("curtain-active");
      }, 500);
      window.setTimeout(() => {
        curtain.remove();
        sessionStorage.setItem("rt-curtain-seen", "1");
      }, 1300);
    };
    requestAnimationFrame(tick);
  };

  // Attendre le premier paint pour que getTotalLength() soit disponible
  requestAnimationFrame(() => requestAnimationFrame(initLengths));
};

/* ---- initCursor : curseur custom physalis (desktop uniquement) ---- */
const initCursor = () => {
  const el = document.getElementById("custom-cursor");
  if (!el) return;
  // Désactivé si touch ou reduced-motion
  if (prefersReduced() || window.matchMedia("(hover: none)").matches) {
    el.style.display = "none";
    return;
  }

  let cx = -200, cy = -200;   // position cible
  let rx = -200, ry = -200;   // position rendue (lerp)
  let raf = null;
  let hovering = false;

  const lerp = (a, b, t) => a + (b - a) * t;

  const tick = () => {
    raf = null;
    rx = lerp(rx, cx, 0.14);
    ry = lerp(ry, cy, 0.14);
    el.style.transform = `translate(calc(${rx.toFixed(1)}px - 50%), calc(${ry.toFixed(1)}px - 50%))${hovering ? " scale(1.35)" : ""}`;
    // Continue tant qu'on n'est pas arrivé
    if (Math.abs(rx - cx) > 0.3 || Math.abs(ry - cy) > 0.3) {
      raf = requestAnimationFrame(tick);
    }
  };

  document.addEventListener("mousemove", (e) => {
    cx = e.clientX;
    cy = e.clientY;
    el.classList.add("cursor-visible");
    if (!raf) raf = requestAnimationFrame(tick);
  }, { passive: true });

  document.addEventListener("mouseleave", () => el.classList.remove("cursor-visible"));

  // Grossit sur les éléments interactifs
  const HOVER_SEL = "a, button, [role='button'], .card-fx, .agenda-row, .nav-link, .nav-cta";
  document.addEventListener("mouseover", (e) => {
    hovering = !!e.target.closest(HOVER_SEL);
    el.classList.toggle("cursor-hover", hovering);
  }, { passive: true });
};

window.prefersReduced = prefersReduced;
window.initCursor = initCursor;
window.useReveal = useReveal;
window.Reveal = Reveal;
window.useParallax = useParallax;
window.useMagnetic = useMagnetic;
window.KineticTitle = KineticTitle;
window.initFX = initFX;
