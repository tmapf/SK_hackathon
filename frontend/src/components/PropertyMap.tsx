import { useEffect, useMemo } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMap,
} from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import type { FeatureCollection, PropertyFeature, PublicConfig } from "../types";

const WARSAW_CENTER: [number, number] = [52.2297, 21.0122];
/** Greater Warsaw / Mazovia extent used to keep panning within a sensible area. */
const MAP_MAX_BOUNDS = L.latLngBounds(
  [51.85, 20.55],
  [52.55, 21.55],
);
const DEFAULT_TILE_URL =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}";
const DEFAULT_TILE_ATTRIBUTION =
  "Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom";

function createIcon(offerType: string, selected: boolean) {
  const className = [
    offerType === "sprzedaz" ? "marker-sale" : "marker-rent",
    selected ? "marker-selected" : "",
  ]
    .filter(Boolean)
    .join(" ");
  return L.divIcon({
    className: "",
    html: `<div class="${className}" aria-hidden="true"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 18],
  });
}

function FitBounds({ features }: { features: PropertyFeature[] }) {
  const map = useMap();
  useEffect(() => {
    map.setMaxBounds(MAP_MAX_BOUNDS);
    if (!features.length) {
      map.setView(WARSAW_CENTER, 11, { animate: false });
      return;
    }
    const bounds = L.latLngBounds(
      features.map((feature) => [
        feature.geometry.coordinates[1],
        feature.geometry.coordinates[0],
      ]),
    );
    const padded = bounds.pad(0.12);
    map.fitBounds(MAP_MAX_BOUNDS.intersects(padded) ? padded : MAP_MAX_BOUNDS, {
      animate: false,
      maxZoom: 14,
    });
  }, [features, map]);
  return null;
}

interface PropertyMapProps {
  data?: FeatureCollection;
  config?: PublicConfig;
  selectedId: number | null;
  onSelect: (feature: PropertyFeature) => void;
}

export function PropertyMap({
  data,
  config,
  selectedId,
  onSelect,
}: PropertyMapProps) {
  const features = data?.features ?? [];
  const tileUrl = config?.tile_url || DEFAULT_TILE_URL;
  const attribution = config?.tile_attribution || DEFAULT_TILE_ATTRIBUTION;

  const markers = useMemo(
    () =>
      features.map((feature) => (
        <Marker
          key={feature.id}
          position={[
            feature.geometry.coordinates[1],
            feature.geometry.coordinates[0],
          ]}
          icon={createIcon(feature.properties.offer_type, feature.id === selectedId)}
          eventHandlers={{
            click: () => onSelect(feature),
          }}
        />
      )),
    [features, onSelect, selectedId],
  );

  return (
    <MapContainer
      className="map-root"
      center={WARSAW_CENTER}
      zoom={11}
      minZoom={10}
      maxZoom={18}
      maxBounds={MAP_MAX_BOUNDS}
      maxBoundsViscosity={1}
      scrollWheelZoom
      preferCanvas
    >
      <TileLayer attribution={attribution} url={tileUrl} />
      <FitBounds features={features} />
      <MarkerClusterGroup chunkedLoading showCoverageOnHover={false}>
        {markers}
      </MarkerClusterGroup>
    </MapContainer>
  );
}
