/* Motif signature : la PHYSALIS (lanterne) — repris du design original Rouletabille */
/* Lanterne en fil de fer + baie orange à l'intérieur, suspendue à une tige. */

/* Une lanterne unique, dessinée à l'origine (0,0) = point d'attache de la tige,
   s'ouvrant vers le haut jusqu'à y=-132, baie au centre. */
const Lantern = ({ x = 0, y = 0, scale = 1, color = "#F5C842", berry = "#E8571A", delay = 0, dur = 4, veins = 4, opacity = 1 }) => {
  const veinPaths = [
    "M-42,-30 C-15,-38,15,-38,42,-30",
    "M-60,-56 C-24,-64,24,-64,60,-56",
    "M-64,-82 C-24,-90,24,-90,64,-82",
    "M-46,-106 C-18,-113,18,-113,46,-106",
  ];
  return (
    <g transform={`translate(${x},${y}) scale(${scale})`} opacity={opacity}>
      {/* inner group pivots at y=0 (attachment point) — transform-box:fill-box + transform-origin:center bottom */}
      <g className="anim-wind" style={{ animationDelay: `${delay}s`, "--wind-dur": `${(dur * 0.88).toFixed(1)}s` }}>
        {/* ribs */}
        <path d="M0,0 C-52,-18,-75,-60,-50,-100 C-28,-122,0,-132,0,-132" stroke={color} strokeWidth="1.9" fill="none" opacity=".9" vectorEffect="non-scaling-stroke"/>
        <path d="M0,0 C52,-18,75,-60,50,-100 C28,-122,0,-132,0,-132" stroke={color} strokeWidth="1.9" fill="none" opacity=".9" vectorEffect="non-scaling-stroke"/>
        <path d="M0,0 C-26,-14,-44,-52,-28,-92 C-14,-118,0,-132,0,-132" stroke={color} strokeWidth="1.4" fill="none" opacity=".74" vectorEffect="non-scaling-stroke"/>
        <path d="M0,0 C26,-14,44,-52,28,-92 C14,-118,0,-132,0,-132" stroke={color} strokeWidth="1.4" fill="none" opacity=".74" vectorEffect="non-scaling-stroke"/>
        <path d="M0,0 C1,-32,0,-82,0,-132" stroke={color} strokeWidth="1.1" fill="none" opacity=".58" vectorEffect="non-scaling-stroke"/>
        {/* cage rings (veins) */}
        {veinPaths.slice(0, veins).map((d, i) => (
          <path key={i} d={d} stroke={color} strokeWidth={0.95 - i*0.08} fill="none" opacity={0.55 - i*0.06} className="anim-vein" style={{ animationDelay: `${i*0.9}s` }} vectorEffect="non-scaling-stroke"/>
        ))}
        {/* berry */}
        <ellipse cx="0" cy="-66" rx="25" ry="27" fill={berry} opacity=".92" className="anim-berry" style={{ animationDelay: `${delay}s`, animationDuration: `${dur}s` }}/>
        <ellipse cx="-8" cy="-74" rx="7" ry="8" fill="rgba(255,255,255,0.25)"/>
        {/* top bud */}
        <circle cx="0" cy="-132" r="3.2" fill={color} opacity=".6"/>
      </g>
    </g>
  );
};

/* Motif décoratif : une branche de physalis (tige + 3 lanternes), réutilisable partout.
   Mêmes props que l'ancien Motif pour compatibilité (size, color, berryColor, rotate, seed, anim, style). */
const Motif = ({ size = 200, color = "#F5C842", berryColor = "#E8571A", rotate = 0, anim = true, style = {}, seed = 1 }) => {
  const a = seed;
  return (
    <svg
      width={size} height={size}
      viewBox="0 0 280 300"
      style={{ transform: `rotate(${rotate}deg)`, overflow: "visible", ...style }}
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <g className={anim ? "" : "anim-off"}>
        {/* main stem */}
        <path d="M150,300 C148,260 145,235 142,205" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" opacity=".82"/>
        {/* left branch */}
        <path d="M143,225 C118,196 86,150 60,108" stroke={color} strokeWidth="2.2" fill="none" strokeLinecap="round" opacity=".66"/>
        {/* right branch */}
        <path d="M145,212 C168,184 204,140 230,96" stroke={color} strokeWidth="2.2" fill="none" strokeLinecap="round" opacity=".66"/>
        {/* tendrils */}
        <path d="M142,250 C130,244 118,242 108,246" stroke={color} strokeWidth="1" fill="none" strokeLinecap="round" opacity=".4"/>
        <path d="M146,240 C158,234 172,232 182,236" stroke={color} strokeWidth="1" fill="none" strokeLinecap="round" opacity=".4"/>

        {/* lanterns */}
        <Lantern x={142} y={205} scale={0.72} color={color} berry={berryColor} delay={0.2*a} dur={4.2} veins={4}/>
        <Lantern x={60}  y={108} scale={0.5}  color={color} berry={berryColor} delay={1.3*a} dur={5} veins={3} opacity={0.92}/>
        <Lantern x={230} y={96}  scale={0.46} color={color} berry={berryColor} delay={2.1*a} dur={4.6} veins={3} opacity={0.88}/>

        {/* buds */}
        <circle cx="108" cy="246" r="2.4" fill={color} opacity=".4"/>
        <circle cx="182" cy="236" r="2.4" fill={color} opacity=".4"/>
      </g>
    </svg>
  );
};

