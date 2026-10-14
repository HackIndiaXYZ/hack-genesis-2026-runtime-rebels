import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Send, Loader2, Clock, CheckCircle2 } from 'lucide-react';

export default function LandingDemoCard() {
  // Steps:
  // 0: Initial image load
  // 1: Analyzing with progress indicator
  // 2: Bounding box detection + Severity "High" tag
  // 3: Complaint text appears
  // 4: Routing to PWD with animated send icon
  const [step, setStep] = useState(0);

  useEffect(() => {
    let timeouts = [];

    const runSequence = () => {
      setStep(0);

      // Transition to Analyzing at 0.9s
      timeouts.push(setTimeout(() => setStep(1), 900));

      // Transition to Detection + Severity at 2.6s
      timeouts.push(setTimeout(() => setStep(2), 2600));

      // Transition to Complaint text at 4.4s
      timeouts.push(setTimeout(() => setStep(3), 4400));

      // Transition to Routing action at 6.0s
      timeouts.push(setTimeout(() => setStep(4), 6000));
    };

    runSequence();
    const interval = setInterval(runSequence, 9000);

    return () => {
      clearInterval(interval);
      timeouts.forEach(clearTimeout);
    };
  }, []);

  return (
    <div className="relative w-full max-w-sm sm:max-w-md bg-surface rounded-lg shadow-xl shadow-main/10 border border-default p-5 sm:p-6 flex flex-col gap-3.5 z-10 transition-shadow">
      {/* Header Info */}
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] font-mono font-bold text-disabled uppercase tracking-wider mb-0.5">
            CF-2026-00847
          </div>
          <div className="text-base font-bold text-main">
            Severe Pothole
          </div>
        </div>

        {/* Severity Badge: scales in at Step 2+ */}
        <div className="min-h-[28px] flex items-center">
          <AnimatePresence mode="wait">
            {step >= 2 ? (
              <motion.div
                key="high-severity"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ type: "spring", stiffness: 450, damping: 20 }}
                className="bg-warning/15 text-warning border border-warning/30 px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse" />
                High
              </motion.div>
            ) : (
              <motion.div
                key="detecting-severity"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="bg-subtle text-disabled border border-default px-2 py-0.5 rounded text-[11px] font-medium"
              >
                {step === 1 ? 'Evaluating...' : 'Pending'}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Pothole Photo Frame */}
      <div className="relative h-44 sm:h-48 w-full rounded overflow-hidden border border-default bg-main shadow-inner">
        <img
          src="/assets/demo_pothole.jpg"
          alt="Detected pothole on road"
          className="w-full h-full object-cover select-none"
        />

        {/* State 1: Analyzing indicator overlay */}
        <AnimatePresence>
          {step === 1 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="absolute inset-0 bg-main/35 backdrop-blur-[1px] flex flex-col justify-between p-3 pointer-events-none"
            >
              <div className="self-end bg-surface/95 backdrop-blur-sm border border-default text-main text-[11px] font-semibold px-2.5 py-1 rounded shadow-sm flex items-center gap-1.5">
                <Loader2 className="w-3 h-3 animate-spin text-primary" />
                <span>Analyzing image...</span>
              </div>
              <div className="w-full bg-slate-700/60 h-1.5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-accent"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 1.6, ease: "easeInOut" }}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* State 2+: YOLO Bounding Box Highlight */}
        <AnimatePresence>
          {step >= 2 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ duration: 0.35, ease: "easeOut" }}
              className="absolute top-[28%] left-[20%] w-[58%] h-[52%] border-2 border-accent rounded-sm shadow-[0_0_16px_rgba(192,86,33,0.45)] bg-accent/10 pointer-events-none"
            >
              {/* Tag Label */}
              <div className="absolute -top-5 left-[-2px] bg-accent text-white text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-t tracking-wider shadow-sm flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-surface animate-pulse" />
                pothole 94%
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Location Row */}
      <div className="flex items-center gap-2 text-sm text-muted font-medium">
        <MapPin className="w-4 h-4 text-accent shrink-0" />
        <span>Civil Lines, Kanpur, UP</span>
      </div>

      {/* Complaint Text Box */}
      <div className="min-h-[64px] bg-subtle p-3 rounded text-sm text-muted border border-default/80 flex items-center">
        <AnimatePresence mode="wait">
          {step >= 3 ? (
            <motion.p
              key="complaint-ready"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35 }}
              className="leading-relaxed"
            >
              "A large pothole has been detected near Civil Lines. It poses a significant risk to vehicles."
            </motion.p>
          ) : (
            <motion.p
              key="complaint-placeholder"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-disabled italic text-xs flex items-center gap-2"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Generating complaint draft...</span>
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* Routing Action Status */}
      <div className="min-h-[38px] flex items-center">
        <AnimatePresence mode="wait">
          {step >= 4 ? (
            <motion.div
              key="routed"
              initial={{ opacity: 0, y: 3 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="w-full py-2 bg-primary/10 text-primary border border-primary/20 rounded font-semibold text-sm flex items-center justify-center gap-2 shadow-xs"
            >
              <motion.div
                animate={{ x: [0, 3, 0] }}
                transition={{ repeat: Infinity, duration: 1.2 }}
              >
                <Send className="w-4 h-4 text-primary" />
              </motion.div>
              <span>Routing to PWD...</span>
            </motion.div>
          ) : (
            <motion.div
              key="waiting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full py-2 bg-subtle text-disabled rounded font-medium text-sm flex items-center justify-center gap-2"
            >
              <Clock className="w-3.5 h-3.5 text-disabled" />
              <span>Awaiting routing confirmation...</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
