import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, MapPin, Building2, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { getComplaints, getComplaint, getImageUrl } from '../api';
import StatusTimeline from '../components/StatusTimeline';
import SeverityBadge from '../components/SeverityBadge';
import LocationMap from '../components/LocationMap';

export default function Track() {
  const [searchParams] = useSearchParams();
  const urlId = searchParams.get('id') || '';
  const [complaints, setComplaints] = useState([]);
  const [searchId, setSearchId] = useState(urlId);
  const [activeComplaint, setActiveComplaint] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);

  const fetchComplaints = () => {
    setIsLoading(true);
    setLoadError(null);
    getComplaints({ limit: 50 })
      .then(async (data) => {
        const list = data || [];
        setComplaints(list);
        
        // If query param ID was provided, fetch or select it
        if (urlId) {
          const match = list.find(c => c.complaint_id.toLowerCase() === urlId.toLowerCase());
          if (match) {
            setActiveComplaint(match);
          } else {
            try {
              const remote = await getComplaint(urlId);
              if (remote) {
                setActiveComplaint(remote);
                setComplaints([remote, ...list]);
              }
            } catch {
              if (list.length > 0) setActiveComplaint(list[0]);
            }
          }
        } else if (list.length > 0) {
          setActiveComplaint(list[0]);
        }
      })
      .catch(err => {
        console.error('Failed to load complaints for tracking:', err);
        setLoadError(err.message || 'Could not connect to backend.');
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchComplaints();
  }, [urlId]);

  const handleSearch = async (e) => {
    e.preventDefault();
    const query = searchId.trim();
    if (!query) return;

    setSearchError(null);
    setIsSearching(true);

    // Check local loaded list first
    const localFound = complaints.find(c => c.complaint_id.toLowerCase() === query.toLowerCase());
    if (localFound) {
      setActiveComplaint(localFound);
      setIsSearching(false);
      return;
    }

    // Try fetching from backend
    try {
      const remoteFound = await getComplaint(query);
      if (remoteFound) {
        setActiveComplaint(remoteFound);
        // Prepend to list if not already there
        setComplaints(prev => [remoteFound, ...prev.filter(c => c.complaint_id !== remoteFound.complaint_id)]);
      }
    } catch (err) {
      setSearchError(`No complaint found with ID '${query}'.`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Sidebar List */}
      <div className="civic-card p-6 flex flex-col h-[80vh]">
        <h2 className="text-2xl mb-6 font-display">Track Status</h2>
        
        <form onSubmit={handleSearch} className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-disabled w-5 h-5" />
          <input 
            type="text" 
            placeholder="Enter Complaint ID (e.g. CF-2026-00847)" 
            className="w-full bg-subtle border border-default rounded-lg pl-10 pr-10 py-3 text-main focus:outline-none focus:border-primary/50 transition-colors text-sm"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
          />
          {isSearching && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 text-primary w-4 h-4 animate-spin" />
          )}
        </form>

        {searchError && (
          <div className="mb-4 text-xs text-critical bg-critical/10 p-2.5 rounded border border-critical/30">
            {searchError}
          </div>
        )}

        <div className="text-xs text-disabled uppercase tracking-wider font-semibold mb-3">Recent Reports</div>
        
        {loadError && (
          <div className="p-3 mb-3 rounded bg-critical/10 border border-critical/30 text-critical text-xs flex flex-col gap-2">
            <span>{loadError}</span>
            <button onClick={fetchComplaints} className="btn-secondary text-xs py-1 px-2 flex items-center justify-center gap-1 self-start">
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center text-disabled">
            <Loader2 className="w-6 h-6 animate-spin text-primary mr-2" /> Loading reports...
          </div>
        ) : complaints.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-disabled text-sm text-center p-4">
            No complaints found in the registry.
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
            {complaints.map(complaint => (
              <div 
                key={complaint.complaint_id}
                onClick={() => setActiveComplaint(complaint)}
                className={`p-3.5 rounded-md border transition-all cursor-pointer ${
                  activeComplaint?.complaint_id === complaint.complaint_id 
                    ? 'bg-primary/10 border-primary/40 shadow-xs' 
                    : 'bg-subtle border-default hover:border-primary/30'
                }`}
              >
                <div className="flex justify-between items-start mb-1.5">
                  <span className="font-mono font-bold text-sm text-main">{complaint.complaint_id}</span>
                  <span className="text-xs text-disabled">
                    {(complaint.created_at || complaint.createdAt) 
                      ? new Date(complaint.created_at || complaint.createdAt).toLocaleDateString([], { month: 'short', day: 'numeric' }) 
                      : ''}
                  </span>
                </div>
                <h4 className="font-medium capitalize text-muted truncate text-sm">{complaint.category}</h4>
                <p className="text-xs text-disabled truncate mt-1">{complaint.location?.address}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Details View */}
      <div className="lg:col-span-2 civic-card p-8 h-[80vh] overflow-y-auto custom-scrollbar">
        {activeComplaint ? (
          <div className="space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h1 className="text-3xl font-display font-bold text-main mb-2">{activeComplaint.complaint_id}</h1>
                <h3 className="text-xl text-muted capitalize font-medium">{activeComplaint.category}</h3>
              </div>
              <div className="flex flex-col items-end">
                <SeverityBadge level={activeComplaint.severity} className="mb-2" />
                <span className="text-sm text-muted flex items-center gap-1">
                  <Building2 className="w-4 h-4 text-primary" /> {activeComplaint.department}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-surface p-5 rounded-md border border-default shadow-sm flex flex-col gap-3">
                <div className="text-disabled text-sm mb-1 flex items-center gap-2"><MapPin className="w-4 h-4 text-primary"/> Location</div>
                <div className="text-main font-medium text-sm">{activeComplaint.location?.address}</div>
                {activeComplaint.location?.lat && (
                  <div className="text-disabled text-xs font-mono">
                    {Math.abs(activeComplaint.location.lat).toFixed(6)}° {activeComplaint.location.lat >= 0 ? 'N' : 'S'}, {Math.abs(activeComplaint.location.lng).toFixed(6)}° {activeComplaint.location.lng >= 0 ? 'E' : 'W'}
                  </div>
                )}
                {activeComplaint.location?.lat && (
                  <div className="h-32 w-full mt-2 rounded overflow-hidden border border-default">
                    <LocationMap lat={activeComplaint.location.lat} lng={activeComplaint.location.lng} editable={false} />
                  </div>
                )}
              </div>
              
              <div className="bg-subtle p-5 rounded-md border border-default flex flex-col justify-between">
                <div>
                  <div className="text-disabled text-sm mb-1 flex items-center gap-2"><AlertCircle className="w-4 h-4 text-primary"/> Estimated SLA</div>
                  <div className="text-2xl font-bold font-display text-main mt-1">{activeComplaint.estimated_resolution_hours} Hours</div>
                  <div className="text-disabled text-xs mt-1">Calculated from submission timestamp</div>
                </div>

                {activeComplaint.suggested_action && (
                  <div className="mt-4 pt-3 border-t border-default">
                    <div className="text-xs font-semibold uppercase text-disabled mb-1">Recommended Action</div>
                    <div className="text-xs text-muted leading-relaxed">{activeComplaint.suggested_action}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Photographic Evidence if available */}
            {activeComplaint.image_path && (
              <div className="bg-surface p-4 rounded-md border border-default shadow-sm">
                <div className="text-disabled text-xs font-semibold uppercase tracking-wider mb-2">Photographic Evidence</div>
                <div className="h-52 w-full rounded overflow-hidden bg-subtle flex items-center justify-center border border-default">
                  <img 
                    src={getImageUrl(activeComplaint.image_path)} 
                    alt={`Evidence for ${activeComplaint.complaint_id}`}
                    className="w-full h-full object-contain bg-black/5"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                </div>
              </div>
            )}

            {/* Official Complaint Statement */}
            <div className="bg-subtle/50 p-5 rounded-md border border-default space-y-2">
              <h4 className="text-xs font-semibold uppercase text-disabled tracking-wider">Complaint Description</h4>
              <p className="text-sm text-main whitespace-pre-line leading-relaxed">{activeComplaint.complaint_text}</p>
            </div>

            {/* Timeline */}
            <div className="bg-subtle/30 p-6 rounded-md border border-default">
              <h4 className="text-lg font-display font-medium mb-4 text-main">Resolution Timeline</h4>
              <StatusTimeline 
                currentStatus={activeComplaint.status} 
                history={activeComplaint.history || []} 
              />
            </div>

            {activeComplaint.status === 'resolved' && (
              <div className="bg-primary/5 border border-primary/20 rounded-md p-6">
                <h4 className="text-primary font-medium mb-4 flex items-center gap-2 font-display">
                  Issue Resolved Successfully
                </h4>
                <div className="text-sm text-muted">
                  Municipal engineering verified field completion. The ticket has been formally closed.
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-disabled">
            Select a complaint from the list to view its real-time tracking details.
          </div>
        )}
      </div>
    </div>
  );
}
