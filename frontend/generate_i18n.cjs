const fs = require('fs');
const path = require('path');

const localesDir = path.join(__dirname, 'src', 'locales');
if (!fs.existsSync(localesDir)) fs.mkdirSync(localesDir, {recursive: true});

const en = {
  landing: {
    badge: "Municipal Corporation Portal",
    title_1: "See it.",
    title_2: "Snap it.",
    title_3: "Fix it.",
    subtitle: "Help keep our city clean and safe. Report civic issues like potholes and broken streetlights directly to the municipal team. We'll take a look and route it to the right department.",
    btn_report: "Report an Issue",
    stats_filed: "Reports Filed",
    stats_resolved: "Issues Resolved",
    stats_time: "Avg. Resolution Time",
    how_title: "How it works",
    step1_title: "1. Upload",
    step1_desc: "Take a photo of the problem on the street.",
    step2_title: "2. Locate",
    step2_desc: "Pinpoint the exact location on the map.",
    step3_title: "3. Auto-Route",
    step3_desc: "We automatically route it to the right officials.",
    step4_title: "4. Resolve",
    step4_desc: "Track the status until it's fixed."
  },
  report: {
    title: "Report an Issue",
    subtitle: "Upload a photo of a public issue. Our system will analyze it, extract details, and route it instantly.",
    evidence: "Evidence",
    click_upload: "Click to upload photo",
    drag_drop: "or drag and drop",
    btn_analyze: "Analyze Photo",
    btn_detecting: "Detecting location...",
    btn_analyzing: "Processing image...",
    btn_complete: "Analysis Complete",
    analysis_failed: "Analysis failed:",
    upload_placeholder: "Upload a photo and analyze it to see extracted details here.",
    location: "Location",
    pin_exact: "Pin exact location",
    pin_instruction: "Click anywhere on the map to place the pin precisely.",
    search_placeholder: "Search address...",
    loading_address: "Loading address...",
    ai_generated: "Generated Complaint",
    btn_submit: "Submit Complaint",
    btn_submitting: "Submitting..."
  },
  nav: {
    home: "Home",
    report: "Report Issue",
    track: "Track",
    map: "City Map",
    dashboard: "Dashboard"
  }
};

const hi = {
  landing: {
    badge: "नगर निगम पोर्टल",
    title_1: "देखें।",
    title_2: "फोटो लें।",
    title_3: "सुधारें।",
    subtitle: "हमारे शहर को स्वच्छ और सुरक्षित रखने में मदद करें। गड्ढों और टूटी स्ट्रीटलाइट जैसी नागरिक समस्याओं की रिपोर्ट सीधे नगर निगम टीम को दें। हम इसकी जांच करेंगे और इसे सही विभाग को भेजेंगे।",
    btn_report: "समस्या की रिपोर्ट करें",
    stats_filed: "दर्ज की गई शिकायतें",
    stats_resolved: "सुलझाई गई समस्याएं",
    stats_time: "औसत समाधान समय",
    how_title: "यह कैसे काम करता है",
    step1_title: "1. अपलोड करें",
    step1_desc: "सड़क पर समस्या की एक फोटो लें।",
    step2_title: "2. स्थान खोजें",
    step2_desc: "नक्शे पर सटीक स्थान पिन करें।",
    step3_title: "3. ऑटो-रूट",
    step3_desc: "हम इसे स्वचालित रूप से सही अधिकारियों को भेजते हैं।",
    step4_title: "4. समाधान",
    step4_desc: "समस्या ठीक होने तक स्थिति को ट्रैक करें।"
  },
  report: {
    title: "समस्या की रिपोर्ट करें",
    subtitle: "सार्वजनिक समस्या की फोटो अपलोड करें। हमारा सिस्टम इसका विश्लेषण करेगा और इसे तुरंत संबंधित विभाग को भेजेगा।",
    evidence: "प्रमाण",
    click_upload: "फोटो अपलोड करने के लिए क्लिक करें",
    drag_drop: "या ड्रैग और ड्रॉप करें",
    btn_analyze: "फोटो का विश्लेषण करें",
    btn_detecting: "स्थान का पता लगाया जा रहा है...",
    btn_analyzing: "विश्लेषण किया जा रहा है...",
    btn_complete: "विश्लेषण पूरा हुआ",
    analysis_failed: "विश्लेषण विफल रहा:",
    upload_placeholder: "एक फोटो अपलोड करें और यहां निकाले गए विवरण देखने के लिए इसका विश्लेषण करें।",
    location: "स्थान",
    pin_exact: "सटीक स्थान पिन करें",
    pin_instruction: "पिन को ठीक से लगाने के लिए नक्शे पर कहीं भी क्लिक करें।",
    search_placeholder: "पता खोजें...",
    loading_address: "पता लोड हो रहा है...",
    ai_generated: "स्वचालित शिकायत",
    btn_submit: "शिकायत दर्ज करें",
    btn_submitting: "दर्ज किया जा रहा है..."
  },
  nav: {
    home: "होम",
    report: "रिपोर्ट करें",
    track: "ट्रैक करें",
    map: "शहर का नक्शा",
    dashboard: "डैशबोर्ड"
  }
};

const languages = ['ta', 'te', 'bn', 'mr', 'kn', 'gu'];

fs.writeFileSync(path.join(localesDir, 'en.json'), JSON.stringify(en, null, 2));
fs.writeFileSync(path.join(localesDir, 'hi.json'), JSON.stringify(hi, null, 2));

languages.forEach(lang => {
  fs.writeFileSync(path.join(localesDir, `${lang}.json`), JSON.stringify(en, null, 2));
});

const i18nCode = `import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import hi from './locales/hi.json';
import ta from './locales/ta.json';
import te from './locales/te.json';
import bn from './locales/bn.json';
import mr from './locales/mr.json';
import kn from './locales/kn.json';
import gu from './locales/gu.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
      ta: { translation: ta },
      te: { translation: te },
      bn: { translation: bn },
      mr: { translation: mr },
      kn: { translation: kn },
      gu: { translation: gu },
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    }
  });

export default i18n;`;

fs.writeFileSync(path.join(__dirname, 'src', 'i18n.js'), i18nCode);
