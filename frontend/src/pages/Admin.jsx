import React, { useState, useEffect } from 'react';
import { getComplaints } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { BrainCircuit, TrendingUp, TrendingDown } from 'lucide-react';
import SeverityBadge from '../components/SeverityBadge';

export default function Admin() {
  const [complaints, setComplaints] = useState([]);

  useEffect(() => {
    getComplaints().then(setComplaints);
  }, []);

  const stats = {
    total: complaints.length,
    resolved: complaints.filter(c => c.status === 'resolved').length,
    critical: complaints.filter(c => c.severity === 'critical').length,
  };

  const categoryData = complaints.reduce((acc, c) => {
    const existing = acc.find(item => item.name === c.category);
    if (existing) existing.value++;
    else acc.push({ name: c.category, value: 1 });
    return acc;
  }, []);

  const COLORS = ['#00E5C3', '#FFB020', '#FF4D6A', '#8B7CFF', '#3B82F6', '#EC4899'];

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold mb-2">City Dashboard</h1>
          <p className="text-disabled">Overview of civic issues across all wards.</p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Total Complaints', value: stats.total, trend: '+12%', up: true },
          { label: 'Resolved (7d)', value: stats.resolved, trend: '+8%', up: true },
          { label: 'Critical Issues', value: stats.critical, trend: '-2%', up: false },
          { label: 'Avg Resolution Time', value: '42h', trend: '-5h', up: true }
        ].map((kpi, i) => (
          <div key={i} className="civic-card p-6 border-l-4 border-l-primary">
            <div className="text-sm text-disabled uppercase tracking-wider mb-2">{kpi.label}</div>
            <div className="text-3xl font-display font-bold text-main mb-2">{kpi.value}</div>
            <div className={`flex items-center gap-1 text-sm ${kpi.up ? 'text-primary' : 'text-critical'}`}>
              {kpi.up ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
              {kpi.trend} from last week
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Charts */}
        <div className="lg:col-span-2 civic-card p-6">
          <h3 className="text-xl mb-6">Issues by Category</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData}>
                <XAxis dataKey="name" stroke="var(--color-text-disabled)" tick={{ fill: 'var(--color-text-muted)' }} />
                <YAxis stroke="var(--color-text-disabled)" tick={{ fill: 'var(--color-text-muted)' }} />
                <Tooltip cursor={{ fill: 'var(--color-subtle)' }} contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border-default)' }} />
                <Bar dataKey="value" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Insights */}
        <div className="civic-card p-6 bg-gradient-to-br from-surface to-ai/5 border-ai/20">
          <div className="flex items-center gap-2 mb-6">
            <BrainCircuit className="w-6 h-6 text-ai" />
            <h3 className="text-xl text-main">AI Insights</h3>
          </div>
          <div className="space-y-4">
            <div className="bg-main/50 p-4 rounded-lg border border-default">
              <span className="text-critical font-semibold block mb-1">Anomaly Detected</span>
              <p className="text-sm text-muted">Pothole reports are up 45% in Ward 5 following recent heavy rains. Recommend dispatching road maintenance team.</p>
            </div>
            <div className="bg-main/50 p-4 rounded-lg border border-default">
              <span className="text-warning font-semibold block mb-1">Resource Reallocation</span>
              <p className="text-sm text-muted">Sanitation team has lower workload this week. Consider reassigning to backlog in Ward 2.</p>
            </div>
            <div className="bg-main/50 p-4 rounded-lg border border-default">
              <span className="text-primary font-semibold block mb-1">Positive Trend</span>
              <p className="text-sm text-muted">Streetlight repair resolution time decreased by 12 hours since last month.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="civic-card overflow-hidden">
        <div className="p-6 border-b border-default">
          <h3 className="text-xl">Recent Complaints</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-subtle text-disabled text-sm">
              <tr>
                <th className="px-6 py-4 font-medium">ID</th>
                <th className="px-6 py-4 font-medium">Category</th>
                <th className="px-6 py-4 font-medium">Severity</th>
                <th className="px-6 py-4 font-medium">Department</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-default">
              {complaints.slice(0, 10).map(c => (
                <tr key={c.complaint_id} className="hover:bg-subtle transition-colors">
                  <td className="px-6 py-4 font-mono text-sm">{c.complaint_id}</td>
                  <td className="px-6 py-4 capitalize">{c.category}</td>
                  <td className="px-6 py-4"><SeverityBadge level={c.severity} /></td>
                  <td className="px-6 py-4 text-sm text-muted">{c.department}</td>
                  <td className="px-6 py-4 capitalize text-sm">
                    <span className={`px-2 py-1 rounded-md border ${
                      c.status === 'resolved' ? 'bg-primary/10 border-primary/20 text-primary' : 
                      c.status === 'in progress' ? 'bg-warning/10 border-warning/20 text-warning' :
                      'bg-slate-700 border-slate-600'
                    }`}>
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
