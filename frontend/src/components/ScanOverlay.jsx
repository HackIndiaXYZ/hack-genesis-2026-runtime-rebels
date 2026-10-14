import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';

export default function ScanOverlay({ isScanning, onScanComplete }) {
  useEffect(() => {
    if (isScanning) {
      const timer2 = setTimeout(() => onScanComplete(), 2000); // reduced from 4s to 2s
      return () => clearTimeout(timer2);
    }
  }, [isScanning, onScanComplete]);

  if (!isScanning) return null;

  return (
    <div className="absolute inset-0 z-20 rounded flex flex-col items-center justify-center bg-surface/70 backdrop-blur-sm border border-default">
      <AnimatePresence>
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="flex flex-col items-center text-primary"
        >
          <Loader2 className="w-10 h-10 mb-3 animate-spin text-primary" />
          <span className="font-semibold text-sm text-main">Processing image...</span>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
