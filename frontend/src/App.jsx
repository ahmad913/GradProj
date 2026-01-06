import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import axios from "axios";
import * as turf from "@turf/turf";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
const API_URL = import.meta.env.VITE_API_URL;

export default function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const drawRef = useRef(null);
  const markersRef = useRef([]);
  const radiiSourceId = "lamp-radii";

  const [lampTypes, setLampTypes] = useState([
    { id: "A", name: "A", cost: 50, radius: 10, color: "#ff0000" },
    { id: "B", name: "B", cost: 90, radius: 15, color: "#0000ff" }
  ]);

  const [maxBudget, setMaxBudget] = useState("1000");
  const [lastResult, setLastResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v11",
      center: [31.2357, 30.0444],
      zoom: 14
    });

    mapRef.current = map;
    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: { polygon: true, trash: true }
    });
    map.addControl(draw);
    drawRef.current = draw;

    map.on("load", () => {
      map.addSource(radiiSourceId, { type: "geojson", data: turf.featureCollection([]) });
      map.addLayer({
        id: "lamp-radii-fill",
        type: "fill",
        source: radiiSourceId,
        paint: { "fill-color": ["get", "color"], "fill-opacity": 0.15 }
      });
      map.addLayer({
        id: "lamp-radii-outline",
        type: "line",
        source: radiiSourceId,
        paint: { "line-color": ["get", "color"], "line-width": 2 }
      });
    });

    return () => map.remove();
  }, []);

  const clearResults = () => {
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];
    if (mapRef.current.getSource(radiiSourceId)) {
      mapRef.current.getSource(radiiSourceId).setData(turf.featureCollection([]));
    }
    setLastResult(null);
  };

  const optimize = async () => {
    const data = drawRef.current.getAll();
    if (!data.features.length) return alert("Draw a polygon first");
    if (!maxBudget || Number(maxBudget) <= 0) return alert("Enter a positive budget");

    setLoading(true);
    clearResults();

    try {
      const res = await axios.post(`${API_URL}/api/optimize`, {
        options: { max_budget: Number(maxBudget) },
        lamp_types: lampTypes,
        polygon: data.features[0].geometry.coordinates[0]
      });

      const { lamps } = res.data;
      if (lamps && lamps.length > 0) {
        const features = [];
        lamps.forEach(l => {
          const marker = new mapboxgl.Marker({ color: l.color })
            .setLngLat([l.lon, l.lat])
            .addTo(mapRef.current);
          markersRef.current.push(marker);

          const circle = turf.circle([l.lon, l.lat], l.radius, { steps: 64, units: "meters" });
          circle.properties = { color: l.color };
          features.push(circle);
        });
        mapRef.current.getSource(radiiSourceId).setData(turf.featureCollection(features));
      }
      setLastResult(res.data);
    } catch (err) {
      alert(`Optimize failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateLampType = (index, key, value) => {
    setLampTypes(prev => {
      const next = [...prev];
      next[index] = { ...next[index], [key]: value };
      return next;
    });
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div id="left-panel" style={{ width: 320, padding: 14, overflow: "auto", background: "#fafafa", borderRight: "1px solid #eee" }}>
        <style>{`
          #left-panel input[type="number"], #left-panel input[type="text"] {
            padding: 8px !important; height: 36px !important; box-sizing: border-box !important;
            border-radius: 4px !important; border: 1px solid #ddd !important; width: 100%;
          }
          #left-panel button { min-height: 40px; padding: 8px 12px; white-space: nowrap; cursor: pointer; }
          #left-panel .btn-primary { background: #0b69ff; color: #fff; border: none; border-radius: 6px; width: 100%; font-weight: 700; }
          #left-panel .btn-primary:disabled { background: #ccc; cursor: not-allowed; }
          #left-panel .btn-secondary { background: #fff; border: 1px solid #ccc; border-radius: 6px; flex: 1; }
          #left-panel .btn-remove { background: #fff; border: 1px solid #e66; color: #a00; border-radius: 4px; padding: 6px 8px; min-height: 30px !important; }
          #left-panel .section { margin-bottom: 12px; }
          #left-panel .lamp-card { margin-bottom: 10px; padding: 8px; border: 1px solid #eee; border-radius: 6px; background: #fff; }
        `}</style>

        <h2 style={{ margin: "4px 0 8px", fontSize: 18 }}>Lamp Types</h2>
        <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>Add one or more lamp types with costs and coverage radius.</div>

        <section className="section">
          {lampTypes.map((t, i) => (
            <div key={t.id} className="lamp-card">
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                <input disabled={loading} value={t.name} onChange={e => updateLampType(i, "name", e.target.value)} />
                <div style={{ width: 24, height: 24, background: t.color, borderRadius: 4, border: "1px solid #999", flexShrink: 0 }} />
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 11, fontWeight: 700 }}>Cost ($)</label>
                  <input disabled={loading} type="number" value={t.cost} onChange={e => updateLampType(i, "cost", Number(e.target.value))} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 11, fontWeight: 700 }}>Radius (m)</label>
                  <input disabled={loading} type="number" value={t.radius} onChange={e => updateLampType(i, "radius", Number(e.target.value))} />
                </div>
              </div>
              <div style={{ textAlign: "right", marginTop: 8 }}>
                <button disabled={loading} className="btn-remove" onClick={() => setLampTypes(lampTypes.filter((_, idx) => idx !== i))}>Remove</button>
              </div>
            </div>
          ))}
          <button disabled={loading} className="btn-primary" onClick={() => setLampTypes([...lampTypes, { id: Date.now(), name: "New", cost: 100, radius: 80, color: `hsl(${Math.random() * 360}, 70%, 50%)` }])}>+ Add Lamp Type</button>
        </section>

        <section className="section">
          <h3 style={{ fontSize: 14, margin: "6px 0" }}>Constraints</h3>
          <label style={{ fontSize: 12, fontWeight: 700 }}>Max budget ($)</label>
          <input disabled={loading} type="number" value={maxBudget} onChange={e => setMaxBudget(e.target.value)} placeholder="e.g. 1000" />
        </section>

        <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
          <button disabled={loading} onClick={optimize} className="btn-primary" style={{ flex: 2 }}>
            {loading ? "Optimizing..." : "Optimize"}
          </button>
          <button disabled={loading} onClick={() => { drawRef.current.deleteAll(); clearResults(); }} className="btn-secondary">Clear</button>
        </div>

        {lastResult && (
          <div style={{ marginTop: 15, padding: 12, border: "2px solid #0b69ff", borderRadius: 8, background: "#fff" }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#0b69ff", marginBottom: 8, borderBottom: "1px solid #eee", paddingBottom: 4 }}>Model Results</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 12 }}>

              {/* Updated Coverage Display */}
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Coverage:</span>
                <strong>
                  {lastResult.points_covered} / {lastResult.total_points} pieces ({lastResult.coverage_pct}%)
                </strong>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Total Cost:</span> <strong>${lastResult.total_cost}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Lamps Placed:</span> <strong>{lastResult.lamps?.length || 0}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Status:</span> <span style={{ color: "green", fontWeight: 700 }}>{lastResult.status}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div ref={mapContainer} style={{ flex: 1 }} />
    </div>
  );
}