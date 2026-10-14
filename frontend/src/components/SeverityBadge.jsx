import React from 'react';
import clsx from 'clsx';
import { AlertCircle, AlertTriangle, Info, ShieldAlert } from 'lucide-react';

const config = {
  low: { color: 'text-success', bg: 'bg-success/10', border: 'border-success/20', icon: Info },
  medium: { color: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/20', icon: AlertTriangle },
  high: { color: 'text-accent', bg: 'bg-accent/10', border: 'border-accent/20', icon: AlertCircle },
  critical: { color: 'text-critical', bg: 'bg-critical/10', border: 'border-critical/20', icon: ShieldAlert },
};

export default function SeverityBadge({ level = 'low', className }) {
  const { color, bg, border, icon: Icon } = config[level.toLowerCase()] || config.low;
  
  return (
    <div className={clsx('inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold uppercase tracking-wider border', color, bg, border, className)}>
      <Icon className="w-3.5 h-3.5" />
      {level}
    </div>
  );
}