/* Grande composition pour le hero — système de tiges + 5 lanternes (façon original) */
const MotifHero = ({ color = "#F5C842", berryColor = "#E8571A", anim = true, style = {} }) => (
  <svg viewBox="0 0 600 620" preserveAspectRatio="xMidYMid slice" style={style} xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <g className={anim ? "" : "anim-off"}>
      {/* stem system */}
      <path d="M295,630 C293,600 291,582 290,545" stroke={color} strokeWidth="3.2" fill="none" strokeLinecap="round" opacity=".82"/>
      <path d="M290,558 C264,532 222,472 162,378" stroke={color} strokeWidth="2.4" fill="none" strokeLinecap="round" opacity=".72"/>
      <path d="M293,550 C322,522 378,462 456,362" stroke={color} strokeWidth="2.4" fill="none" strokeLinecap="round" opacity=".72"/>
      <path d="M162,378 C138,348 108,292 80,218" stroke={color} strokeWidth="1.8" fill="none" strokeLinecap="round" opacity=".58"/>
      <path d="M456,362 C474,332 502,278 528,210" stroke={color} strokeWidth="1.8" fill="none" strokeLinecap="round" opacity=".58"/>
      <path d="M178,445 C158,432 134,424 108,420" stroke={color} strokeWidth="1.3" fill="none" strokeLinecap="round" opacity=".4"/>
      <path d="M418,435 C440,422 462,415 482,412" stroke={color} strokeWidth="1.3" fill="none" strokeLinecap="round" opacity=".4"/>

      <Lantern x={290} y={545} scale={1.05} color={color} berry={berryColor} delay={0} dur={4} veins={4}/>
      <Lantern x={162} y={378} scale={0.68} color={color} berry={berryColor} delay={1.5} dur={5} veins={4} opacity={0.92}/>
      <Lantern x={456} y={362} scale={0.64} color={color} berry={berryColor} delay={0.7} dur={4.5} veins={4} opacity={0.88}/>
      <Lantern x={80}  y={218} scale={0.44} color={color} berry={berryColor} delay={2.2} dur={6} veins={3} opacity={0.82}/>
      <Lantern x={528} y={210} scale={0.47} color={color} berry={berryColor} delay={0.3} dur={4.5} veins={3} opacity={0.8}/>

      {/* scattered buds */}
      <circle cx="172" cy="305" r="3.8" fill={color} opacity=".35"/>
      <circle cx="464" cy="285" r="3.5" fill={color} opacity=".32"/>
      <circle cx="92" cy="148" r="3" fill={color} opacity=".3"/>
      <circle cx="536" cy="142" r="2.5" fill={color} opacity=".28"/>
      <circle cx="45" cy="380" r="2.5" fill={color} opacity=".28"/>
      <circle cx="560" cy="480" r="2" fill={color} opacity=".25"/>
    </g>
  </svg>
);

