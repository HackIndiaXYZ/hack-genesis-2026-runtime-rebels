const fs = require('fs');
const path = require('path');

const walkSync = (dir, filelist = []) => {
  fs.readdirSync(dir).forEach(file => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory()) {
      if (file !== 'node_modules') filelist = walkSync(filePath, filelist);
    } else {
      if (filePath.endsWith('.jsx')) {
        filelist.push(filePath);
      }
    }
  });
  return filelist;
};

const replacements = [
  { regex: /\bbg-white\b/g, replace: 'bg-surface' },
  { regex: /\bbg-slate-50\b/g, replace: 'bg-subtle' },
  { regex: /\bbg-slate-100\b/g, replace: 'bg-subtle' },
  { regex: /\bbg-slate-200\b/g, replace: 'bg-default' },
  { regex: /\bbg-slate-900\b/g, replace: 'bg-main' },
  
  { regex: /\btext-slate-900\b/g, replace: 'text-main' },
  { regex: /\btext-slate-800\b/g, replace: 'text-main' },
  { regex: /\btext-slate-700\b/g, replace: 'text-muted' },
  { regex: /\btext-slate-600\b/g, replace: 'text-muted' },
  { regex: /\btext-slate-500\b/g, replace: 'text-disabled' },
  { regex: /\btext-slate-400\b/g, replace: 'text-disabled' },
  { regex: /\btext-slate-300\b/g, replace: 'text-disabled' },
  
  { regex: /\bborder-slate-100\b/g, replace: 'border-default' },
  { regex: /\bborder-slate-200\b/g, replace: 'border-default' },
  { regex: /\bborder-slate-300\b/g, replace: 'border-default' },
  { regex: /\bborder-slate-400\b/g, replace: 'border-default' },
  
  { regex: /\bbg-red-500\/10\b/g, replace: 'bg-critical/10' },
  { regex: /\btext-red-500\b/g, replace: 'text-critical' },
  { regex: /\bborder-red-500\/50\b/g, replace: 'border-critical/50' },
];

const files = walkSync(path.join(__dirname, 'src'));

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;
  
  replacements.forEach(({regex, replace}) => {
    content = content.replace(regex, replace);
  });
  
  if (original !== content) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('Updated:', file);
  }
});
