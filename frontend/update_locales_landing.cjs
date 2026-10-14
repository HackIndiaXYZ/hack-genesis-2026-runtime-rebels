const fs = require('fs');
const path = require('path');

const localesDir = path.join(__dirname, 'src', 'locales');

['en', 'hi', 'ta', 'te', 'bn', 'mr', 'kn', 'gu'].forEach(lang => {
  const file = path.join(localesDir, `${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));

  if (lang === 'en') {
    data.landing = {
      badge: "Uttar Pradesh Municipal Portal",
      title_1: "Snap a photo.",
      title_2: "Report it.",
      title_3: "Fixed.",
      subtitle: "Help keep our streets safe in Kanpur, Varanasi, and across UP. Snap a photo of the problem — we'll figure out what it is and send it to the right department.",
      btn_report: "Report an Issue",
      stats_filed: "14,892",
      stats_filed_label: "Reports Filed in UP",
      stats_resolved: "11,204",
      stats_resolved_label: "Issues Fixed",
      stats_time: "48h",
      stats_time_label: "Avg. Resolution Time",
      how_title: "How it works",
      step1_title: "1. Upload",
      step1_desc: "Take a quick photo of the pothole or broken light.",
      step2_title: "2. Locate",
      step2_desc: "Confirm the exact street location on the map.",
      step3_title: "3. Auto-Route",
      step3_desc: "Our system identifies the issue and routes it directly to the local ward officer.",
      step4_title: "4. Track",
      step4_desc: "Get updates right here until the job is done."
    };
  } else if (lang === 'hi') {
    data.landing = {
      badge: "उत्तर प्रदेश नगर निगम पोर्टल",
      title_1: "फोटो लें।",
      title_2: "रिपोर्ट करें।",
      title_3: "समाधान।",
      subtitle: "कानपुर, वाराणसी और पूरे यूपी में हमारी सड़कों को सुरक्षित रखने में मदद करें। समस्या की एक फोटो लें — हम पता लगाएंगे कि यह क्या है और इसे सही विभाग को भेजेंगे।",
      btn_report: "समस्या की रिपोर्ट करें",
      stats_filed: "14,892",
      stats_filed_label: "यूपी में दर्ज शिकायतें",
      stats_resolved: "11,204",
      stats_resolved_label: "सुलझाई गई समस्याएं",
      stats_time: "48h",
      stats_time_label: "औसत समाधान समय",
      how_title: "यह कैसे काम करता है",
      step1_title: "1. अपलोड करें",
      step1_desc: "गड्ढे या टूटी लाइट की तुरंत फोटो लें।",
      step2_title: "2. स्थान खोजें",
      step2_desc: "नक्शे पर सटीक गली या स्थान की पुष्टि करें।",
      step3_title: "3. ऑटो-रूट",
      step3_desc: "हमारा सिस्टम समस्या की पहचान करता है और इसे सीधे स्थानीय वार्ड अधिकारी को भेजता है।",
      step4_title: "4. ट्रैक करें",
      step4_desc: "काम पूरा होने तक यहीं अपडेट प्राप्त करें।"
    };
  } else {
    // For other languages just sync the structure (using English as fallback base for the new keys)
    data.landing = {
      ...data.landing, // keep old translations
      stats_filed: "14,892",
      stats_resolved: "11,204",
      stats_time: "48h",
    };
  }

  fs.writeFileSync(file, JSON.stringify(data, null, 2));
});
