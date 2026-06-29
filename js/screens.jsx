/* Écrans : Home, Spectacles, FicheSpectacle, Agenda, Ateliers, Équipe, Partenaires, Contact */

import { useState, useEffect, useMemo, useRef } from 'react';
import { Motif, MotifMark, Poster } from './motif.jsx';
import { SPECTACLES, AGENDA, ATELIERS, EQUIPE, PARTENAIRES } from './data.jsx';
import { prefersReduced, Reveal, KineticTitle, useParallax } from './fx.jsx';

/* ======================= NAV ======================= */
const ATELIER_CATS = [
  { id:"", label:"Tous les ateliers" },
  { id:"enfants", label:"Enfants (6–11 ans)" },
  { id:"ados", label:"Ados (12–17 ans)" },
  { id:"adultes", label:"Adultes" },
  { id:"ecole", label:"Milieu scolaire" },
  { id:"seniors", label:"Personnes âgées" },
  { id:"quartier", label:"Quartier & résidents" },
  { id:"insertion", label:"Insertion sociale" },
];

const Nav = ({ route, setRoute, setAtelierAudience }) => {
  const [scrolled, setScrolled] = useState(false);
  const [atelierOpen, setAtelierOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setAtelierOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const items = [
    { id:"home", label:"Accueil" },
    { id:"spectacles", label:"Spectacles" },
    { id:"agenda", label:"Agenda" },
    { id:"equipe", label:"Équipe" },
    { id:"partenaires", label:"Partenaires" },
    { id:"contact", label:"Contact" },
  ];

  return (
    <nav className={`nav ${scrolled ? "is-scrolled" : ""}`}>
      <div className="nav-logo" onClick={() => setRoute("home")} style={{ cursor:"pointer" }}>
        <MotifMark size={32} color="var(--terra)"/>
        <span>Cie Rouletabille</span>
      </div>
      <div className="nav-menu">
        {items.map(it => (
          <button key={it.id} className={`nav-link ${route.startsWith(it.id) ? "active" : ""}`} onClick={() => setRoute(it.id)}>
            {it.label}
          </button>
        ))}

        {/* Ateliers avec dropdown */}
        <div ref={dropdownRef} style={{ position:"relative" }}
          onMouseEnter={() => setAtelierOpen(true)}
          onMouseLeave={() => setAtelierOpen(false)}
        >
          <button
            className={`nav-link ${route === "ateliers" ? "active" : ""}`}
            onClick={() => { setAtelierAudience(""); setRoute("ateliers"); setAtelierOpen(false); }}
            style={{ display:"flex", alignItems:"center", gap:4 }}
          >
            Ateliers
            <span style={{ fontSize:9, opacity:0.55, marginTop:1, transition:"transform 0.2s", transform: atelierOpen ? "rotate(180deg)" : "rotate(0)" }}>▾</span>
          </button>
          {atelierOpen && (
            <div style={{
              position:"absolute", top:"calc(100% + 8px)", left:"50%", transform:"translateX(-50%)",
              background:"var(--paper)", border:"1px solid var(--rule)",
              boxShadow:"0 12px 32px rgba(0,0,0,0.13)", minWidth:210, zIndex:200,
              padding:"6px 0",
            }}>
              {/* petit triangle */}
              <div style={{ position:"absolute", top:-6, left:"50%", transform:"translateX(-50%)",
                width:0, height:0, borderLeft:"6px solid transparent", borderRight:"6px solid transparent",
                borderBottom:"6px solid var(--paper)", filter:"drop-shadow(0 -1px 0 var(--rule))" }}/>
              {ATELIER_CATS.map((cat, i) => (
                <button key={cat.id}
                  onClick={() => { setAtelierAudience(cat.id); setRoute("ateliers"); setAtelierOpen(false); }}
                  style={{
                    display:"block", width:"100%", textAlign:"left",
                    background:"none", border:"none", cursor:"pointer",
                    padding: i === 0 ? "10px 20px 10px" : "8px 20px",
                    fontSize:13, fontFamily:"var(--ff-body)",
                    color: i === 0 ? "var(--terra)" : "var(--ink)",
                    fontWeight: i === 0 ? 600 : 400,
                    borderBottom: i === 0 ? "1px solid var(--rule)" : "none",
                    transition:"background 0.15s",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = "color-mix(in oklab, var(--terra) 7%, transparent)"}
                  onMouseLeave={e => e.currentTarget.style.background = "none"}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <button className="nav-cta" onClick={() => setRoute("agenda")}>Réserver</button>
      </div>
    </nav>
  );
};

/* ======================= PARALLAX HERO ======================= */
/*
 * PHOTOS PLACEHOLDER — remplacer ces 4 URLs la semaine prochaine :
 *   HERO_MAIN  : photo principale (plein écran, format paysage)
 *   HERO_F0    : photo flottante gauche haute (portrait)
 *   HERO_F1    : photo flottante droite (portrait)
 *   HERO_F2    : photo flottante gauche basse (portrait)
 */
const HERO_MAIN = "images/p1.jpg";
const HERO_F0   = "images/p2.jpg";
const HERO_F1   = "images/p3.jpg";
const HERO_F2   = "images/p4.jpg";

const SCROLL_H = 2200;

const ParallaxHero = ({ setRoute }) => {
  const centerRef = useRef(null);
  const float0    = useRef(null);
  const float1    = useRef(null);
  const float2    = useRef(null);

  useEffect(() => {
    if (prefersReduced()) return;
    let raf = null;
    const update = () => {
      raf = null;
      const p = Math.min(Math.max(window.scrollY / SCROLL_H, 0), 1);
      const c = 28 * (1 - p);
      const e = 100 - c;
      if (centerRef.current) {
        centerRef.current.style.clipPath = `polygon(${c}% ${c}%, ${e}% ${c}%, ${e}% ${e}%, ${c}% ${e}%)`;
        centerRef.current.style.backgroundSize = `${170 - 70 * p}%`;
      }
      const shifts = [-180, 230, -120];
      [float0, float1, float2].forEach((r, i) => {
        if (r.current) r.current.style.transform = `translateY(${p * shifts[i]}px)`;
      });
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => { window.removeEventListener("scroll", onScroll); if (raf) cancelAnimationFrame(raf); };
  }, []);

  const floatStyle = (top, side, w, extra = {}) => ({
    position:"absolute", [side[0]]:side[1], top, width:w, zIndex:3,
    willChange:"transform", overflow:"hidden", borderRadius:3,
    boxShadow:"0 16px 48px rgba(0,0,0,0.55)", ...extra,
  });

  return (
    <div style={{ height:`calc(${SCROLL_H}px + 100vh)`, position:"relative" }}>
      <div style={{ position:"sticky", top:0, height:"100vh", overflow:"hidden", background:"#1A0E08" }}>

        {/* Image centrale qui s'ouvre au scroll */}
        <div ref={centerRef} style={{
          position:"absolute", inset:0,
          backgroundImage:`url(${HERO_MAIN})`,
          backgroundSize:"170%", backgroundPosition:"center",
          backgroundRepeat:"no-repeat",
          clipPath:"polygon(28% 28%, 72% 28%, 72% 72%, 28% 72%)",
          willChange:"clip-path, background-size",
        }}/>

        {/* Image flottante gauche haute */}
        <div ref={float0} style={floatStyle("10%", ["left","4%"], "20%")}>
          <div style={{ paddingTop:"135%", background:`url(${HERO_F0}) center/cover` }}/>
        </div>

        {/* Image flottante droite */}
        <div ref={float1} style={floatStyle("28%", ["right","3%"], "17%")}>
          <div style={{ paddingTop:"125%", background:`url(${HERO_F1}) center/cover` }}/>
        </div>

        {/* Image flottante gauche basse */}
        <div ref={float2} style={{ ...floatStyle("auto", ["left","7%"], "15%"), bottom:"18%" }}>
          <div style={{ paddingTop:"115%", background:`url(${HERO_F2}) center/cover` }}/>
        </div>

        {/* Dégradé gauche pour lisibilité texte */}
        <div style={{ position:"absolute", inset:0, zIndex:2,
          background:"linear-gradient(to right, rgba(26,14,8,0.88) 0%, rgba(26,14,8,0.55) 40%, rgba(26,14,8,0.08) 65%, transparent 100%)" }}/>

        {/* Dégradé bas */}
        <div style={{ position:"absolute", bottom:0, left:0, right:0, height:180, zIndex:4,
          background:"linear-gradient(to bottom, transparent, #1A0E08)" }}/>

        {/* Texte hero */}
        <div style={{ position:"relative", zIndex:5, padding:"0 var(--pad-x)", maxWidth:640,
          height:"100%", display:"flex", flexDirection:"column", justifyContent:"center" }}>
          <Reveal variant="fade" delay={50} className="eyebrow" style={{ color:"var(--amber)", marginBottom:24 }}>
            Saison 2025 — 2026 · Toulon & tournée
          </Reveal>
          <h1 className="display" style={{ fontSize:"clamp(56px, 8vw, 118px)", marginBottom:28, color:"var(--paper)" }}>
            <KineticTitle lineDelay={110} baseDelay={150} lines={[
              <>Théâtre <span className="display-italic">vivant</span>,</>,
              <>corps & <span className="display-italic">voix</span>.</>,
            ]}/>
          </h1>
          <Reveal variant="up" delay={500} as="p" style={{ fontSize:18, lineHeight:1.6, color:"color-mix(in oklab, var(--paper) 82%, transparent)", textWrap:"pretty", maxWidth:460, marginBottom:32 }}>
            Compagnie de création installée à Toulon depuis 2014. Des spectacles qui traversent les frontières du réel et du fantastique, ouverts à tous.
          </Reveal>
          <Reveal variant="up" delay={620} style={{ display:"flex", gap:12, flexWrap:"wrap" }}>
            <button className="btn btn-amber" onClick={() => setRoute("spectacles")}>Découvrir les spectacles →</button>
            <button className="btn btn-ghost" onClick={() => setRoute("agenda")} style={{ color:"var(--paper)", borderColor:"color-mix(in oklab, var(--paper) 40%, transparent)" }}>Voir l'agenda</button>
          </Reveal>
        </div>

        <div className="scroll-cue">
          <span>Défiler</span>
          <span className="cue-rail"><span className="cue-dot"/></span>
        </div>
      </div>
    </div>
  );
};

/* ======================= HOME ======================= */
const Home = ({ setRoute, setSpectacle }) => {
  return (
  <>
    <ParallaxHero setRoute={setRoute}/>

    {/* MARQUEE */}
    <div className="marquee">
      <div className="marquee-track">
        {[...Array(2)].map((_,k) => (
          <span key={k} className="marquee-item">
            Théâtre <span className="marquee-sep"/> Danse-théâtre <span className="marquee-sep"/> Conte musical <span className="marquee-sep"/> Ateliers enfants <span className="marquee-sep"/> Médiation culturelle <span className="marquee-sep"/> Création collective <span className="marquee-sep"/> Tournée 2026 <span className="marquee-sep"/>
          </span>
        ))}
      </div>
    </div>

    {/* SPECTACLES PREVIEW */}
    <section className="section">
      <Reveal variant="up" className="section-head">
        <div className="section-num">№ 01 / Affiche</div>
        <h2 className="section-title">Spectacles<br/><span className="display-italic">à l'affiche.</span></h2>
        <div className="section-meta">Six créations en répertoire, du conte musical au théâtre brut. <a className="link-underline" onClick={() => setRoute("spectacles")}>Tous les spectacles →</a></div>
      </Reveal>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"var(--grid-gap)" }}>
        {SPECTACLES.slice(0,4).map((s,i) => (
          <Reveal key={s.id} variant="up" delay={i*90}>
            <SpectacleCard s={s} variant={i % 4} onClick={() => { setSpectacle(s.id); setRoute("spectacles/detail"); }}/>
          </Reveal>
        ))}
      </div>
    </section>

    {/* PROCHAINES DATES */}
    <section className="section" style={{ background:"var(--paper-warm)" }}>
      <Reveal variant="up" className="section-head">
        <div className="section-num">№ 02 / Agenda</div>
        <h2 className="section-title">Prochaines<br/><span className="display-italic">dates.</span></h2>
        <div className="section-meta">Une saison de tournée entre Provence, Languedoc et Avignon. <a className="link-underline" onClick={() => setRoute("agenda")}>Calendrier complet →</a></div>
      </Reveal>
      <div style={{ display:"flex", flexDirection:"column" }}>
        {AGENDA.slice(0,5).map((d,i) => (
          <Reveal key={i} variant="up" delay={i*60}>
            <AgendaRow d={d} onClick={() => { setSpectacle(d.spectacle); setRoute("spectacles/detail"); }}/>
          </Reveal>
        ))}
      </div>
    </section>

    {/* ABOUT BAND */}
    <section className="section" style={{ background:"var(--aubergine)", color:"var(--paper)", position:"relative", overflow:"hidden" }}>
      <div ref={useParallax(0.22, 130)} className="motif-bg" style={{ right:-100, top:-80, opacity:0.4 }}>
        <Motif size={500} color="var(--paper)" berryColor="var(--amber)" rotate={20} seed={3.2}/>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1.3fr", gap:80, alignItems:"center", position:"relative", zIndex:2 }}>
        <Reveal variant="left">
          <div className="eyebrow" style={{ color:"var(--amber)", marginBottom:24 }}>La compagnie</div>
          <h2 className="display" style={{ fontSize:"clamp(48px, 6vw, 84px)" }}>
            Faire théâtre <span className="display-italic">avec</span>
            <br/>les gens, <span className="display-italic">pour</span>
            <br/>les gens.
          </h2>
        </Reveal>
        <Reveal variant="right" delay={120}>
          <p style={{ fontSize:18, lineHeight:1.6, color:"color-mix(in oklab, var(--paper) 88%, transparent)", marginBottom:24, textWrap:"pretty" }}>
            La pratique et l'accompagnement artistiques sont au cœur du projet de la Cie Rouletabille. Chaque saison, plus de dix-sept projets d'interventions sont élaborés en partenariat avec des structures sociales, éducatives et médico-sociales du territoire.
          </p>
          <p style={{ fontSize:18, lineHeight:1.6, color:"color-mix(in oklab, var(--paper) 88%, transparent)", marginBottom:32 }}>
            Une compagnie qui pense le spectacle vivant comme un geste partagé, où la salle commence dans la rue et le plateau dans l'écoute.
          </p>
          <button className="btn btn-amber" onClick={() => setRoute("equipe")}>Rencontrer l'équipe →</button>
        </Reveal>
      </div>
    </section>

    {/* NEWSLETTER */}
    <Newsletter/>
  </>
  );
};

/* ======================= SPECTACLE CARD ======================= */
const SpectacleCard = ({ s, variant=0, onClick }) => (
  <article className="card card-fx" onClick={onClick} style={{ cursor:"pointer", background:"transparent", border:"none" }}>
    <div className="card-img noise" style={{ aspectRatio:"4/5" }}>
      <Poster bg={s.color} ink={s.textColor} title={s.title} subtitle={s.tag} num={s.num} variant={variant}/>
    </div>
    <div style={{ padding:"16px 4px 8px", display:"flex", justifyContent:"space-between", alignItems:"baseline", borderTop:"1px solid var(--rule)", marginTop:12 }}>
      <div>
        <div className="tag" style={{ color:"var(--terra)", marginBottom:4 }}>{s.tag} · {s.duration}</div>
        <h3 className="display" style={{ fontSize:24, lineHeight:1.05 }}>{s.title}<span className="card-arrow">→</span></h3>
      </div>
      <div className="mono" style={{ opacity:0.6 }}>{s.date}</div>
    </div>
  </article>
);

/* ======================= AGENDA ROW ======================= */
const AgendaRow = ({ d, onClick }) => {
  const status = {
    available: { label:"Places disponibles", color:"var(--terra)" },
    few:       { label:"Dernières places", color:"var(--amber-deep)" },
    sold:      { label:"Complet", color:"var(--ink-soft)" },
  }[d.status];
  return (
    <div className="agenda-row" style={{
      display:"grid", gridTemplateColumns:"110px 1fr 1fr 180px 140px 60px",
      alignItems:"center", gap:24,
      padding:"24px 8px", borderTop:"1px solid var(--rule)",
      cursor:"pointer", transition:"background 0.2s"
    }}
    onMouseEnter={e => e.currentTarget.style.background = "color-mix(in oklab, var(--terra) 6%, transparent)"}
    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
    onClick={onClick}
    >
      <div>
        <div className="display" style={{ fontSize:48, lineHeight:1 }}>{d.day}</div>
        <div className="mono" style={{ marginTop:4 }}>{d.month} {d.year}</div>
      </div>
      <div>
        <h4 className="display" style={{ fontSize:28, lineHeight:1.05 }}>{d.title}</h4>
      </div>
      <div style={{ fontFamily:"var(--ff-body)", fontSize:14, color:"var(--ink-soft)" }}>{d.venue}</div>
      <div className="mono">{d.time} · {d.price}</div>
      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
        <span style={{ width:6, height:6, borderRadius:"50%", background:status.color }}/>
        <span style={{ fontSize:11, color:status.color, fontWeight:500 }}>{status.label}</span>
      </div>
      <div style={{ textAlign:"right", fontSize:18 }}>→</div>
    </div>
  );
};

/* ======================= SPECTACLES (liste) ======================= */
const Spectacles = ({ setRoute, setSpectacle }) => {
  const [filter, setFilter] = useState("Tous");
  const filters = ["Tous", "Théâtre", "Danse-théâtre", "Jeune public", "Création", "Conte musical"];
  const list = SPECTACLES.filter(s => filter === "Tous" || s.tag === filter);
  return (
    <>
      <section className="section" style={{ position:"relative", overflow:"hidden" }}>
        <div ref={useParallax(0.2, 120)} className="motif-bg" style={{ right:-50, top:0, opacity:0.3 }}>
          <Motif size={420} color="var(--terra)" berryColor="var(--amber)" rotate={15} seed={2}/>
        </div>
        <Reveal variant="up" className="section-head">
          <div className="section-num">№ 01 / Répertoire</div>
          <h2 className="section-title">Six <span className="display-italic">créations</span><br/>en répertoire.</h2>
          <div className="section-meta">Six pièces de format et public différents, traversées par une même quête : faire entendre les voix qu'on n'entend pas.</div>
        </Reveal>
        <div style={{ display:"flex", gap:8, marginBottom:40, flexWrap:"wrap" }}>
          {filters.map(f => (
            <button key={f} className={`tweak-pill ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>{f}</button>
          ))}
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:"var(--grid-gap)" }}>
          {list.map((s,i) => (
            <Reveal key={s.id} variant="up" delay={(i % 3) * 80}>
              <SpectacleCard s={s} variant={i} onClick={() => { setSpectacle(s.id); setRoute("spectacles/detail"); }}/>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
};

/* ======================= FICHE SPECTACLE ======================= */
const FicheSpectacle = ({ id, setRoute, setSpectacle }) => {
  const s = SPECTACLES.find(x => x.id === id) || SPECTACLES[0];
  const dates = AGENDA.filter(a => a.spectacle === s.id);
  return (
    <>
      <section className="section" style={{ paddingBottom:40 }}>
        <button className="nav-link" onClick={() => setRoute("spectacles")} style={{ paddingLeft:0, marginBottom:24 }}>← Tous les spectacles</button>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1.2fr", gap:64, alignItems:"start" }}>
          <div className="noise" style={{ position:"relative", aspectRatio:"4/5", overflow:"hidden" }}>
            <Poster bg={s.color} ink={s.textColor} title={s.title} subtitle={s.tag} num={s.num} variant={2}/>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom:20 }}>№ {s.num} · {s.tag} · {s.duration} · {s.ages}</div>
            <h1 className="display" style={{ fontSize:"clamp(60px, 8vw, 120px)", marginBottom:32 }}>
              {s.title.split(" ").map((w,i) => i === 1 ? <span key={i} className="display-italic">{w} </span> : <span key={i}>{w} </span>)}
            </h1>
            <p style={{ fontSize:20, lineHeight:1.5, marginBottom:32, color:"var(--ink-soft)", textWrap:"pretty" }}>{s.desc}</p>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:24, padding:"24px 0", borderTop:"1px solid var(--rule)", borderBottom:"1px solid var(--rule)", marginBottom:32 }}>
              <div><div className="mono" style={{ opacity:0.5, marginBottom:6 }}>Texte</div><div>{s.auteur}</div></div>
              <div><div className="mono" style={{ opacity:0.5, marginBottom:6 }}>Mise en scène</div><div>{s.mes}</div></div>
              <div style={{ gridColumn:"1 / -1" }}><div className="mono" style={{ opacity:0.5, marginBottom:6 }}>Avec</div><div>{s.with}</div></div>
            </div>
            <div style={{ display:"flex", gap:12 }}>
              <button className="btn" onClick={() => setRoute("agenda")}>Voir les dates ({dates.length})</button>
              <button className="btn btn-ghost">Dossier de presse ↓</button>
            </div>
          </div>
        </div>
      </section>

      {dates.length > 0 && (
        <section className="section" style={{ background:"var(--paper-warm)" }}>
          <div className="section-head">
            <div className="section-num">№ — / Dates</div>
            <h2 className="section-title">En <span className="display-italic">tournée.</span></h2>
            <div className="section-meta">{dates.length} dates programmées</div>
          </div>
          {dates.map((d,i) => <AgendaRow key={i} d={d}/>)}
        </section>
      )}
    </>
  );
};

/* ======================= AGENDA CARD ======================= */
const TYPE_CONFIG = {
  spectacle: { label:"Spectacle", color:"var(--terra)" },
  atelier:   { label:"Atelier",   color:"var(--plum)" },
  résidence: { label:"Résidence", color:"var(--aubergine)" },
  événement: { label:"Évènement", color:"var(--amber-deep)" },
};

const STATUS_CONFIG = {
  available: { label:"Places disponibles", color:"var(--terra)" },
  few:       { label:"Dernières places",   color:"var(--amber-deep)" },
  sold:      { label:"Complet",            color:"var(--ink-soft)" },
  free:      { label:"Entrée libre",       color:"var(--plum)" },
};

const AgendaCard = ({ d, onClick }) => {
  const tc = TYPE_CONFIG[d.type] || TYPE_CONFIG.spectacle;
  const sc = STATUS_CONFIG[d.status] || STATUS_CONFIG.available;
  const spectacleData = d.spectacle ? SPECTACLES.find(s => s.id === d.spectacle) : null;

  return (
    <article
      onClick={onClick}
      style={{ cursor: onClick ? "pointer" : "default", display:"flex", flexDirection:"column" }}
      className={onClick ? "card card-fx" : ""}
    >
      {/* Visual header */}
      <div style={{
        position:"relative", aspectRatio:"3/2", overflow:"hidden",
        background: spectacleData ? spectacleData.color : (d.cardColor || "var(--paper-warm)"),
      }}>
        {spectacleData && (
          <div style={{ position:"absolute", inset:0 }}>
            <Poster bg={spectacleData.color} ink={spectacleData.textColor} title={spectacleData.title} subtitle={spectacleData.tag} num={spectacleData.num} variant={1}/>
          </div>
        )}
        {!spectacleData && (
          <div style={{
            position:"absolute", inset:0, display:"flex", alignItems:"center", justifyContent:"center", opacity:0.18,
          }}>
            <Motif size={180} color={d.cardTextColor || "var(--paper)"} berryColor={d.cardTextColor || "var(--paper)"} rotate={15} seed={2.5}/>
          </div>
        )}
        {/* Type badge (pastille) */}
        <div style={{
          position:"absolute", top:12, left:12,
          background: tc.color, color:"#fff",
          fontSize:10, fontWeight:700, letterSpacing:"0.08em",
          padding:"4px 10px", textTransform:"uppercase",
        }}>
          {tc.label}
        </div>
      </div>

      {/* Text content — vraiment minimal */}
      <div style={{ padding:"14px 0 8px", borderTop:"1px solid var(--rule)", marginTop:0 }}>
        <h4 className="display" style={{ fontSize:20, lineHeight:1.05, marginBottom:6 }}>{d.title}</h4>
        <div style={{ fontSize:12, color:"var(--ink-soft)", marginBottom:8, letterSpacing:"0.02em" }}>
          {d.day} {d.month} {d.year} · {d.venue}
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:6 }}>
          <span style={{ width:5, height:5, borderRadius:"50%", background:sc.color, flexShrink:0 }}/>
          <span style={{ fontSize:11, color:sc.color, fontWeight:500 }}>{sc.label}</span>
        </div>
      </div>
    </article>
  );
};

/* ======================= AGENDA ======================= */
const AGENDA_FILTERS = [
  { id:"tout",      label:"Tout" },
  { id:"spectacle", label:"Spectacle" },
  { id:"atelier",   label:"Atelier" },
  { id:"résidence", label:"Résidence" },
  { id:"événement", label:"Évènement" },
];

const Agenda = ({ setRoute, setSpectacle }) => {
  const [filter, setFilter] = useState("tout");
  const [month, setMonth] = useState("Tous");

  const months = useMemo(() => {
    const seen = new Set();
    const result = [];
    AGENDA.forEach(d => {
      const key = d.month + " " + d.year;
      if (!seen.has(key)) { seen.add(key); result.push({ key, label: d.month + " " + d.year }); }
    });
    return result;
  }, []);

  const list = useMemo(() => {
    let result = filter === "tout" ? AGENDA : AGENDA.filter(d => d.type === filter);
    if (month !== "Tous") result = result.filter(d => d.month + " " + d.year === month);
    return result;
  }, [filter, month]);

  return (
    <section className="section" style={{ position:"relative", overflow:"hidden" }}>
      <div ref={useParallax(0.18, 110)} className="motif-bg" style={{ right:-80, top:80, opacity:0.25 }}>
        <Motif size={380} color="var(--plum)" berryColor="var(--terra)" rotate={-20} seed={2.7}/>
      </div>
      <Reveal variant="up" className="section-head">
        <div className="section-num">№ 02 / Saison</div>
        <h2 className="section-title">Agenda<br/><span className="display-italic">2025 — 2026.</span></h2>
        <div className="section-meta">{AGENDA.length} rendez-vous · spectacles, ateliers, résidences & événements.</div>
      </Reveal>

      {/* Filtres : type à gauche, mois à droite */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:16, marginBottom:48, flexWrap:"wrap" }}>
        <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
          {AGENDA_FILTERS.map(f => (
            <button key={f.id}
              className={`tweak-pill ${filter === f.id ? "active" : ""}`}
              onClick={() => setFilter(f.id)}
              style={ filter === f.id && f.id !== "tout" ? { background: TYPE_CONFIG[f.id]?.color, color:"#fff", borderColor: TYPE_CONFIG[f.id]?.color } : {} }
            >
              {f.label}
              {f.id !== "tout" && (
                <span style={{ marginLeft:6, fontSize:10, opacity:0.7 }}>
                  {AGENDA.filter(d => d.type === f.id).length}
                </span>
              )}
            </button>
          ))}
        </div>
        <div style={{ display:"flex", gap:8, alignItems:"center", flexWrap:"wrap" }}>
          <span style={{ fontSize:11, fontFamily:"var(--ff-mono)", letterSpacing:"0.1em", textTransform:"uppercase", opacity:0.45 }}>Mois</span>
          <button className={`tweak-pill ${month === "Tous" ? "active" : ""}`} onClick={() => setMonth("Tous")}>Tous</button>
          {months.map(m => (
            <button key={m.key}
              className={`tweak-pill ${month === m.key ? "active" : ""}`}
              onClick={() => setMonth(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grille 3 colonnes */}
      {list.length === 0 ? (
        <p style={{ color:"var(--ink-soft)", fontStyle:"italic" }}>Aucun rendez-vous dans cette catégorie pour le moment.</p>
      ) : (
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:"var(--grid-gap)" }}>
          {list.map((d, i) => (
            <Reveal key={i} variant="up" delay={(i % 3) * 70}>
              <AgendaCard
                d={d}
                onClick={d.spectacle ? () => { setSpectacle(d.spectacle); setRoute("spectacles/detail"); } : null}
              />
            </Reveal>
          ))}
        </div>
      )}
    </section>
  );
};

/* ======================= ATELIERS ======================= */
const AUDIENCE_FILTERS = [
  { id:"",         label:"Tous" },
  { id:"enfants",  label:"Enfants" },
  { id:"ados",     label:"Ados" },
  { id:"adultes",  label:"Adultes" },
  { id:"ecole",    label:"Milieu scolaire" },
  { id:"seniors",  label:"Personnes âgées" },
  { id:"quartier", label:"Quartier" },
  { id:"insertion",label:"Insertion sociale" },
];

const Ateliers = ({ audience = "" }) => {
  const [filter, setFilter] = useState(audience);
  const [selected, setSelected] = useState(null);

  useEffect(() => { setFilter(audience); setSelected(null); }, [audience]);

  const list = filter ? ATELIERS.filter(a => a.audience === filter) : ATELIERS;

  return (
    <>
      <section className="section" style={{ position:"relative", overflow:"hidden" }}>
        <div ref={useParallax(0.2, 120)} className="motif-bg" style={{ left:-60, top:0, opacity:0.3 }}>
          <Motif size={380} color="var(--amber-deep)" berryColor="var(--terra)" rotate={-30} seed={3}/>
        </div>
        <Reveal variant="up" className="section-head">
          <div className="section-num">№ 03 / Pratiques</div>
          <h2 className="section-title">Ateliers<br/><span className="display-italic">& pratiques.</span></h2>
          <div className="section-meta">{ATELIERS.length} ateliers réguliers, du jeu enfant à la médiation en milieu social. Inscriptions ouvertes pour la saison 2026.</div>
        </Reveal>

        {/* Filtre par public */}
        <div style={{ display:"flex", gap:8, marginBottom:40, flexWrap:"wrap" }}>
          {AUDIENCE_FILTERS.map(f => (
            <button key={f.id}
              className={`tweak-pill ${filter === f.id ? "active" : ""}`}
              onClick={() => { setFilter(f.id); setSelected(null); }}
            >
              {f.label}
              {f.id !== "" && (
                <span style={{ marginLeft:6, fontSize:10, opacity:0.65 }}>
                  {ATELIERS.filter(a => a.audience === f.id).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {list.length === 0 ? (
          <p style={{ color:"var(--ink-soft)", fontStyle:"italic" }}>Aucun atelier dans cette catégorie pour le moment.</p>
        ) : (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:"var(--grid-gap)" }}>
            {list.map((a,i) => (
              <Reveal key={a.num} variant="scale" delay={(i % 3) * 80} style={{ display:"flex" }}>
              <article className="noise" style={{ flex:1, background:a.color, color:a.textColor, padding:32, position:"relative", overflow:"hidden", minHeight:340, cursor:"pointer", display:"flex", flexDirection:"column", justifyContent:"space-between" }}
                onClick={() => setSelected(selected === a.num ? null : a.num)}
              >
                <div style={{ position:"absolute", right:-30, bottom:-40, opacity:0.18 }}>
                  <Motif size={220} color={a.textColor} berryColor={a.textColor} rotate={20} seed={parseInt(a.num.slice(1))}/>
                </div>
                <div style={{ position:"relative", zIndex:2 }}>
                  <div className="mono" style={{ marginBottom:24 }}>№ {a.num}</div>
                  <h3 className="display" style={{ fontSize:36, lineHeight:1, marginBottom:14 }}>{a.title}</h3>
                  <div style={{ fontSize:14, opacity:0.85, marginBottom:18 }}>{a.who}</div>
                  <p style={{ fontSize:14, lineHeight:1.5, opacity:0.9, textWrap:"pretty" }}>{a.desc}</p>
                </div>
                <div style={{ position:"relative", zIndex:2, paddingTop:24, marginTop:24, borderTop:`1px solid ${a.textColor}`, opacity:0.95 }}>
                  <div className="mono" style={{ marginBottom:6 }}>{a.when}</div>
                  <div className="mono" style={{ marginBottom:6, opacity:0.7 }}>{a.where}</div>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"baseline", marginTop:12 }}>
                    <strong style={{ fontFamily:"var(--ff-display)", fontStyle:"italic", fontSize:22 }}>{a.price}</strong>
                    <span>{selected === a.num ? "S'inscrire ↓" : "→"}</span>
                  </div>
                  {selected === a.num && (
                    <form style={{ marginTop:16, display:"grid", gap:8 }} onClick={e => e.stopPropagation()} onSubmit={e => { e.preventDefault(); alert("Demande envoyée — nous revenons vers vous sous 48h."); setSelected(null); }}>
                      <input className="input" placeholder="Nom" style={{ borderColor:a.textColor, color:a.textColor }} required/>
                      <input className="input" placeholder="Email" type="email" style={{ borderColor:a.textColor, color:a.textColor }} required/>
                      <button className="btn btn-amber" type="submit" style={{ width:"100%", justifyContent:"center" }}>Envoyer la demande</button>
                    </form>
                  )}
                </div>
              </article>
              </Reveal>
            ))}
          </div>
        )}
      </section>
    </>
  );
};

/* ======================= ÉQUIPE ======================= */
const Equipe = () => {
  const [active, setActive] = useState(0);
  return (
    <section className="section" style={{ position:"relative" }}>
      <div className="section-head">
        <div className="section-num">№ 04 / Équipe</div>
        <h2 className="section-title">Huit <span className="display-italic">artistes,</span><br/>une compagnie.</h2>
        <div className="section-meta">L'équipe permanente et associée de la compagnie. Survolez ou cliquez pour lire la biographie.</div>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1.4fr", gap:64, alignItems:"start" }}>
        <div>
          {EQUIPE.map((p,i) => (
            <div key={p.name}
              onClick={() => setActive(i)}
              style={{
                padding:"24px 0", borderTop:"1px solid var(--rule)", cursor:"pointer",
                opacity: active === i ? 1 : 0.6,
                transition:"opacity 0.2s, transform 0.2s",
                transform: active === i ? "translateX(8px)" : "translateX(0)"
              }}
            >
              <h3 className="display" style={{ fontSize: active === i ? 44 : 32, lineHeight:1, transition:"font-size 0.2s" }}>
                {p.name.split(" ").map((w,j) => j === 1 ? <span key={j} className="display-italic">{w} </span> : <span key={j}>{w} </span>)}
              </h3>
              <div className="mono" style={{ marginTop:8, color:"var(--terra)" }}>{p.role}</div>
            </div>
          ))}
        </div>
        <div style={{ position:"sticky", top:100 }}>
          <div className="noise" style={{ background:"var(--paper-warm)", aspectRatio:"4/5", position:"relative", overflow:"hidden", marginBottom:24 }}>
            <Poster bg={["#B84A2E","#9B7AA8","#E8B542","#3A1B2E","#8E3620","#C89420","#9B7AA8","#3A1B2E"][active] || "#B84A2E"} ink="#F4E8D5" title={EQUIPE[active].name.split(" ")[0]} subtitle={EQUIPE[active].role.split(",")[0]} num={String(active+1).padStart(2,"0")} variant={active % 4} motifOpacity={0.5}/>
          </div>
          <p style={{ fontSize:18, lineHeight:1.6, color:"var(--ink-soft)", textWrap:"pretty" }}>{EQUIPE[active].bio}</p>
        </div>
      </div>
    </section>
  );
};

/* ======================= PARTENAIRES ======================= */
const Partenaires = () => {
  const groups = useMemo(() => {
    const g = {};
    PARTENAIRES.forEach(p => { if (!g[p.type]) g[p.type] = []; g[p.type].push(p); });
    return g;
  }, []);
  return (
    <section className="section" style={{ position:"relative", overflow:"hidden" }}>
      <div ref={useParallax(0.16, 100)} className="motif-bg" style={{ right:-50, bottom:-100, opacity:0.3 }}>
        <Motif size={420} color="var(--terra)" berryColor="var(--amber)" rotate={180} seed={3.5}/>
      </div>
      <div className="section-head">
        <div className="section-num">№ 05 / Soutiens</div>
        <h2 className="section-title">Partenaires<br/><span className="display-italic">& soutiens.</span></h2>
        <div className="section-meta">La compagnie est conventionnée par la DRAC PACA et soutenue par les collectivités territoriales du sud-est.</div>
      </div>
      {Object.entries(groups).map(([type, list]) => (
        <div key={type} style={{ marginBottom:48 }}>
          <div className="eyebrow" style={{ marginBottom:24 }}>{type}</div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:0, borderTop:"1px solid var(--rule-strong)" }}>
            {list.map(p => (
              <div key={p.name} style={{
                padding:"32px 24px", borderRight:"1px solid var(--rule)", borderBottom:"1px solid var(--rule)",
                minHeight:140, display:"flex", alignItems:"center"
              }}>
                <div className="display" style={{ fontSize:24, lineHeight:1.05 }}>{p.name}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
};

/* ======================= CONTACT ======================= */
const Contact = () => {
  const [sent, setSent] = useState(false);
  return (
    <>
      <section className="section" style={{ position:"relative", overflow:"hidden" }}>
        <div ref={useParallax(0.18, 110)} className="motif-bg" style={{ left:-100, top:-50, opacity:0.35 }}>
          <Motif size={460} color="var(--terra)" berryColor="var(--amber)" rotate={-15} seed={4}/>
        </div>
        <div className="section-head">
          <div className="section-num">№ 06 / Nous joindre</div>
          <h2 className="section-title">Écrivez-<span className="display-italic">nous,</span><br/>passez nous voir.</h2>
          <div className="section-meta">Atelier ouvert le mercredi après-midi. Pour la billetterie scolaire ou groupes, écrivez à Nadia.</div>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1.3fr", gap:80 }}>
          <div>
            <div style={{ marginBottom:32 }}>
              <div className="mono" style={{ marginBottom:8, opacity:0.5 }}>Adresse</div>
              <div style={{ fontFamily:"var(--ff-display)", fontStyle:"italic", fontSize:28, lineHeight:1.2 }}>
                Atelier Rouletabille<br/>
                14 rue Pierre Sémard<br/>
                83000 Toulon
              </div>
            </div>
            <div style={{ marginBottom:32 }}>
              <div className="mono" style={{ marginBottom:8, opacity:0.5 }}>Diffusion · Production</div>
              <div style={{ fontSize:18 }}>Nadia Pereira</div>
              <div style={{ fontSize:18, color:"var(--terra)" }}>nadia@cie-rouletabille.fr</div>
              <div className="mono" style={{ marginTop:4 }}>+33 (0)4 94 00 00 00</div>
            </div>
            <div>
              <div className="mono" style={{ marginBottom:8, opacity:0.5 }}>Action culturelle · Ateliers</div>
              <div style={{ fontSize:18 }}>Mira Solano</div>
              <div style={{ fontSize:18, color:"var(--terra)" }}>ateliers@cie-rouletabille.fr</div>
            </div>
          </div>
          <div>
            {sent ? (
              <div style={{ padding:48, background:"var(--amber)", color:"var(--ink)" }}>
                <h3 className="display" style={{ fontSize:48, marginBottom:12 }}>Merci.</h3>
                <p>Votre message est arrivé. Nous revenons vers vous sous 48h.</p>
              </div>
            ) : (
              <form onSubmit={e => { e.preventDefault(); setSent(true); }} style={{ display:"grid", gap:16 }}>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
                  <input className="input" placeholder="Nom" required/>
                  <input className="input" placeholder="Email" type="email" required/>
                </div>
                <select className="input" required>
                  <option>Objet du message</option>
                  <option>Information spectacle</option>
                  <option>Inscription atelier</option>
                  <option>Diffusion / Programmation</option>
                  <option>Presse</option>
                  <option>Autre</option>
                </select>
                <textarea className="textarea" rows={8} placeholder="Votre message" required/>
                <button className="btn" type="submit" style={{ justifySelf:"start" }}>Envoyer →</button>
              </form>
            )}
          </div>
        </div>
      </section>
      <Newsletter/>
    </>
  );
};

/* ======================= NEWSLETTER ======================= */
const Newsletter = () => {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  return (
    <section className="section" style={{ background:"var(--amber)", color:"var(--ink)", paddingTop:64, paddingBottom:64 }}>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:48, alignItems:"center" }}>
        <h2 className="display" style={{ fontSize:"clamp(40px, 5vw, 72px)" }}>
          La saison<br/><span className="display-italic">par lettre.</span>
        </h2>
        <div>
          <p style={{ fontSize:18, marginBottom:24, maxWidth:480 }}>Une lettre par mois. Les nouvelles dates, les coulisses des créations, les ateliers à venir. Pas de spam, promis.</p>
          {done ? (
            <div className="display-italic" style={{ fontSize:32 }}>Inscrit. À très vite ✦</div>
          ) : (
            <form onSubmit={e => { e.preventDefault(); setDone(true); }} style={{ display:"flex", gap:8, maxWidth:520 }}>
              <input className="input" type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="votre@email.fr" style={{ background:"transparent", borderColor:"var(--ink)", flex:1 }}/>
              <button className="btn" type="submit">S'inscrire →</button>
            </form>
          )}
        </div>
      </div>
    </section>
  );
};

/* ======================= FOOTER ======================= */
const Footer = ({ setRoute }) => (
  <footer className="footer">
    <div style={{ display:"grid", gridTemplateColumns:"1.4fr 1fr 1fr 1fr", gap:48, marginBottom:48 }}>
      <div>
        <div className="nav-logo" style={{ color:"var(--paper)", fontSize:32, marginBottom:16 }}>
          <MotifMark size={36} color="var(--amber)"/>
          <span>Cie Rouletabille</span>
        </div>
        <p style={{ opacity:0.7, fontSize:14, lineHeight:1.6, maxWidth:340 }}>Compagnie de théâtre fondée en 2014 à Toulon. Conventionnée DRAC PACA.</p>
      </div>
      <div>
        <div className="mono" style={{ marginBottom:14, opacity:0.5 }}>Découvrir</div>
        <ul style={{ listStyle:"none", display:"flex", flexDirection:"column", gap:8, fontSize:14 }}>
          <li onClick={() => setRoute("spectacles")} style={{ cursor:"pointer" }}>Spectacles</li>
          <li onClick={() => setRoute("agenda")} style={{ cursor:"pointer" }}>Agenda</li>
          <li onClick={() => setRoute("ateliers")} style={{ cursor:"pointer" }}>Ateliers</li>
          <li onClick={() => setRoute("equipe")} style={{ cursor:"pointer" }}>Équipe</li>
        </ul>
      </div>
      <div>
        <div className="mono" style={{ marginBottom:14, opacity:0.5 }}>Pratique</div>
        <ul style={{ listStyle:"none", display:"flex", flexDirection:"column", gap:8, fontSize:14 }}>
          <li onClick={() => setRoute("contact")} style={{ cursor:"pointer" }}>Contact</li>
          <li>Venir à l'atelier</li>
          <li>Dossiers de presse</li>
          <li>Mentions légales</li>
        </ul>
      </div>
      <div>
        <div className="mono" style={{ marginBottom:14, opacity:0.5 }}>Suivre</div>
        <ul style={{ listStyle:"none", display:"flex", flexDirection:"column", gap:8, fontSize:14 }}>
          <li>Instagram</li>
          <li>Facebook</li>
          <li>Vimeo</li>
          <li>Newsletter</li>
        </ul>
      </div>
    </div>
    <div style={{ borderTop:"1px solid color-mix(in oklab, var(--paper) 20%, transparent)", paddingTop:24, display:"flex", justifyContent:"space-between", fontSize:12, opacity:0.6 }}>
      <span>© 2026 Cie Rouletabille — Tous droits réservés</span>
      <span>Saison 2025 — 2026</span>
    </div>
  </footer>
);

export { Nav, Home, Spectacles, FicheSpectacle, Agenda, Ateliers, Equipe, Partenaires, Contact, Footer };
