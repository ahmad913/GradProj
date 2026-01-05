import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import axios from "axios";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
const API_URL = import.meta.env.VITE_API_URL;

export default function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const drawRef = useRef(null);

  const [p, setP] = useState(5);
  const [lampTypes] = useState([
    { id: "A", radius: 80, cost: 100 },
    { id: "B", radius: 150, cost: 180 }
  ]);

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

    return () => map.remove();
  }, []);

  const optimize = async () => {
    const data = drawRef.current.getAll();
    if (!data.features.length) {
      alert("Draw a polygon first");
      return;
    }

    const polygon = data.features[0].geometry.coordinates[0];

    const res = await axios.post(`${API_URL}/api/optimize`, {
      polygon,
      p,
      lamp_types: lampTypes
    });

    res.data.lamps.forEach(l => {
      new mapboxgl.Marker()
        .setLngLat([l.lon, l.lat])
        .addTo(mapRef.current);
    });
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ width: 300, padding: 10 }}>
        <h3>Lighting Optimization</h3>

        <label>Lamps (p)</label>
        <input
          type="number"
          value={p}
          onChange={e => setP(Number(e.target.value))}
          style={{ width: "100%" }}
        />

        <button onClick={optimize} style={{ marginTop: 10 }}>
          Optimize
        </button>
      </div>

      <div ref={mapContainer} style={{ flex: 1 }} />
    </div>
  );
}
