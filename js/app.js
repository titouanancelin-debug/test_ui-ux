
const { useState, useEffect } = React;

const TWEAK_DEFAULS = /*EDITMODE-BEGIN*/{
  "palette": "default",
  "density": "airy",
  "anim": "normal",
  "dark": false
}/*EDITMODE-END*/;

function App() {
  // Persistent route
  const [route, setRouteRaw] = useState(() => localStorage.getItem("rt-route") || "home");
  const [spectacle, setSpectacle] = useState(() => localStorage.getItem("rt-spectacle") || "gens-de-peu");
  const setRoute = (r) => { setRouteRaw(r); localStorage.setItem("rt-route", r); window.scrollTo({ top:0, behavior:"smooth" }); };
  useEffect(() => { localStorage.setItem("rt-spectacle", spectacle); }, [spectacle]);

  // Effets d'ambiance : rideau d'intro + barre de progression (une fois)
  useEffect(() => { if (window.initFX) window.initFX(); }, []);

  // Tweaks
  const [tweaks, setTweaks] = useState(TWEAK_DEFAULS);
  const [tweaksOpen, setTweaksOpen] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      if (e.data?.type === "__activate_edit_mode") setTweaksOpen(true);
      if (e.data?.type === "__deactivate_edit_mode") setTweaksOpen(false);
    };
    window.addEventListener("message", handler);
    window.parent.postMessage({type: "__edit_mode_available"}, "*");
    return () => window.removeEventListener("message", handler);
  }, []);

  const updateTweak = (k, v) => {
    const next = { ...tweaks, [k]: v };
    setTweaks(next);
    window.parent.postMessage({type: "__edit_mode_set_keys", edits: { [k]: v }}, "*");
  };

  // Apply classes
  useEffect(() => {
    const root = document.body;
    root.className = "app-root";
    if (tweaks.palette === "sobre") root.classList.add("palette-sobre");
    if (tweaks.palette === "nocturne" || tweaks.dark) root.classList.add("palette-nocturne");
    if (tweaks.density === "compact") root.classList.add("density-compact");
    if (tweaks.density === "airy") root.classList.add("density-airy");
    if (tweaks.anim === "off") root.classList.add("anim-off");
    if (tweaks.anim === "low") root.classList.add("anim-low");
  }, [tweaks]);

  let screen;
  if (route === "home") screen = <Home setRoute={setRoute} setSpectacle={setSpectacle}/>;
  else if (route === "spectacles") screen = <Spectacles setRoute={setRoute} setSpectacle={setSpectacle}/>;
  else if (route === "spectacles/detail") screen = <FicheSpectacle id={spectacle} setRoute={setRoute} setSpectacle={setSpectacle}/>;
  else if (route === "agenda") screen = <Agenda setRoute={setRoute} setSpectacle={setSpectacle}/>;
  else if (route === "ateliers") screen = <Ateliers/>;
  else if (route === "equipe") screen = <Equipe/>;
  else if (route === "partenaires") screen = <Partenaires/>;
  else if (route === "contact") screen = <Contact/>;
  else screen = <Home setRoute={setRoute} setSpectacle={setSpectacle}/>;

  return (
    <div className="app" data-screen-label={route}>
      <Nav route={route} setRoute={setRoute}/>
      {screen}
      <Footer setRoute={setRoute}/>
      {tweaksOpen && (
        <div className="tweaks-panel">
          <h4>Tweaks</h4>
          <div className="tweaks-row">
            <label>Palette</label>
            <div className="tweaks-pills">
              {["default","sobre","nocturne"].map(p => (
                <button key={p} className={`tweak-pill ${tweaks.palette === p ? "active" : ""}`} onClick={() => updateTweak("palette", p)}>{p === "default" ? "terracotta" : p}</button>
              ))}
            </div>
          </div>
          <div className="tweaks-row">
            <label>Densité</label>
            <div className="tweaks-pills">
              {["compact","default","airy"].map(p => (
                <button key={p} className={`tweak-pill ${tweaks.density === p ? "active" : ""}`} onClick={() => updateTweak("density", p)}>{p === "default" ? "normal" : p}</button>
              ))}
            </div>
          </div>
          <div className="tweaks-row">
            <label>Animations botaniques</label>
            <div className="tweaks-pills">
              {["off","low","normal"].map(p => (
                <button key={p} className={`tweak-pill ${tweaks.anim === p ? "active" : ""}`} onClick={() => updateTweak("anim", p)}>{p}</button>
              ))}
            </div>
          </div>
          <div className="tweaks-row">
            <label>Mode</label>
            <div className="tweaks-pills">
              <button className={`tweak-pill ${!tweaks.dark ? "active" : ""}`} onClick={() => updateTweak("dark", false)}>clair</button>
              <button className={`tweak-pill ${tweaks.dark ? "active" : ""}`} onClick={() => updateTweak("dark", true)}>sombre</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