/* Logo : une petite lanterne dans un cercle */
const MotifMark = ({ size = 28, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 40 44" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <g transform="translate(20,40) scale(0.26)">
      <path d="M0,0 C-52,-18,-75,-60,-50,-100 C-28,-122,0,-132,0,-132" stroke={color} strokeWidth="3" fill="none" vectorEffect="non-scaling-stroke"/>
      <path d="M0,0 C52,-18,75,-60,50,-100 C28,-122,0,-132,0,-132" stroke={color} strokeWidth="3" fill="none" vectorEffect="non-scaling-stroke"/>
      <path d="M0,0 C1,-32,0,-82,0,-132" stroke={color} strokeWidth="2" fill="none" vectorEffect="non-scaling-stroke"/>
      <path d="M-42,-30 C-15,-38,15,-38,42,-30" stroke={color} strokeWidth="2.2" fill="none" vectorEffect="non-scaling-stroke"/>
      <path d="M-60,-56 C-24,-64,24,-64,60,-56" stroke={color} strokeWidth="2" fill="none" vectorEffect="non-scaling-stroke"/>
      <ellipse cx="0" cy="-66" rx="22" ry="24" fill={color}/>
    </g>
  </svg>
);

/* Poster placeholder — sérigraphie avec lanterne physalis */
const Poster = ({ bg = "#B84A2E", ink = "#F4E8D5", title = "", subtitle = "", num = "01", variant = 0, motifOpacity = 0.45 }) => {
  // compositions de lanternes
  const comps = [
    // 0 — une grande lanterne centrée
    <g key="0" transform="translate(200,360) scale(1.5)" opacity={motifOpacity}>
      <Lantern color={ink} berry={ink} dur={5} veins={4}/>
    </g>,
    // 1 — branche montante de deux lanternes
    <g key="1" opacity={motifOpacity}>
      <path d="M120,420 C110,360 150,300 220,250" stroke={ink} strokeWidth="2" fill="none" strokeLinecap="round"/>
      <g transform="translate(120,420) scale(1.1)"><Lantern color={ink} berry={ink} dur={4.5} veins={4}/></g>
      <g transform="translate(220,250) scale(0.7)"><Lantern color={ink} berry={ink} delay={1.2} dur={5} veins={3}/></g>
    </g>,
    // 2 — trois lanternes suspendues
    <g key="2" opacity={motifOpacity}>
      <path d="M80,120 C80,180 80,200 80,220" stroke={ink} strokeWidth="1.6" fill="none" strokeLinecap="round"/>
      <path d="M200,90 C200,160 200,190 200,220" stroke={ink} strokeWidth="1.8" fill="none" strokeLinecap="round"/>
      <path d="M320,120 C320,180 320,210 320,250" stroke={ink} strokeWidth="1.6" fill="none" strokeLinecap="round"/>
      <g transform="translate(80,355) scale(0.7)"><Lantern color={ink} berry={ink} dur={4} veins={4}/></g>
      <g transform="translate(200,400) scale(0.95)"><Lantern color={ink} berry={ink} delay={1} dur={5} veins={4}/></g>
      <g transform="translate(320,390) scale(0.72)"><Lantern color={ink} berry={ink} delay={2} dur={4.5} veins={4}/></g>
    </g>,
    // 3 — diagonale
    <g key="3" opacity={motifOpacity}>
      <path d="M60,460 C160,400 280,300 380,200" stroke={ink} strokeWidth="1.8" fill="none" strokeLinecap="round"/>
      <g transform="translate(120,420) scale(0.85)"><Lantern color={ink} berry={ink} dur={4.2} veins={4}/></g>
      <g transform="translate(300,280) scale(0.6)"><Lantern color={ink} berry={ink} delay={1.5} dur={5} veins={3}/></g>
    </g>,
  ];
  return (
    <svg viewBox="0 0 400 500" preserveAspectRatio="xMidYMid slice" style={{ width:"100%", height:"100%", display:"block" }} xmlns="http://www.w3.org/2000/svg">
      <rect width="400" height="500" fill={bg}/>
      {/* hatch corner */}
      <g opacity="0.12">
        {[...Array(46)].map((_,i) => (
          <line key={i} x1="0" y1={i*14} x2={i*14} y2="0" stroke={ink} strokeWidth="0.5"/>
        ))}
      </g>
      {comps[variant % comps.length]}
      <text x="24" y="48" fill={ink} opacity="0.6" style={{ fontFamily:"var(--ff-mono)", fontSize:"12px", letterSpacing:"2px" }}>№ {num}</text>
      <text x="24" y="442" fill={ink} style={{ fontFamily:"var(--ff-display)", fontSize:"42px", fontStyle:"italic", letterSpacing:"-0.02em" }}>{title}</text>
      {subtitle && (
        <text x="24" y="470" fill={ink} opacity="0.8" style={{ fontFamily:"var(--ff-mono)", fontSize:"11px", letterSpacing:"2px", textTransform:"uppercase" }}>{subtitle}</text>
      )}
    </svg>
  );
};

export { Lantern, Motif, MotifHero, MotifMark, Poster };
