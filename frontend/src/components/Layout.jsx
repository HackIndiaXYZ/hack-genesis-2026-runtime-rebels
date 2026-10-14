import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Map as MapIcon, PlusCircle, Activity, Menu, X, Globe, Sun, Moon } from 'lucide-react';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';
import Footer from './Footer';

const languages = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'हिन्दी' },
  { code: 'ta', name: 'தமிழ்' },
  { code: 'te', name: 'తెలుగు' },
  { code: 'bn', name: 'বাংলা' },
  { code: 'mr', name: 'मराठी' },
  { code: 'kn', name: 'ಕನ್ನಡ' },
  { code: 'gu', name: 'ગુજરાતી' },
];

export default function Layout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t, i18n } = useTranslation();

  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const navItems = [
    { path: '/', label: t('nav.home'), icon: Activity },
    { path: '/report', label: t('nav.report'), icon: PlusCircle },
    { path: '/track', label: t('nav.track'), icon: Activity },
    { path: '/map', label: t('nav.map'), icon: MapIcon },
    { path: '/admin', label: t('nav.dashboard'), icon: LayoutDashboard },
  ];

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-background">
      <header className="sticky top-0 z-50 bg-surface border-b border-default shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-primary flex items-center justify-center shadow-sm">
                <Activity className="text-white w-5 h-5" />
              </div>
              <span className="font-display font-bold text-xl tracking-tight text-main">CivicFix</span>
            </Link>
            
            <div className="flex items-center gap-4 lg:gap-6">
              <nav className="hidden md:flex gap-4 lg:gap-6">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={clsx(
                        "flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary",
                        isActive ? "text-primary font-semibold" : "text-muted"
                      )}
                    >
                      <item.icon className="w-4 h-4" />
                      {item.label}
                    </Link>
                  )
                })}
              </nav>

              <div className="flex items-center gap-4 border-l border-default pl-4 lg:pl-6">
                <button 
                  onClick={toggleTheme} 
                  className="text-muted hover:text-primary transition-colors p-1.5 rounded-full hover:bg-subtle"
                  aria-label="Toggle theme"
                >
                  {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </button>

                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-disabled hidden sm:block" />
                  <select 
                    className="bg-transparent text-sm font-medium text-muted focus:outline-none cursor-pointer"
                    value={i18n.language}
                    onChange={(e) => i18n.changeLanguage(e.target.value)}
                  >
                    {languages.map(lang => (
                      <option key={lang.code} value={lang.code}>{lang.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <button className="md:hidden text-muted hover:text-primary ml-2" onClick={() => setMobileOpen(!mobileOpen)}>
                {mobileOpen ? <X /> : <Menu />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {mobileOpen && (
        <div className="md:hidden bg-surface absolute top-16 left-0 right-0 z-40 border-b border-default shadow-md p-4 flex flex-col gap-2">
          {navItems.map((item) => {
             const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
             return (
             <Link
              key={item.path}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              className={clsx("flex items-center gap-3 font-medium p-3 rounded hover:bg-subtle",
                 isActive ? "text-primary bg-subtle" : "text-muted"
              )}
            >
              <item.icon className={clsx("w-5 h-5", isActive ? "text-primary" : "text-disabled")} />
              {item.label}
            </Link>
          )})}
        </div>
      )}

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
