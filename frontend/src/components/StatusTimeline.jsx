import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

const statuses = [
  { id: 'submitted', label: 'Submitted' },
  { id: 'assigned', label: 'Assigned' },
  { id: 'in progress', label: 'In Progress' },
  { id: 'resolved', label: 'Resolved' }
];

export default function StatusTimeline({ currentStatus }) {
  const currentIndex = statuses.findIndex(s => s.id === currentStatus.toLowerCase());

  return (
    <div className="relative py-4">
      <div className="absolute left-3 top-6 bottom-6 w-0.5 bg-slate-700"></div>
      
      <div className="space-y-6 relative">
        {statuses.map((status, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          
          return (
            <div key={status.id} className="flex gap-4 items-start relative">
              <div className={clsx(
                "relative z-10 w-6 h-6 rounded-full flex items-center justify-center bg-background",
                isCompleted ? "text-primary" : isCurrent ? "text-warning" : "text-muted"
              )}>
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 bg-background" />
                ) : isCurrent ? (
                  <motion.div 
                    animate={{ scale: [1, 1.2, 1] }} 
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    <Clock className="w-5 h-5 bg-background" />
                  </motion.div>
                ) : (
                  <Circle className="w-4 h-4 bg-background" />
                )}
              </div>
              
              <div className="flex-1 pt-0.5">
                <h4 className={clsx(
                  "font-medium",
                  (isCompleted || isCurrent) ? "text-slate-100" : "text-disabled"
                )}>
                  {status.label}
                </h4>
                {isCurrent && status.id === 'resolved' && (
                  <span className="inline-flex items-center gap-1 text-xs text-ai font-medium mt-1 bg-ai/10 px-2 py-0.5 rounded-full border border-ai/20">
                    <CheckCircle2 className="w-3 h-3" />
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
