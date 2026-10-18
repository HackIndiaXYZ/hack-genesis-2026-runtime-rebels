import { useTranslation } from 'react-i18next';
import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, Image as ImageIcon, MapPin, Building2, Send, CheckCircle2, Search, Loader2, AlertTriangle, ThumbsUp } from 'lucide-react';
import ScanOverlay from '../components/ScanOverlay';
import ConfidenceGauge from '../components/ConfidenceGauge';
import SeverityBadge from '../components/SeverityBadge';
import LocationMap from '../components/LocationMap';
import { analyzeIssue, submitComplaint, upvoteComplaint, generateComplaintText } from '../api';
import clsx from 'clsx';
import { Link } from 'react-router-dom';
import exifr from 'exifr';

export default function Report() {
  const { t, i18n } = useTranslation();
  const [image, setImage] = useState(null);
  const [file, setFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [isPinningMode, setIsPinningMode] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successId, setSuccessId] = useState(null);
  const [upvotedId, setUpvotedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const fileInputRef = useRef(null);

  const reverseGeocode = async (lat, lng) => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`);
      const data = await res.json();
      if (data && data.address) {
        const { road, neighbourhood, suburb, village, city, town, state, postcode } = data.address;
        const localArea = road || neighbourhood || suburb || village || '';
        const cityArea = city || town || '';
        const parts = [localArea, cityArea, state, postcode].filter(Boolean);
        if (parts.length > 0) return parts.join(', ');
      }
      return data.display_name || `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    } catch (e) {
      return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
  };

  const handleImageUpload = async (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onload = (e) => setImage(e.target.result);
      reader.readAsDataURL(selectedFile);
      setAnalysisResult(null);
      setSuccessId(null);
      setUpvotedId(null);
      setError(null);
    }
  };

  const detectLocationAndAnalyze = async () => {
    setIsLocating(true);
    let lat = 26.4729, lng = 80.3498; // Default Kanpur
    let accuracy = null;

    try {
      // 1. Try EXIF
      const exifData = await exifr.gps(file);
      if (exifData && exifData.latitude && exifData.longitude) {
        lat = exifData.latitude;
        lng = exifData.longitude;
      } else {
        // 2. Try Browser Geolocation
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 6000, maximumAge: 0 });
        });
        lat = pos.coords.latitude;
        lng = pos.coords.longitude;
        accuracy = pos.coords.accuracy;
      }
    } catch (err) {
      console.warn("Location detection fallback applied:", err);
    }

    const address = await reverseGeocode(lat, lng);
    setIsLocating(false);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('latitude', lat);
      formData.append('longitude', lng);
      formData.append('address', address);
      formData.append('language', i18n.language || 'en');

      const realResult = await analyzeIssue(formData);
      realResult.location.accuracy = accuracy;
      setAnalysisResult(realResult);
    } catch (err) {
      console.error("AI Analysis failed:", err);
      setError(err.message || 'AI pipeline analysis failed. Please verify server connection.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Re-generate complaint text when language changes
  useEffect(() => {
    if (analysisResult && analysisResult.location && analysisResult.location.address !== t('report.loading_address')) {
      generateComplaintText(
        analysisResult.category,
        analysisResult.severity,
        analysisResult.location.address,
        i18n.language
      ).then(text => {
        if (text) {
          setAnalysisResult(prev => ({ ...prev, complaint_text: text, language: i18n.language }));
        }
      });
    }
  }, [i18n.language]);

  const handleAnalyze = () => {
    if (!image || !file) return;
    setIsAnalyzing(true);
    setError(null);
  };

  const handleScanComplete = async () => {
    await detectLocationAndAnalyze();
  };

  const handleLocationChange = async ({ lat, lng }) => {
    if (!analysisResult) return;
    setAnalysisResult(prev => ({ ...prev, location: { ...prev.location, lat, lng, address: t("report.loading_address") } }));
    const address = await reverseGeocode(lat, lng);
    
    // Regenerate text with new address
    const newText = await generateComplaintText(analysisResult.category, analysisResult.severity, address, i18n.language);

    setAnalysisResult(prev => ({ 
      ...prev, 
      location: { ...prev.location, lat, lng, address },
      complaint_text: newText || prev.complaint_text
    }));
  };

  const handleSearchAddress = async () => {
    if (!searchQuery) return;
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (data && data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lng = parseFloat(data[0].lon);
        handleLocationChange({ lat, lng });
      }
    } catch (e) {
      console.error('Geocoding search failed:', e);
    }
  };

  const handleSubmit = async () => {
    if (!analysisResult) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await submitComplaint({
        complaint_id: analysisResult.complaint_id,
        category: analysisResult.category,
        confidence: analysisResult.confidence,
        severity: analysisResult.severity,
        location: analysisResult.location,
        department: analysisResult.department,
        suggested_action: analysisResult.suggested_action,
        complaint_text: analysisResult.complaint_text,
        language: i18n.language || 'en',
        duplicate_of: analysisResult.duplicate_of,
        estimated_resolution_hours: analysisResult.estimated_resolution_hours,
        image_path: analysisResult.image_path
      });
      setSuccessId(result.complaint_id);
    } catch (err) {
      setError(err.message || 'Submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpvoteDuplicate = async () => {
    if (!analysisResult?.duplicate_of) return;
    try {
      await upvoteComplaint(analysisResult.duplicate_of);
      setUpvotedId(analysisResult.duplicate_of);
    } catch (err) {
      setError(err.message || 'Upvoting duplicate failed');
    }
  };

  if (upvotedId) {
    return (
      <div className="max-w-2xl mx-auto text-center mt-20">
        <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="civic-card p-10 flex flex-col items-center">
          <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center mb-6">
            <ThumbsUp className="w-10 h-10 text-primary" />
          </div>
          <h2 className="text-3xl mb-2 font-display">Duplicate Upvoted!</h2>
          <p className="text-muted mb-8">We added your report to the existing complaint to escalate its priority with the municipal department.</p>
          
          <div className="bg-subtle border border-default rounded-lg p-6 w-full mb-8">
            <div className="text-sm text-disabled uppercase tracking-wider mb-1">Existing Tracking ID</div>
            <div className="text-4xl font-mono text-main tracking-widest">{upvotedId}</div>
          </div>

          <div className="flex gap-4 w-full">
            <Link to={`/track?id=${encodeURIComponent(upvotedId)}`} className="btn-secondary flex-1">Track Existing Issue</Link>
            <button onClick={() => { setImage(null); setFile(null); setAnalysisResult(null); setUpvotedId(null); setError(null); }} className="btn-primary flex-1">Report Another</button>
          </div>
        </motion.div>
      </div>
    );
  }

  if (successId) {
    return (
      <div className="max-w-2xl mx-auto text-center mt-20">
        <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="civic-card p-10 flex flex-col items-center">
          <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center mb-6">
            <CheckCircle2 className="w-10 h-10 text-primary" />
          </div>
          <h2 className="text-3xl mb-2 font-display">Complaint Submitted!</h2>
          <p className="text-muted mb-8">Your issue has been recorded and routed to the appropriate department.</p>
          
          <div className="bg-subtle border border-default rounded-lg p-6 w-full mb-8">
            <div className="text-sm text-disabled uppercase tracking-wider mb-1">Official Tracking ID</div>
            <div className="text-4xl font-mono text-main tracking-widest">{successId}</div>
          </div>

          <div className="flex gap-4 w-full">
            <Link to={`/track?id=${encodeURIComponent(successId)}`} className="btn-secondary flex-1">Track Status</Link>
            <button onClick={() => { setImage(null); setFile(null); setAnalysisResult(null); setSuccessId(null); setError(null); }} className="btn-primary flex-1">Report Another</button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-3xl md:text-4xl mb-4 font-display">Report an Issue</h1>
        <p className="text-muted max-w-xl mx-auto">Upload a photo of a public issue. Our AI detects the problem, pinpoints GPS coordinates, and routes it directly to city officials.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="civic-card p-6 flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-display">{t("report.evidence")}</h3>
          </div>
          
          <div 
            className="flex-1 border-2 border-dashed border-default hover:border-primary transition-colors rounded-md relative overflow-hidden flex items-center justify-center bg-subtle cursor-pointer min-h-[300px]"
            onClick={() => fileInputRef.current?.click()}
          >
            {image ? (
              <>
                <img src={image} alt="Preview" className="absolute inset-0 w-full h-full object-cover" />
                <ScanOverlay isScanning={isAnalyzing} onScanComplete={handleScanComplete} />
              </>
            ) : (
              <div className="flex flex-col items-center text-disabled">
                <UploadCloud className="w-12 h-12 mb-4 text-primary/70" />
                <span className="font-medium text-main">{t("report.click_upload")}</span>
                <span className="text-sm mt-1">{t("report.drag_drop")}</span>
              </div>
            )}
            <input type="file" ref={fileInputRef} onChange={handleImageUpload} accept="image/*,video/*" className="hidden" />
          </div>

          <div className="mt-6">
            <button 
              className={clsx("w-full py-4 rounded-md font-bold flex items-center justify-center gap-2 transition-all", 
                !image || (isAnalyzing || isLocating) ? "bg-default text-disabled cursor-not-allowed" : "btn-primary border-primary shadow-sm"
              )}
              onClick={handleAnalyze}
              disabled={!image || isAnalyzing || isLocating || analysisResult}
            >
              {isLocating ? <><Loader2 className="w-5 h-5 animate-spin" /> {t("report.btn_detecting")}</> : isAnalyzing ? <><Loader2 className="w-5 h-5 animate-spin" /> {t("report.btn_analyzing")}</> : analysisResult ? t("report.btn_complete") : t("report.btn_analyze")}
            </button>
          </div>
        </div>

        {/* Results Section */}
        <div className="civic-card p-6 relative overflow-hidden min-h-[600px]">
          {error && (
            <div className="p-4 mb-4 rounded-lg bg-critical/10 border border-critical/50 text-critical flex flex-col items-center justify-center text-center">
               <strong className="block mb-1">{t("report.analysis_failed")}</strong>
               <span className="text-sm">{error}</span>
            </div>
          )}
          {!analysisResult ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-disabled px-8 text-center lg:border-l border-default">
               <ImageIcon className="w-16 h-16 mb-4 opacity-20" />
               <p>{t("report.upload_placeholder")}</p>
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full space-y-6">
              
              {/* Duplicate Banner */}
              {analysisResult.duplicate_of && (
                <div className="p-4 rounded-lg bg-warning/10 border border-warning/40 text-main flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-warning shrink-0" />
                    <div>
                      <div className="font-semibold text-sm">Similar issue already reported nearby!</div>
                      <div className="text-xs text-muted">Tracking ID: <span className="font-mono font-bold text-main">{analysisResult.duplicate_of}</span> (50m radius)</div>
                    </div>
                  </div>
                  <button 
                    onClick={handleUpvoteDuplicate}
                    className="btn-secondary text-xs py-1.5 px-3 whitespace-nowrap flex items-center gap-1.5 self-end sm:self-auto"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" /> Upvote Instead
                  </button>
                </div>
              )}

              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-2xl font-bold capitalize text-main mb-2">{analysisResult.category}</h3>
                  <div className="flex flex-wrap gap-2">
                    <SeverityBadge level={analysisResult.severity} />
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 bg-subtle rounded-full border border-default text-muted">
                      <Building2 className="w-3.5 h-3.5 text-primary" /> {analysisResult.department}
                    </span>
                  </div>
                </div>
                <ConfidenceGauge score={analysisResult.confidence} size={64} />
              </div>

              <div className="space-y-4 flex-1">
                <div className="bg-surface p-4 rounded-lg border border-default shadow-sm flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2 text-sm text-disabled font-medium">
                      <MapPin className="w-4 h-4 text-primary" /> Location & Coordinates
                    </div>
                    <button 
                      onClick={() => setIsPinningMode(!isPinningMode)}
                      className={clsx("text-xs font-semibold px-3 py-1.5 rounded-full transition-colors flex items-center gap-1", 
                        isPinningMode ? "bg-primary text-main shadow-sm" : "bg-subtle text-muted hover:bg-default"
                      )}
                    >
                      📍 Pin on map
                    </button>
                  </div>
                  
                  {isPinningMode && (
                    <div className="text-xs text-primary font-medium bg-primary/10 p-2 rounded text-center border border-primary/20">
                      {t("report.pin_instruction")}
                    </div>
                  )}
                  
                  <div className="flex gap-2">
                    <input 
                      type="text" 
                      placeholder={t("report.search_placeholder")} 
                      className="flex-1 bg-subtle border border-default rounded p-2 text-sm text-main focus:outline-none focus:border-primary/50"
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleSearchAddress()}
                    />
                    <button onClick={handleSearchAddress} className="bg-subtle hover:bg-default text-muted font-semibold px-3 py-2 rounded transition-colors">
                      <Search className="w-4 h-4" />
                    </button>
                  </div>

                  <div className={`h-48 w-full rounded overflow-hidden border ${isPinningMode ? 'border-primary shadow-[0_0_0_2px_rgba(0,229,195,0.2)]' : 'border-default'}`}>
                    <LocationMap 
                      lat={analysisResult.location.lat} 
                      lng={analysisResult.location.lng} 
                      accuracy={analysisResult.location.accuracy}
                      editable={true} 
                      pinningMode={isPinningMode}
                      onLocationChange={handleLocationChange} 
                    />
                  </div>
                  <div className="text-disabled text-xs font-mono text-center">
                    {Math.abs(analysisResult.location.lat).toFixed(6)}° {analysisResult.location.lat >= 0 ? 'N' : 'S'}, {Math.abs(analysisResult.location.lng).toFixed(6)}° {analysisResult.location.lng >= 0 ? 'E' : 'W'}
                  </div>
                  <textarea 
                    className="w-full bg-subtle border border-default rounded text-main resize-none p-2 text-sm focus:outline-none focus:border-primary/50"
                    rows={2}
                    value={analysisResult.location.address}
                    onChange={(e) => setAnalysisResult(prev => ({ ...prev, location: { ...prev.location, address: e.target.value } }))}
                  />
                </div>

                <div className="bg-subtle p-4 rounded-lg border border-default space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold uppercase tracking-wider text-disabled">{t("report.ai_generated")}</span>
                    <span className="text-xs text-muted">Estimated SLA: <strong className="text-main">{analysisResult.estimated_resolution_hours}h</strong></span>
                  </div>
                  <textarea 
                    className="w-full bg-surface border border-default rounded text-main resize-none p-2.5 text-sm focus:outline-none focus:border-primary/50"
                    rows={3}
                    value={analysisResult.complaint_text}
                    onChange={(e) => setAnalysisResult(prev => ({ ...prev, complaint_text: e.target.value }))}
                  />
                </div>
              </div>

              <button 
                className="btn-primary w-full flex items-center justify-center gap-2 py-3.5 font-bold"
                onClick={handleSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> {t("report.btn_submitting")}</>
                ) : (
                  <><Send className="w-5 h-5" /> Submit Complaint</>
                )}
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
