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

  // --- Animation JS de la floraison (rAF, plus fiable que CSS transform sur SVG) ---
  const sepals = curtain.querySelectorAll('.sepal');
  // ease-out-back : légère surtension en fin d'ouverture (effet ressort)
  const easeOutBack = t => { const c = 1.70158 + 1; return 1 + c * Math.pow(t - 1, 3) + 1.70158 * Math.pow(t - 1, 2); };
  const delays = [450, 500, 550, 550, 500];
  const dur = 1250;
  // angles finaux (positif = sens horaire, 3 = on fait -144 pour le chemin court)
  const finalAngles = [0, 72, 144, -144, -72];

  sepals.forEach((el, i) => {
    const target = finalAngles[i];
    const delay = delays[i];
    const t0 = performance.now() + delay;
    const tick = (now) => {
      const elapsed = now - t0;
      if (elapsed < 0) { requestAnimationFrame(tick); return; }
      const p = Math.min(elapsed / dur, 1);
      const angle = target * easeOutBack(p);
      el.setAttribute('transform', `rotate(${angle.toFixed(2)}, 0, 0)`);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  // Nervures : on retire la classe .sv-hidden après 1200ms pour déclencher l'animation CSS
  window.setTimeout(() => {
    curtain.querySelectorAll('.sv').forEach(el => el.classList.add('sv-draw'));
  }, 1150);

  // Exit : fade-out après que la fleur est épanouie (~2.4s) et retrait du DOM
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
