import L from "leaflet";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";

const defaultCenter = [31.9038, 35.2034];

export function GeoMap({ parcels, heatmap }) {
  const parcelFeatures = parcels?.features || [];
  const heatFeatures = heatmap?.features || [];

  return (
    <MapContainer center={defaultCenter} zoom={13} className="leaflet-frame">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {parcelFeatures.length > 0 && (
        <GeoJSON
          key={`parcels-${parcelFeatures.length}`}
          data={parcels}
          style={{
            color: "#136f63",
            weight: 2,
            fillColor: "#d7f2ec",
            fillOpacity: 0.35
          }}
          onEachFeature={(feature, layer) => {
            const props = feature.properties || {};
            layer.bindPopup(
              `<strong>${props.parcel_code || "Parcel"}</strong><br/>Zone: ${
                props.zone_id || "-"
              }`
            );
          }}
        />
      )}
      {heatFeatures.length > 0 && (
        <GeoJSON
          key={`heat-${heatFeatures.length}`}
          data={heatmap}
          pointToLayer={(_, latlng) =>
            L.circleMarker(latlng, {
              radius: 9,
              color: "#b42318",
              fillColor: "#f97066",
              fillOpacity: 0.75,
              weight: 2
            })
          }
          onEachFeature={(feature, layer) => {
            const props = feature.properties || {};
            layer.bindPopup(
              `<strong>${props.application_id || "Pending application"}</strong><br/>Status: ${
                props.status || "-"
              }`
            );
          }}
        />
      )}
    </MapContainer>
  );
}
