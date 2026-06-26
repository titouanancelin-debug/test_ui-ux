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

  // --- Volée de physalis : on injecte plusieurs <use> et on les anime au rAF ---
  const SVGNS = "http://www.w3.org/2000/svg";
  const XLINK = "http://www.w3.org/1999/xlink";
  const field = curtain.querySelector("#physalis-field");
  const easeOutBack = t => { const c = 2.2; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };

  // Disposition : positions (en coord viewBox 1440×900), échelle, rotation de base, délai.
  // Une grande au centre, plusieurs autres réparties — comme une grappe séchée.
  const layout = [
    { x: 720, y: 430, s: 1.7,  rot: -4,  delay: 120, sway: 3 },
    { x: 470, y: 300, s: 1.05, rot: 14,  delay: 320, sway: 5 },
    { x: 990, y: 320, s: 1.2,  rot: -16, delay: 260, sway: 4 },
    { x: 360, y: 560, s: 0.78, rot: 22,  delay: 520, sway: 6 },
    { x: 1080, y: 580, s: 0.9, rot: -22, delay: 460, sway: 5 },
    { x: 600, y: 660, s: 0.62, rot: 8,   delay: 640, sway: 7 },
    { x: 860, y: 650, s: 0.7,  rot: -10, delay: 700, sway: 6 },
    { x: 250, y: 410, s: 0.5,  rot: 30,  delay: 820, sway: 8 },
    { x: 1210, y: 430, s: 0.55, rot: -28, delay: 780, sway: 7 },
  ];
  const growDur = 1100;

  layout.forEach((cfg) => {
    const use = document.createElementNS(SVGNS, "use");
    use.setAttributeNS(XLINK, "href", "#physalis");
    use.setAttribute("href", "#physalis");
    use.setAttribute("class", "physalis");
    field.appendChild(use);

    const t0 = performance.now() + cfg.delay;
    let fadedIn = false;
    const tick = (now) => {
      const elapsed = now - t0;
      if (elapsed < 0) { requestAnimationFrame(tick); return; }
      if (!fadedIn) { use.classList.add("ph-in"); fadedIn = true; }
      const p = Math.min(elapsed / growDur, 1);
      const grow = easeOutBack(p);                    // 0 → 1 avec léger rebond
      const scale = cfg.s * grow;
      // oscillation douce, perpétuelle, façon brise
      const t = elapsed / 1000;
      const angle = cfg.rot + Math.sin(t * 1.1 + cfg.x) * cfg.sway;
      const drift = Math.sin(t * 0.8 + cfg.y) * 4 * grow;
      use.setAttribute(
        "transform",
        `translate(${(cfg.x + drift).toFixed(1)}, ${cfg.y}) rotate(${angle.toFixed(2)}) scale(${scale.toFixed(3)})`
      );
      requestAnimationFrame(tick);                    // continue d'osciller jusqu'au retrait
    };
    requestAnimationFrame(tick);
  });

  // Exit : fondu après que toutes les physalis sont écloses, puis retrait du DOM
  window.setTimeout(() => {
    curtain.classList.add("curtain-exit");
    document.body.classList.remove("curtain-active");
  }, 3000);
  window.setTimeout(() => {
    curtain.remove();
    sessionStorage.setItem("rt-curtain-seen", "1");
  }, 4100);
};

window.prefersReduced = prefersReduced;
window.useReveal = useReveal;
window.Reveal = Reveal;
window.useParallax = useParallax;
window.useMagnetic = useMagnetic;
window.KineticTitle = KineticTitle;
window.initFX = initFX;
