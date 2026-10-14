import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Camera, MapPin, Send, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import LandingDemoCard from '../components/LandingDemoCard';

export default function Landing() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-20 pb-20">
      <section className="relative pt-10 pb-16 lg:pt-20 lg:pb-24 overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-xl text-left"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-subtle border border-default text-muted text-sm font-medium mb-8">
              <span className="w-2 h-2 rounded-full bg-success"></span>
              {t('landing.badge')}
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-display font-semibold tracking-tight mb-6 text-main leading-tight">
              {t('landing.title_1')} <span className="text-primary block mt-2">{t('landing.title_2')}</span> <span className="block mt-2">{t('landing.title_3')}</span>
            </h1>
            <p className="text-lg text-muted mb-10 font-body leading-relaxed">
              {t('landing.subtitle')}
            </p>
            <div className="flex flex-wrap gap-4">
              <Link to="/report" className="btn-primary text-lg inline-flex items-center gap-2 shadow-md py-3.5 px-8">
                <Camera className="w-5 h-5" />
                {t('landing.btn_report')}
              </Link>
              <Link to="/track" className="btn-secondary text-lg inline-flex items-center gap-2 py-3.5 px-8">
                Track Status
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="relative lg:h-[530px] bg-subtle/70 rounded-xl border border-default/90 shadow-sm overflow-hidden flex items-center justify-center p-4 sm:p-8"
          >
            {/* Subtle background texture */}
            <div 
              className="absolute inset-0 bg-surface" 
              style={{
                backgroundImage: 'radial-gradient(#cbd5e1 1.2px, transparent 1.2px)',
                backgroundSize: '24px 24px'
              }}
            />
            
            {/* Live indicator badge */}
            <div className="absolute top-4 right-4 text-[11px] font-mono font-medium text-muted bg-surface/95 border border-default px-2.5 py-1 rounded shadow-xs flex items-center gap-1.5 z-20">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live AI Preview</span>
            </div>

            {/* Alive Animated Demo Card */}
            <LandingDemoCard />
          </motion.div>
        </div>
      </section>

      <section className="civic-card py-10 px-8 grid grid-cols-1 md:grid-cols-3 gap-8 text-center md:text-left divide-y md:divide-y-0 md:divide-x divide-default">
        <div className="md:px-8">
          <div className="text-4xl lg:text-5xl font-display font-bold text-main mb-2">{t('landing.stats_filed')}</div>
          <div className="text-disabled text-sm font-medium">{t('landing.stats_filed_label', 'Reports Filed in UP')}</div>
        </div>
        <div className="pt-8 md:pt-0 md:px-8">
          <div className="text-4xl lg:text-5xl font-display font-bold text-primary mb-2">{t('landing.stats_resolved')}</div>
          <div className="text-disabled text-sm font-medium">{t('landing.stats_resolved_label', 'Issues Fixed')}</div>
        </div>
        <div className="pt-8 md:pt-0 md:px-8">
          <div className="text-4xl lg:text-5xl font-display font-bold text-accent mb-2">{t('landing.stats_time')}</div>
          <div className="text-disabled text-sm font-medium">{t('landing.stats_time_label', 'Avg. Resolution Time')}</div>
        </div>
      </section>

      <section className="flex flex-col gap-12 max-w-5xl mx-auto w-full">
        <div className="text-center mb-4">
          <h2 className="text-3xl md:text-4xl text-main font-bold mb-4">{t('landing.how_title')}</h2>
          <div className="w-16 h-1 bg-primary mx-auto rounded"></div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-16 relative">
          {[
            { icon: Camera, title: t('landing.step1_title'), desc: t('landing.step1_desc') },
            { icon: MapPin, title: t('landing.step2_title'), desc: t('landing.step2_desc') },
            { icon: Send, title: t('landing.step3_title'), desc: t('landing.step3_desc') },
            { icon: CheckCircle, title: t('landing.step4_title'), desc: t('landing.step4_desc') }
          ].map((step, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="flex gap-6"
            >
              <div className="shrink-0 w-16 h-16 rounded-full bg-subtle border-2 border-primary flex items-center justify-center text-primary shadow-sm">
                <step.icon className="w-7 h-7" />
              </div>
              <div className="pt-2">
                <h3 className="text-xl font-bold text-main mb-2">{step.title}</h3>
                <p className="text-muted leading-relaxed">{step.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
