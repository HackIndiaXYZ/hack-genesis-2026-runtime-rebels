import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, Activity, MapPin } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-surface border-t border-default mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded bg-primary flex items-center justify-center shadow-sm">
                <Activity className="text-white w-3.5 h-3.5" />
              </div>
              <span className="font-display font-bold text-lg tracking-tight text-main">CivicFix</span>
            </Link>
            <p className="text-muted text-sm max-w-sm mb-6 leading-relaxed">
              A civic utility tool designed to help citizens report and track public infrastructure issues across local municipalities. Built for real people, solving real problems.
            </p>
            <div className="flex gap-4">
              <a href="https://github.com/placeholder/civicfix" target="_blank" rel="noreferrer" className="text-disabled hover:text-muted transition-colors text-sm font-medium">
                GitHub
              </a>
              <a href="mailto:hello@civicfix.local" className="text-disabled hover:text-muted transition-colors">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>
          
          <div>
            <h3 className="font-semibold text-main mb-4">Platform</h3>
            <ul className="space-y-3">
              <li><Link to="/report" className="text-muted hover:text-primary text-sm">Report an Issue</Link></li>
              <li><Link to="/track" className="text-muted hover:text-primary text-sm">Track Status</Link></li>
              <li><Link to="/map" className="text-muted hover:text-primary text-sm">City Map</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-main mb-4">Legal</h3>
            <ul className="space-y-3">
              <li><Link to="/" className="text-muted hover:text-primary text-sm">Terms of Service</Link></li>
              <li><Link to="/" className="text-muted hover:text-primary text-sm">Privacy Policy</Link></li>
              <li><Link to="/" className="text-muted hover:text-primary text-sm">Contact Us</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-default mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-disabled text-sm">© {new Date().getFullYear()} CivicFix Municipal Utility. All rights reserved.</p>
          <div className="text-disabled text-xs font-medium">
            Currently serving Kanpur, Varanasi, and select UP districts.
          </div>
        </div>
      </div>
    </footer>
  );
}
