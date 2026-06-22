import { analyticsApi } from "../api/client";
import { DataState } from "../components/DataState";
import { GeoMap } from "../components/GeoMap";
import { useAsyncData } from "../hooks/useAsyncData";

export function LiveMapPage() {
  const { data, loading, error } = useAsyncData(
    async () => {
      const [parcels, heatmap] = await Promise.all([
        analyticsApi.parcelsFeed(),
        analyticsApi.pendingHeatmap()
      ]);
      return { parcels, heatmap };
    },
    []
  );

  return (
    <DataState loading={loading} error={error}>
      <section className="stack">
        <div className="panel map-toolbar">
          <div>
            <h2>Parcels and Pending Applications</h2>
            <p>Green polygons are registered parcel geometries. Red points are pending application hotspots.</p>
          </div>
          <div className="map-legend">
            <span><i className="legend-parcel" /> Parcel</span>
            <span><i className="legend-pending" /> Pending</span>
          </div>
        </div>
        <GeoMap parcels={data?.parcels} heatmap={data?.heatmap} />
      </section>
    </DataState>
  );
}
