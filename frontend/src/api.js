const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && window.location.origin.includes('localhost') ? 'http://localhost:8000' : '');

/**
 * Returns auth headers for admin actions if configured via environment or localStorage.
 */
export const getAdminHeaders = () => {
  const headers = { 'Content-Type': 'application/json' };
  const adminKey = typeof window !== 'undefined' 
    ? (sessionStorage.getItem('civicfix_admin_key') || localStorage.getItem('civicfix_admin_key'))
    : null;
  if (adminKey) {
    headers['X-Admin-Key'] = adminKey;
  }
  return headers;
};

/**
 * Resolve full URL for uploaded complaint images (supports both local disk and Cloudinary).
 */
export const getImageUrl = (imagePath) => {
  if (!imagePath) return null;
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://') || imagePath.startsWith('data:')) {
    return imagePath;
  }
  const cleanPath = imagePath.replace(/^\//, '');
  return `${API_BASE_URL}/${cleanPath}`;
};

/**
 * Fetch all complaints with optional filters (category, severity, status, limit, offset).
 */
export const getComplaints = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE_URL}/api/complaints${qs}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.error('getComplaints failed:', err);
    throw err;
  }
};

/**
 * Fetch single complaint by ID with full status history.
 */
export const getComplaint = async (id) => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/complaints/${encodeURIComponent(id)}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Complaint ${id} not found (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error(`getComplaint(${id}) failed:`, err);
    throw err;
  }
};

/**
 * Send image, GPS location, and language to AI pipeline for analysis.
 * Returns preview complaint draft without saving to DB yet.
 */
export const analyzeIssue = async (formData) => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Analysis failed (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error('analyzeIssue failed:', err);
    throw err;
  }
};

/**
 * Save confirmed complaint to database.
 */
export const submitComplaint = async (complaintData) => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/complaints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(complaintData),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Submission failed (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error('submitComplaint failed:', err);
    throw err;
  }
};

/**
 * Admin status update (submitted, assigned, in_progress, resolved, rejected).
 * Supports optional department reassignment and admin API key header.
 */
export const updateComplaintStatus = async (complaintId, newStatus, note = '', department = null) => {
  try {
    const payload = { status: newStatus, note };
    if (department) payload.department = department;

    const res = await fetch(`${API_BASE_URL}/api/complaints/${encodeURIComponent(complaintId)}/status`, {
      method: 'PATCH',
      headers: getAdminHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Status update failed (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error('updateComplaintStatus failed:', err);
    throw err;
  }
};

/**
 * Admin department assignment.
 */
export const assignComplaintDepartment = async (complaintId, department, note = '') => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/complaints/${encodeURIComponent(complaintId)}/department`, {
      method: 'PATCH',
      headers: getAdminHeaders(),
      body: JSON.stringify({ department, note }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Department reassignment failed (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error('assignComplaintDepartment failed:', err);
    throw err;
  }
};

/**
 * Upvote an existing complaint (used in duplicate detection flow).
 */
export const upvoteComplaint = async (complaintId) => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/complaints/${encodeURIComponent(complaintId)}/upvote`, {
      method: 'POST',
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Upvote failed (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error('upvoteComplaint failed:', err);
    throw err;
  }
};

/**
 * Fetch aggregated city analytics and KPI counts.
 */
export const getStats = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/stats`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch stats (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error('getStats failed:', err);
    throw err;
  }
};

/**
 * Regenerate complaint text in selected language or updated location.
 */
export const generateComplaintText = async (category, severity, address, language = 'en') => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/generate-complaint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, severity, address, language }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to generate text (${res.status})`);
    }
    const data = await res.json();
    return data.complaint_text;
  } catch (err) {
    console.error('generateComplaintText failed:', err);
    return null;
  }
};
