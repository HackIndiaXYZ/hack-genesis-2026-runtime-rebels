import React, { useState, useEffect } from 'react';
import { getComplaints, getStats, updateComplaintStatus } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { BrainCircuit, TrendingUp, TrendingDown, Loader2, CheckCircle2, Key } from 'lucide-react';
import SeverityBadge from '../components/SeverityBadge';

export default function Admin() {
  const [complaints, setComplaints] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  const loadData = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [complaintsData, statsData] = await Promise.all([
        getComplaints({ limit: 50 }),
        getStats()
      ]);
      setComplaints(complaintsData || []);
      setStats(statsData || null);
    } catch (err) {
      console.error('Failed to load admin dashboard data:', err);
      setLoadError(err.message || 'Failed to connect to backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStatusChange = async (complaintId, newStatus) => {
    setUpdatingId(complaintId);
    try {
      const updated = await updateComplaintStatus(complaintId, newStatus, `Admin set status to ${newStatus}`);
      // Update local table
      setComplaints(prev => prev.map(c => c.complaint_id === complaintId ? { ...c, status: updated.status } : c));
      
      // Show toast
      setToastMsg(`Status for ${complaintId} updated to ${newStatus.replace('_', ' ')}`);
      setTimeout(() => setToastMsg(null), 3000);

      // Refresh stats
      getStats().then(setStats);
    } catch (err) {
      if (err.message && err.message.includes('401')) {
        const key = prompt('Admin Authorization Key required for status changes. Please enter passkey:');
        if (key && key.trim()) {
          sessionStorage.setItem('civicfix_admin_key', key.trim());
          // Retry status change with updated key
          setUpdatingId(null);
          return handleStatusChange(complaintId, newStatus);
        }
      }
      alert(`Failed to update status: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  const chartData = stats?.by_category
    ? Object.entries(stats.by_category).map(([name, value]) => ({ name, value }))
    : complaints.reduce((acc, c) => {
        const existing = acc.find(item => item.name === c.category);
        if (existing) existing.value++;
        else acc.push({ name: c.category, value: 1 });
        return acc;
      }, []);

  const hasAdminKey = typeof window !== 'undefined' && Boolean(sessionStorage.getItem('civicfix_admin_key'));

  return (
    <div className="space-y-8">
      {toastMsg && (
        <div className="fixed top-5 right-5 z-50 bg-primary text-black font-semibold px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-5 h-5" />
          <span>{toastMsg}</span>
        </div>
      )}

      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold mb-2">City Dashboard</h1>
          <p className="text-disabled">Real-time civic operations overview across Kanpur & Varanasi wards.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              const cur = sessionStorage.getItem('civicfix_admin_key') || '';
              const key = prompt('Enter Admin Passkey (stored in session memory only):', cur);
              if (key !== null) {
                if (key.trim()) {
                  sessionStorage.setItem('civicfix_admin_key', key.trim());
                } else {
                  sessionStorage.removeItem('civicfix_admin_key');
                }
                setToastMsg('Admin key updated for this session.');
                setTimeout(() => setToastMsg(null), 3000);
              }
            }}
            className="btn-secondary text-sm py-2 px-3.5 flex items-center gap-1.5"
            title="Configure Admin Key for privileged endpoints"
          >
            <Key className="w-4 h-4 text-muted" />
            <span>{hasAdminKey ? 'Admin Key Set' : 'Set Admin Key'}</span>
          </button>

          <button 
            onClick={loadData} 
            disabled={isLoading}
            className="btn-secondary text-sm py-2 px-4 flex items-center gap-2"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            Refresh Metrics
          </button>
        </div>
      </div>

      {loadError && (
        <div className="p-4 rounded-lg bg-critical/10 border border-critical/30 text-critical text-sm flex items-center justify-between">
          <span>Failed to load live city metrics: {loadError}</span>
          <button onClick={loadData} className="btn-secondary text-xs py-1.5 px-3">Retry</button>
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Total Complaints', value: stats ? stats.total : complaints.length, trend: '+12%', up: true },
          { label: 'Resolved', value: stats ? stats.resolved : complaints.filter(c => c.status === 'resolved').length, trend: '+8%', up: true },
          { label: 'Critical Issues', value: stats ? stats.critical : complaints.filter(c => c.severity === 'critical').length, trend: '-2%', up: false },
          { label: 'Avg SLA Time', value: stats ? `${stats.avg_resolution_hours}h` : '37h', trend: '-5h', up: true }
        ].map((kpi, i) => (
          <div key={i} className="civic-card p-6 border-l-4 border-l-primary">
            <div className="text-sm text-disabled uppercase tracking-wider mb-2 font-semibold">{kpi.label}</div>
            <div className="text-3xl font-display font-bold text-main mb-2">
              {isLoading ? '...' : kpi.value}
            </div>
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
          <h3 className="text-xl mb-6 font-display font-semibold">Issues by Category</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
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
            <h3 className="text-xl text-main font-display font-semibold">AI Insights</h3>
          </div>
          <div className="space-y-4">
            <div className="bg-main/50 p-4 rounded-lg border border-default">
              <span className="text-critical font-semibold block mb-1">Geographic Cluster</span>
              <p className="text-sm text-muted">High pothole frequency detected along VIP Road / Civil Lines (Kanpur). Recommend road re-tarring tender.</p>
            </div>
            <div className="bg-main/50 p-4 rounded-lg border border-default">
              <span className="text-warning font-semibold block mb-1">Critical Hazard Warning</span>
              <p className="text-sm text-muted">Uncovered manhole complaints in Kakadeo & Lanka BHU route escalated to Emergency Tier 1.</p>
            </div>
            <div className="bg-main/50 p-4 rounded-lg border border-default">
              <span className="text-primary font-semibold block mb-1">Resolution Velocity</span>
              <p className="text-sm text-muted">Municipal Sanitation team closed 4 waste reports in Varanasi within 18 hours average.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="civic-card overflow-hidden">
        <div className="p-6 border-b border-default flex justify-between items-center">
          <h3 className="text-xl font-display font-semibold">Recent Complaints ({complaints.length})</h3>
          <span className="text-xs text-muted">Select dropdown to live-update status</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-subtle text-disabled text-sm">
              <tr>
                <th className="px-6 py-4 font-medium">ID</th>
                <th className="px-6 py-4 font-medium">Category</th>
                <th className="px-6 py-4 font-medium">Severity</th>
                <th className="px-6 py-4 font-medium">Department</th>
                <th className="px-6 py-4 font-medium">Status & Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-default">
              {complaints.slice(0, 15).map(c => (
                <tr key={c.complaint_id} className="hover:bg-subtle/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-sm font-bold text-main">{c.complaint_id}</td>
                  <td className="px-6 py-4 capitalize text-sm">{c.category}</td>
                  <td className="px-6 py-4"><SeverityBadge level={c.severity} /></td>
                  <td className="px-6 py-4 text-sm text-muted">{c.department}</td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex items-center gap-2">
                      <select
                        className="bg-surface border border-default rounded px-2.5 py-1 text-xs text-main font-medium focus:outline-none focus:border-primary/50 capitalize"
                        value={c.status?.toLowerCase()}
                        disabled={updatingId === c.complaint_id}
                        onChange={(e) => handleStatusChange(c.complaint_id, e.target.value)}
                      >
                        <option value="submitted">Submitted</option>
                        <option value="assigned">Assigned</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="rejected">Rejected</option>
                      </select>
                      {updatingId === c.complaint_id && (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                      )}
                    </div>
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
