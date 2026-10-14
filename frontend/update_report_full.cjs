const fs = require('fs');

let content = fs.readFileSync('src/pages/Report.jsx', 'utf8');

// The replacement for the detectLocation block
const detectLocationTexts = `const getComplaintText = (lang, category, address) => {
      const texts = {
        en: \`A \${category} has been detected near \${address}. It poses a significant risk to vehicles and pedestrians.\`,
        hi: \`\${address} के पास एक \${category} पाया गया है। यह वाहनों आणि पादचाऱ्यांसाठी एक महत्त्वपूर्ण जोखिम प्रस्तुत करता है।\`,
        ta: \`\${address} அருகில் ஒரு \${category} கண்டறியப்பட்டுள்ளது. இது வாகனங்கள் மற்றும் பாதசாரிகளுக்கு பெரும் ஆபத்தை ஏற்படுத்துகிறது.\`,
        te: \`\${address} సమీపంలో ఒక \${category} కనుగొనబడింది. ఇది వాహనాలకు మరియు పాదచారులకు తీవ్రమైన ప్రమాదాన్ని కలిగిస్తుంది.\`,
        bn: \`\${address} এর কাছে একটি \${category} শনাক্ত করা হয়েছে। এটি যানবাহন এবং পথচারীদের জন্য একটি উল্লেখযোগ্য ঝুঁকি তৈরি করে।\`,
        mr: \`\${address} जवळ एक \${category} आढळला आहे. यामुळे वाहने आणि पादचाऱ्यांसाठी मोठा धोका निर्माण झाला आहे.\`,
        kn: \`\${address} ಬಳಿ ಒಂದು \${category} ಪತ್ತೆಯಾಗಿದೆ. ಇದು ವಾಹನಗಳಿಗೆ ಮತ್ತು ಪಾದಚಾರಿಗಳಿಗೆ ಗಮನಾರ್ಹ ಅಪಾಯವನ್ನು ಉಂಟುಮಾಡುತ್ತದೆ.\`,
        gu: \`\${address} પાસે એક \${category} મળી આવ્યું છે. આ વાહનો અને રાહદારીઓ માટે નોંધપાત્ર જોખમ ઊભું કરે છે.\`
      };
      return texts[lang] || texts.en;
    };`;

content = content.replace(/const texts = {[\s\S]*?texts\[i18n\.language\] \|\| texts\.en;/m, `mockResult.complaint_text = getComplaintText(i18n.language, mockResult.category, address);`);

content = content.replace(/const texts = {[\s\S]*?texts\[i18n\.language\] \|\| texts\.en;/m, `const text = getComplaintText(i18n.language, analysisResult.category, analysisResult.location.address);`);

content = content.replace(/complaint_text: \(i18n\.language[\s\S]*?pedestrians\.\`/m, `complaint_text: getComplaintText(i18n.language, prev.category, address)`);

// We need to inject getComplaintText somewhere at the top level or inside the component.
content = content.replace("export default function Report() {", `const getComplaintText = (lang, category, address) => {
  const texts = {
    en: \`A \${category} has been detected near \${address}. It poses a significant risk to vehicles and pedestrians.\`,
    hi: \`\${address} के पास एक \${category} पाया गया है। यह वाहनों और पैदल चलने वालों के लिए एक महत्वपूर्ण जोखिम प्रस्तुत करता है।\`,
    ta: \`\${address} அருகில் ஒரு \${category} கண்டறியப்பட்டுள்ளது. இது வாகனங்கள் மற்றும் பாதசாரிகளுக்கு பெரும் ஆபத்தை ஏற்படுத்துகிறது.\`,
    te: \`\${address} సమీపంలో ఒక \${category} కనుగొనబడింది. ఇది వాహనాలకు మరియు పాదచారులకు తీవ్రమైన ప్రమాదాన్ని కలిగిస్తుంది.\`,
    bn: \`\${address} এর কাছে একটি \${category} শনাক্ত করা হয়েছে। এটি যানবাহন এবং পথচারীদের জন্য একটি উল্লেখযোগ্য ঝুঁকি তৈরি করে।\`,
    mr: \`\${address} जवळ एक \${category} आढळला आहे. यामुळे वाहने आणि पादचाऱ्यांसाठी मोठा धोका निर्माण झाला आहे.\`,
    kn: \`\${address} ಬಳಿ ಒಂದು \${category} ಪತ್ತೆಯಾಗಿದೆ. ಇದು ವಾಹನಗಳಿಗೆ ಮತ್ತು ಪಾದಚಾರಿಗಳಿಗೆ ಗಮನಾರ್ಹ ಅಪಾಯವನ್ನು ಉಂಟುಮಾಡುತ್ತದೆ.\`,
    gu: \`\${address} પાસે એક \${category} મળી આવ્યું છે. આ વાહનો અને રાહદારીઓ માટે નોંધપાત્ર જોખમ ઊભું કરે છે.\`
  };
  return texts[lang] || texts.en;
};\n\nexport default function Report() {`);

fs.writeFileSync('src/pages/Report.jsx', content);
