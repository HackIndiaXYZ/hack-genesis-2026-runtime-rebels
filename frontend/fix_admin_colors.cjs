const fs = require('fs');
let c = fs.readFileSync('src/pages/Admin.jsx', 'utf8');
c = c.replace(/stroke="#64748b"/g, 'stroke="var(--color-text-disabled)"');
c = c.replace(/fill: '#94a3b8'/g, "fill: 'var(--color-text-muted)'");
c = c.replace(/cursor={{ fill: '#1e293b' }}/g, "cursor={{ fill: 'var(--color-subtle)' }}");
c = c.replace(/backgroundColor: '#0f172a'/g, "backgroundColor: 'var(--color-surface)'");
c = c.replace(/borderColor: '#334155'/g, "borderColor: 'var(--color-border-default)'");
c = c.replace(/fill="#00E5C3"/g, 'fill="var(--color-primary)"');
fs.writeFileSync('src/pages/Admin.jsx', c);
