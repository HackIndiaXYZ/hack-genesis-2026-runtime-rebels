import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, useMap, useMapEvents, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet's default icon path issues in bundlers
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

const pulseIcon = L.divIcon({
  className: 'custom-leaflet-icon bg-transparent border-0',
  html: `<div class="pulse-marker-custom" style="background-color: #00E5C3; --pulse-color: rgba(0, 229, 195, 0.7); width: 16px; height: 16px; border: 2px solid white;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

function MapController({ center, isEditable }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, map.getZoom(), { duration: 1.2, easeLinearity: 0.25 });
  }, [center, map]);
  return null;
}

function MapClickEvents({ pinningMode, onLocationChange }) {
  useMapEvents({
    click(e) {
      if (pinningMode && onLocationChange) {
        onLocationChange({ lat: e.latlng.lat, lng: e.latlng.lng });
      }
    }
  });
  return null;
}

export default function LocationMap({ lat, lng, accuracy, editable = false, pinningMode = false, onLocationChange }) {
  // Fallback to city center if no location provided
  const position = [lat || 25.317, lng || 82.973];
  const markerRef = useRef(null);

  const eventHandlers = {
    dragend() {
      const marker = markerRef.current;
      if (marker != null) {
        const { lat, lng } = marker.getLatLng();
        if (onLocationChange) onLocationChange({ lat, lng });
      }
    },
  };

  return (
    <div className={`w-full h-full min-h-[250px] relative rounded-md overflow-hidden z-0 shadow-sm border border-default ${pinningMode ? 'crosshair-cursor-enabled' : ''}`}>
      <MapContainer center={position} zoom={18} maxZoom={19} style={{ height: '100%', width: '100%', background: '#f8fafc' }}>
        {/* Free OpenStreetMap tiles, no API key ever required — do not switch to CARTO/Mapbox/Stadia without adding a key. */}
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <MapController center={position} isEditable={editable} />
        <MapClickEvents pinningMode={pinningMode} onLocationChange={onLocationChange} />
        {accuracy && lat && lng && (
          <Circle 
            center={position} 
            radius={accuracy} 
            pathOptions={{ color: '#00E5C3', fillColor: '#00E5C3', fillOpacity: 0.1, weight: 1 }} 
          />
        )}
        {lat && lng && (
          <Marker 
            position={position} 
            icon={pulseIcon} 
            draggable={editable}
            eventHandlers={editable ? eventHandlers : undefined}
            ref={markerRef}
          />
        )}
      </MapContainer>
    </div>
  );
}
