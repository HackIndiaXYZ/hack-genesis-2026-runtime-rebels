const fs = require('fs');

let content = fs.readFileSync('src/pages/Report.jsx', 'utf8');

if (!content.includes("useTranslation")) {
  content = content.replace("import React, { useState, useRef } from 'react';", "import React, { useState, useRef, useEffect } from 'react';\nimport { useTranslation } from 'react-i18next';");
}

if (!content.includes("const { t, i18n } = useTranslation();")) {
  content = content.replace("export default function Report() {", "export default function Report() {\n  const { t, i18n } = useTranslation();");
}

content = content.replace(/<h2 className="text-3xl font-display font-bold text-slate-900 mb-2">Report an Issue<\/h2>/, '<h2 className="text-3xl font-display font-bold text-slate-900 mb-2">{t("report.title")}</h2>');
content = content.replace(/<p className="text-slate-600">Upload a photo of a public issue.*?<\/p>/, '<p className="text-slate-600">{t("report.subtitle")}</p>');
content = content.replace(/<h3 className="text-xl">Evidence<\/h3>/, '<h3 className="text-xl">{t("report.evidence")}</h3>');
content = content.replace(/<span className="font-medium">Click to upload photo<\/span>/, '<span className="font-medium">{t("report.click_upload")}</span>');
content = content.replace(/<span className="text-sm mt-1">or drag and drop<\/span>/, '<span className="text-sm mt-1">{t("report.drag_drop")}</span>');
content = content.replace(/Detecting location\.\.\./g, '{t("report.btn_detecting")}');
content = content.replace(/Analyzing with AI\.\.\./g, '{t("report.btn_analyzing")}');
content = content.replace(/"Analysis Complete"/g, 't("report.btn_complete")');
content = content.replace(/"Analyze Photo"/g, 't("report.btn_analyze")');
content = content.replace(/>Analysis failed:</g, '>{t("report.analysis_failed")}<');
content = content.replace(/<p>Upload a photo and analyze it to see AI extracted details here\.<\/p>/, '<p>{t("report.upload_placeholder")}</p>');
content = content.replace(/Location<\/div>/, '{t("report.location")}</div>');
content = content.replace(/Pin exact location<\/button>/, '{t("report.pin_exact")}</button>');
content = content.replace(/Click anywhere on the map to place the pin precisely\./, '{t("report.pin_instruction")}');
content = content.replace(/placeholder="Search address\.\.\."/, 'placeholder={t("report.search_placeholder")}');
content = content.replace(/'Loading address\.\.\.'/g, 't("report.loading_address")');
content = content.replace(/AI Generated Complaint<\/span>/, '{t("report.ai_generated")}</span>');
content = content.replace(/Submit Complaint<\/button>/g, '{t("report.btn_submit")}</button>');
content = content.replace(/>Submit Complaint<\/>/g, '>{t("report.btn_submit")}</>');
content = content.replace(/"Submitting\.\.\."/g, 't("report.btn_submitting")');

const effect = `
  useEffect(() => {
    if (analysisResult && analysisResult.location && analysisResult.location.address !== t('report.loading_address')) {
      const texts = {
        en: \`A \${analysisResult.category} has been detected near \${analysisResult.location.address}. It poses a significant risk to vehicles and pedestrians.\`,
        hi: \`\${analysisResult.location.address} के पास एक \${analysisResult.category} पाया गया है। यह वाहनों और पैदल चलने वालों के लिए एक महत्वपूर्ण जोखिम प्रस्तुत करता है।\`
      };
      const text = texts[i18n.language] || texts.en;
      setAnalysisResult(prev => ({ ...prev, complaint_text: text }));
    }
  }, [i18n.language]);
`;

content = content.replace("const handleAnalyze = async () => {", effect + "\n  const handleAnalyze = async () => {");

content = content.replace(/mockResult\.complaint_text = [\s\S]*?;/, `const texts = {
      en: \`A \${mockResult.category} has been detected near \${address}. It poses a significant risk to vehicles and pedestrians.\`,
      hi: \`\${address} के पास एक \${mockResult.category} पाया गया है। यह वाहनों और पैदल चलने वालों के लिए एक महत्वपूर्ण जोखिम प्रस्तुत करता है।\`
    };
    mockResult.complaint_text = texts[i18n.language] || texts.en;`);

content = content.replace(/complaint_text: \`A \$\{prev.category\}[\s\S]*?\`/g, `complaint_text: (i18n.language === 'hi') ? \`\${address} के पास एक \${prev.category} पाया गया है। यह वाहनों और पैदल चलने वालों के लिए एक महत्वपूर्ण जोखिम प्रस्तुत करता है।\` : \`A \${prev.category} has been detected near \${address}. It poses a significant risk to vehicles and pedestrians.\``);

fs.writeFileSync('src/pages/Report.jsx', content);
