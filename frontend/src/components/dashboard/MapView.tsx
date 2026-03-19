import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Polygon, Popup, useMap } from "react-leaflet";
import { LatLngBoundsExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { Geo, Zone } from "@/types/analysis";

interface MapViewProps {
  geo: Geo;
  zones: Zone[];
  activeZoneId?: number | null;
  mapImage?: string;
}

const severityColor: Record<string, string> = {
  HIGH: "#EF4444",
  MODERATE: "#F59E0B",
  LOW: "#10B981",
};

const severityFill: Record<string, number> = {
  HIGH: 0.4,
  MODERATE: 0.3,
  LOW: 0.25,
};

function FlyToZone({ zone }: { zone: Zone | undefined }) {
  const map = useMap();
  useEffect(() => {
    if (zone?.geo_coordinates && zone.geo_coordinates.length > 0) {
      const coords = zone.geo_coordinates;
      const lat = coords.reduce((s, c) => s + c[0], 0) / coords.length;
      const lon = coords.reduce((s, c) => s + c[1], 0) / coords.length;
      map.flyTo([lat, lon], 17, { duration: 0.8 });
    }
  }, [zone, map]);
  return null;
}

const MapView = ({ geo, zones, activeZoneId, mapImage }: MapViewProps) => {
  if (!geo.available) {
    return (
      <div className="card-elevated overflow-hidden flex items-center justify-center bg-muted/50 min-h-[400px] border border-border">
        {mapImage ? (
          <img 
            src={`data:image/jpeg;base64,${mapImage}`} 
            alt="Analysis overlay" 
            className="w-full h-full object-contain"
          />
        ) : (
          <p className="text-sm text-muted-foreground">Geolocation data unavailable — map view disabled</p>
        )}
      </div>
    );
  }

  const activeZone = zones.find((z) => z.zone_id === activeZoneId);

  return (
    <div className="card-elevated overflow-hidden" style={{ height: "100%", minHeight: 400 }}>
      <MapContainer
        center={[geo.lat, geo.lon]}
        zoom={16}
        scrollWheelZoom
        style={{ height: "100%", width: "100%", minHeight: 400 }}
        bounds={geo.bounds as LatLngBoundsExpression}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />
        <FlyToZone zone={activeZone} />
        {zones.map((zone) => {
          if (!zone.geo_coordinates || zone.geo_coordinates.length < 3) return null;
          const isActive = zone.zone_id === activeZoneId;
          return (
            <Polygon
              key={zone.zone_id}
              positions={zone.geo_coordinates.map(([lat, lon]) => [lat, lon] as [number, number])}
              pathOptions={{
                color: severityColor[zone.severity],
                fillColor: severityColor[zone.severity],
                fillOpacity: isActive ? 0.6 : severityFill[zone.severity],
                weight: isActive ? 3 : 2,
              }}
            >
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-semibold">Zone {zone.zone_id} — {zone.severity}</p>
                  <p>{zone.issue}</p>
                  <p className="text-muted-foreground">{zone.recommendation}</p>
                </div>
              </Popup>
            </Polygon>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default MapView;
