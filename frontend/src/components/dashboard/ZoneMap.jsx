import { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { motion } from 'framer-motion';
import { MapPinned } from 'lucide-react';

function zoneStyle(zone, worstKey, focusedKey) {
  const mos = zone.avg_mos;
  const crit = zone.critical_count ?? 0;
  const records = Math.max(zone.records ?? 0, 1);
  const critRate = crit / records;
  let fill = '#22c55e';
  if (critRate >= 0.35 || (mos != null && mos < 3.0)) fill = '#ef4444';
  else if (critRate >= 0.2 || (mos != null && mos < 3.8)) fill = '#f97316';
  else if (critRate >= 0.1 || (mos != null && mos < 4.2)) fill = '#eab308';

  const isWorst = worstKey != null && zone.zone === worstKey;
  const isFocused = focusedKey != null && zone.zone === focusedKey;
  const r = isFocused ? 22 : isWorst ? 18 : 12;
  const weight = isFocused ? 4 : isWorst ? 3 : 2;
  return { fill, r, weight };
}

function FitBounds({ zones }) {
  const map = useMap();
  useEffect(() => {
    if (!zones?.length) return;
    const bounds = L.latLngBounds(zones.map((z) => [z.lat, z.lon]));
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [48, 48], maxZoom: 5, animate: true });
    }
  }, [zones, map]);
  return null;
}

/** Fly / zoom when user picks a zone from an alert or marker. */
function FlyToZone({ zoneName, zones }) {
  const map = useMap();
  useEffect(() => {
    if (!zoneName || !zones?.length) return;
    const z = zones.find((x) => x.zone === zoneName);
    if (!z || typeof z.lat !== 'number' || typeof z.lon !== 'number') return;
    map.flyTo([z.lat, z.lon], Math.max(map.getZoom(), 6), { duration: 0.7 });
  }, [zoneName, zones, map]);
  return null;
}

export default function ZoneMap({ zones = [], focusedZone, onSelectZone, worstZoneKey }) {
  const validZones = useMemo(() => {
    const toNumber = (value) => {
      const n = Number(value);
      return Number.isFinite(n) ? n : null;
    };

    return (zones || [])
      .map((z) => {
        if (!z) return null;

        let lat = toNumber(z.lat ?? z.latitude);
        let lon = toNumber(z.lon ?? z.lng ?? z.longitude);

        if (lat == null || lon == null) return null;

        // Defensive normalization for APIs sending [lon, lat] instead of [lat, lon].
        if (Math.abs(lat) > 90 && Math.abs(lon) <= 90) {
          [lat, lon] = [lon, lat];
        }

        if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;

        return { ...z, lat, lon };
      })
      .filter(Boolean);
  }, [zones]);

  const center = useMemo(() => {
    if (!validZones.length) return [20, 0];
    const lat = validZones.reduce((s, z) => s + z.lat, 0) / validZones.length;
    const lon = validZones.reduce((s, z) => s + z.lon, 0) / validZones.length;
    return [lat, lon];
  }, [validZones]);

  if (!validZones.length) {
    return (
      <div className="h-[320px] rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center text-slate-400 text-sm">
        No geographic zones in this view. Try &ldquo;All&rdquo; or another BO.
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="relative h-[320px] rounded-2xl overflow-hidden border border-white/10 shadow-2xl"
    >
      <div className="absolute top-3 left-3 z-[500] flex items-center gap-2 rounded-xl bg-black/50 backdrop-blur-md px-3 py-2 text-xs text-white">
        <MapPinned className="w-4 h-4 text-cyan-400" />
        <span>Zone QoS — green good · red poor</span>
      </div>
      <MapContainer
        center={center}
        zoom={3}
        className="h-full w-full z-0"
        scrollWheelZoom
        attributionControl
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <FitBounds zones={validZones} />
        <FlyToZone zoneName={focusedZone} zones={validZones} />
        {validZones.map((zone) => {
          const { fill, r, weight } = zoneStyle(zone, worstZoneKey, focusedZone);
          return (
            <CircleMarker
              key={zone.cell_id ? `${zone.country ?? 'na'}-${zone.zone}-${zone.cell_id}` : `${zone.country ?? 'na'}-${zone.zone}`}
              center={[zone.lat, zone.lon]}
              radius={r}
              pathOptions={{
                color: '#0f172a',
                weight,
                fillColor: fill,
                fillOpacity: 0.82,
              }}
              eventHandlers={{
                click: () => onSelectZone?.(zone.zone),
              }}
            >
              <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
                <div className="text-xs font-medium text-slate-800 max-w-[200px]">
                  <div className="font-bold">{zone.zone}</div>
                  <div>Country: {zone.country ?? 'Unknown'}</div>
                  {zone.cell_id && <div>Cell: {zone.cell_id}</div>}
                  <div>MOS avg: {zone.avg_mos != null ? zone.avg_mos.toFixed(2) : '—'}</div>
                  <div>SLA risk: {zone.avg_sla_breach_risk != null ? zone.avg_sla_breach_risk.toFixed(3) : '—'}</div>
                  <div>Critical events: {zone.critical_count ?? 0}</div>
                  <div>Records: {zone.records ?? '—'}</div>
                </div>
              </Tooltip>
              <Popup>
                <strong>{zone.zone}</strong>
                <br />
                Latency / packet KPIs are available in the unified dataset per cell; zone view is aggregated by city.
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </motion.div>
  );
}
