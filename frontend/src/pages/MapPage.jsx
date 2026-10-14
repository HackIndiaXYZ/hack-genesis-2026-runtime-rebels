import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import 'leaflet/dist/leaflet.css';
import { getComplaints } from '../api';
import L from 'leaflet';
import SeverityBadge from '../components/SeverityBadge';
import { Link } from 'react-router-dom';
import { Navigation } from 'lucide-react';

const severityColors = {
  low: '#00E5C3', // teal
  medium: '#FFB020', // amber
  high: '#FF4D6A', // coral
  critical: '#FF4D6A' // coral
};

const createCustomIcon = (severity) => {
  const color = severityColors[severity] || '#60A5FA';
  // convert hex to rgba for the pulse shadow
  let rgba = 'rgba(96, 165, 250, 0.7)';
  if (color === '#00E5C3') rgba = 'rgba(0, 229, 195, 0.7)';
  else if (color === '#FFB020') rgba = 'rgba(255, 176, 32, 0.7)';
  else if (color === '#FF4D6A') rgba = 'rgba(255, 77, 106, 0.7)';

  return L.divIcon({
    className: 'custom-leaflet-icon bg-transparent border-0',
    html: `<div class="pulse-marker-custom" style="background-color: ${color}; --pulse-color: ${rgba}; width: 16px; height: 16px; border: 2px solid white;"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

function LocateMeButton() {
  const map = useMap();
  const handleLocate = () => {
    navigator.geolocation.getCurrentPosition((pos) => {
      map.flyTo([pos.coords.latitude, pos.coords.longitude], 16, { duration: 1.5 });
    }, () => alert("Could not get your location. Please check your browser permissions."));
  };
  return (
    <button 
      onClick={handleLocate}
      className="absolute bottom-6 right-6 z-[1000] bg-surface text-muted p-3 rounded-full shadow-lg border border-default hover:bg-subtle transition-colors"
      title="Locate me"
    >
      <Navigation className="w-6 h-6 text-primary" />
    </button>
  );
}

export default function MapPage() {
  const [complaints, setComplaints] = useState([]);
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [filters, setFilters] = useState({ category: '', severity: '', status: '' });

  useEffect(() => {
    getComplaints().then(setComplaints);
  }, []);

  const filteredComplaints = complaints.filter(c => {
    if (filters.category && c.category !== filters.category) return false;
    if (filters.severity && c.severity !== filters.severity) return false;
    if (filters.status && c.status !== filters.status) return false;
    return true;
  });

  return (
    <div className="h-[calc(100vh-8rem)] -mx-4 sm:-mx-6 lg:-mx-8 -my-8 relative flex flex-col md:flex-row">
      {/* Filters Overlay */}
      <div className="absolute top-4 left-4 z-[1000] flex gap-2">
        <select 
          className="bg-surface border border-default text-muted text-sm rounded-lg px-3 py-2 shadow-sm focus:outline-none"
          value={filters.category}
          onChange={e => setFilters(prev => ({ ...prev, category: e.target.value }))}
        >
          <option value="">All Categories</option>
          <option value="pothole">Pothole</option>
          <option value="overflowing garbage">Overflowing Garbage</option>
          <option value="broken streetlight">Broken Streetlight</option>
          <option value="open manhole">Open Manhole</option>
          <option value="water leakage">Water Leakage</option>
          <option value="damaged road sign">Damaged Road Sign</option>
        </select>
        
        <select 
          className="bg-surface border border-default text-muted text-sm rounded-lg px-3 py-2 shadow-sm focus:outline-none hidden sm:block"
          value={filters.severity}
          onChange={e => setFilters(prev => ({ ...prev, severity: e.target.value }))}
        >
          <option value="">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>

        <select 
          className="bg-surface border border-default text-muted text-sm rounded-lg px-3 py-2 shadow-sm focus:outline-none hidden sm:block"
          value={filters.status}
          onChange={e => setFilters(prev => ({ ...prev, status: e.target.value }))}
        >
          <option value="">All Statuses</option>
          <option value="submitted">Submitted</option>
          <option value="assigned">Assigned</option>
          <option value="in progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      <div className="w-full h-full relative z-0">
        <MapContainer 
          center={[25.317, 82.973]} 
          zoom={13} 
          style={{ height: '100%', width: '100%', background: '#f8fafc' }}
        >
          {/* Free OpenStreetMap tiles, no API key ever required — do not switch to CARTO/Mapbox/Stadia without adding a key. */}
          <TileLayer
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <MarkerClusterGroup 
            chunkedLoading
            maxClusterRadius={40}
            showCoverageOnHover={false}
          >
            {filteredComplaints.map(complaint => (
              <Marker 
                key={complaint.complaint_id}
                position={[complaint.location.lat, complaint.location.lng]}
                icon={createCustomIcon(complaint.severity)}
                eventHandlers={{ click: () => setSelectedComplaint(complaint) }}
              />
            ))}
          </MarkerClusterGroup>
          <LocateMeButton />
        </MapContainer>
      </div>

      {/* Info Panel Overlay */}
      {selectedComplaint && (
        <div className="absolute bottom-0 left-0 right-0 md:top-16 md:right-4 md:left-auto md:bottom-auto w-full md:w-80 bg-surface shadow-xl p-5 z-[1000] rounded-b-none md:rounded-md border border-default m-0">
          <div className="flex justify-between items-start mb-3">
            <div>
              <span className="font-mono text-xs text-primary mb-1 block">{selectedComplaint.complaint_id}</span>
              <h3 className="text-lg font-bold capitalize leading-tight text-main">{selectedComplaint.category}</h3>
            </div>
            <button onClick={() => setSelectedComplaint(null)} className="text-muted hover:text-muted">&times;</button>
          </div>
          
          <SeverityBadge level={selectedComplaint.severity} className="mb-4" />
          
          <div className="text-xs text-muted mb-4 bg-subtle p-2 rounded-lg line-clamp-2 border border-default">
            {selectedComplaint.location.address}
          </div>

          <div className="flex justify-between items-center mb-4">
             <span className="text-xs text-disabled capitalize">Status: <strong className="text-main">{selectedComplaint.status}</strong></span>
          </div>
          
          <Link to="/track" className="btn-primary text-sm w-full block text-center py-2">View Full Details</Link>
        </div>
      )}
    </div>
  );
}
