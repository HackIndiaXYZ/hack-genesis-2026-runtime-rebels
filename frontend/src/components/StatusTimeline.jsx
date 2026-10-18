import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

const statuses = [
  { id: 'submitted', label: 'Submitted' },
  { id: 'assigned', label: 'Assigned' },
  { id: 'in_progress', label: 'In Progress' },
  { id: 'resolved', label: 'Resolved' }
];

export default function StatusTimeline({ currentStatus = 'submitted', history = [] }) {
  const normalizedStatus = (currentStatus || 'submitted').toLowerCase().replace(' ', '_');
  const currentIndex = statuses.findIndex(s => s.id === normalizedStatus);

  // Map history events by normalized status
  const historyMap = {};
  if (Array.isArray(history)) {
    history.forEach(h => {
      const k = (h.status || '').toLowerCase().replace(' ', '_');
      historyMap[k] = h;
    });
  }

  return (
    <div className="relative py-4">
      <div className="absolute left-3 top-6 bottom-6 w-0.5 bg-border-default"></div>
      
      <div className="space-y-6 relative">
        {statuses.map((status, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          const hist = historyMap[status.id];
          
          return (
            <div key={status.id} className="flex gap-4 items-start relative">
              <div className={clsx(
                "relative z-10 w-6 h-6 rounded-full flex items-center justify-center bg-surface border",
                isCompleted ? "border-primary text-primary" : isCurrent ? "border-warning text-warning" : "border-default text-muted"
              )}>
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 bg-surface" />
                ) : isCurrent ? (
                  <motion.div 
                    animate={{ scale: [1, 1.2, 1] }} 
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    <Clock className="w-5 h-5 bg-surface" />
                  </motion.div>
                ) : (
                  <Circle className="w-4 h-4 bg-surface" />
                )}
              </div>
              
              <div className="flex-1 pt-0.5">
                <div className="flex items-baseline justify-between">
                  <h4 className={clsx(
                    "font-medium text-sm",
                    (isCompleted || isCurrent) ? "text-main font-semibold" : "text-disabled"
                  )}>
                    {status.label}
                  </h4>
                  {hist?.timestamp && (
                    <span className="text-xs text-disabled">
                      {new Date(hist.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                </div>
                {hist?.note && (
                  <p className="text-xs text-muted mt-0.5">{hist.note}</p>
                )}
                {isCurrent && status.id === 'resolved' && (
                  <span className="inline-flex items-center gap-1 text-xs text-ai font-medium mt-1 bg-ai/10 px-2 py-0.5 rounded-full border border-ai/20">
                    <CheckCircle2 className="w-3 h-3 text-primary" />
                    AI verified: issue resolved
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
