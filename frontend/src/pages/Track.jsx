import React, { useState, useEffect } from 'react';
import { Search, MapPin, Building2, AlertCircle } from 'lucide-react';
import { getComplaints } from '../api';
import StatusTimeline from '../components/StatusTimeline';
import SeverityBadge from '../components/SeverityBadge';
import LocationMap from '../components/LocationMap';

export default function Track() {
  const [complaints, setComplaints] = useState([]);
  const [searchId, setSearchId] = useState('');
  const [activeComplaint, setActiveComplaint] = useState(null);

  useEffect(() => {
    getComplaints().then(data => {
      setComplaints(data);
      if (data.length > 0) setActiveComplaint(data[0]);
    });
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    const found = complaints.find(c => c.complaint_id.toLowerCase() === searchId.toLowerCase());
    if (found) setActiveComplaint(found);
  };

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Sidebar List */}
      <div className="civic-card p-6 flex flex-col h-[80vh]">
        <h2 className="text-2xl mb-6">Track Status</h2>
        
        <form onSubmit={handleSearch} className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-disabled w-5 h-5" />
          <input 
            type="text" 
            placeholder="Enter Complaint ID" 
            className="w-full bg-subtle border border-default rounded-lg pl-10 pr-4 py-3 text-main focus:outline-none focus:border-primary/50 transition-colors"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
          />
        </form>

        <div className="text-sm text-disabled uppercase tracking-wider font-semibold mb-4">Recent Reports</div>
        
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
          {complaints.map(complaint => (
            <div 
              key={complaint.complaint_id}
              onClick={() => setActiveComplaint(complaint)}
              className={`p-4 rounded-md border transition-all cursor-pointer ${
                activeComplaint?.complaint_id === complaint.complaint_id 
                  ? 'bg-primary/10 border-primary/30' 
                  : 'bg-subtle border-default hover:bg-subtle'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="font-mono font-bold text-main">{complaint.complaint_id}</span>
                <span className="text-xs text-disabled">{new Date(complaint.createdAt).toLocaleDateString()}</span>
              </div>
              <h4 className="font-medium capitalize text-muted truncate">{complaint.category}</h4>
              <p className="text-sm text-disabled truncate mt-1">{complaint.location.address}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Details View */}
      <div className="lg:col-span-2 civic-card p-8 h-[80vh] overflow-y-auto custom-scrollbar">
        {activeComplaint ? (
          <div className="space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h1 className="text-3xl font-display font-bold text-main mb-2">{activeComplaint.complaint_id}</h1>
                <h3 className="text-xl text-muted capitalize">{activeComplaint.category}</h3>
              </div>
              <div className="flex flex-col items-end">
                <SeverityBadge level={activeComplaint.severity} className="mb-2" />
                <span className="text-sm text-disabled flex items-center gap-1">
                  <Building2 className="w-4 h-4" /> {activeComplaint.department}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-surface p-5 rounded-md border border-default shadow-sm flex flex-col gap-3">
                <div className="text-disabled text-sm mb-1 flex items-center gap-2"><MapPin className="w-4 h-4"/> Location</div>
                <div className="text-main font-medium">{activeComplaint.location.address}</div>
                <div className="text-disabled text-xs font-mono">
                  {Math.abs(activeComplaint.location.lat).toFixed(6)}° {activeComplaint.location.lat >= 0 ? 'N' : 'S'}, {Math.abs(activeComplaint.location.lng).toFixed(6)}° {activeComplaint.location.lng >= 0 ? 'E' : 'W'}
                </div>
                <div className="h-32 w-full mt-2 rounded overflow-hidden border border-default">
                  <LocationMap lat={activeComplaint.location.lat} lng={activeComplaint.location.lng} editable={false} />
                </div>
              </div>
              
              <div className="bg-subtle p-5 rounded-md border border-default">
                <div className="text-disabled text-sm mb-1 flex items-center gap-2"><AlertCircle className="w-4 h-4"/> Estimated Resolution</div>
                <div className="text-main font-medium">{activeComplaint.estimated_resolution_hours} Hours</div>
                <div className="text-disabled text-xs mt-1">From submission time</div>
              </div>
            </div>

            <div className="bg-subtle/30 p-6 rounded-md border border-default/30">
              <h4 className="text-lg font-medium mb-4">Timeline</h4>
              <StatusTimeline currentStatus={activeComplaint.status} />
            </div>

            {activeComplaint.status === 'resolved' && (
              <div className="bg-primary/5 border border-primary/20 rounded-md p-6">
                <h4 className="text-primary font-medium mb-4 flex items-center gap-2">
                  Issue Resolved Successfully
                </h4>
                <div className="grid grid-cols-2 gap-4">
                   <div className="aspect-video bg-subtle rounded-lg flex items-center justify-center text-disabled text-sm relative overflow-hidden">
                     <div className="absolute top-2 left-2 bg-black/60 px-2 py-1 rounded text-xs">Before</div>
                     [Original Photo]
                   </div>
                   <div className="aspect-video bg-subtle rounded-lg flex items-center justify-center text-disabled text-sm relative overflow-hidden">
                     <div className="absolute top-2 left-2 bg-primary/80 text-black px-2 py-1 rounded text-xs font-bold">After</div>
                     [Resolution Photo]
                   </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-disabled">
            Select a complaint to view details
          </div>
        )}
      </div>
    </div>
  );
}
