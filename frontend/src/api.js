export const mockComplaints = [
  {
    "complaint_id": "CF-0001",
    "category": "pothole",
    "confidence": 0.94,
    "severity": "high",
    "location": {"lat": 25.311, "lng": 82.973, "address": "123 Main St, Ward 5"},
    "department": "Road Maintenance",
    "suggested_action": "Immediate repair required",
    "complaint_text": "A large pothole has been detected near 123 Main St. It poses a significant risk to vehicles.",
    "status": "submitted",
    "duplicate_of": null,
    "estimated_resolution_hours": 48,
    "createdAt": new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString()
  },
  {
    "complaint_id": "CF-0002",
    "category": "overflowing garbage",
    "confidence": 0.88,
    "severity": "medium",
    "location": {"lat": 25.320, "lng": 82.980, "address": "Market Square, Ward 2"},
    "department": "Sanitation",
    "suggested_action": "Schedule pickup within 24 hours",
    "complaint_text": "Overflowing garbage bins detected at Market Square, causing sanitation concerns.",
    "status": "in progress",
    "duplicate_of": null,
    "estimated_resolution_hours": 24,
    "createdAt": new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString()
  },
  {
    "complaint_id": "CF-0003",
    "category": "broken streetlight",
    "confidence": 0.92,
    "severity": "low",
    "location": {"lat": 25.315, "lng": 82.975, "address": "Park Ave, Ward 1"},
    "department": "Electrical",
    "suggested_action": "Inspect and replace bulb",
    "complaint_text": "Broken streetlight reported. Area is poorly lit at night.",
    "status": "resolved",
    "duplicate_of": null,
    "estimated_resolution_hours": 72,
    "createdAt": new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString()
  },
  {
    "complaint_id": "CF-0004",
    "category": "open manhole",
    "confidence": 0.99,
    "severity": "critical",
    "location": {"lat": 25.305, "lng": 82.965, "address": "School Road, Ward 4"},
    "department": "Public Works",
    "suggested_action": "Immediate barricading and cover replacement",
    "complaint_text": "Dangerous open manhole detected on School Road. High risk to pedestrians.",
    "status": "assigned",
    "duplicate_of": null,
    "estimated_resolution_hours": 12,
    "createdAt": new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
  },
  {
    "complaint_id": "CF-0005",
    "category": "water leakage",
    "confidence": 0.85,
    "severity": "medium",
    "location": {"lat": 25.330, "lng": 82.990, "address": "Riverfront, Ward 7"},
    "department": "Water Supply",
    "suggested_action": "Dispatch plumber to inspect pipeline",
    "complaint_text": "Significant water leakage observed on Riverfront.",
    "status": "submitted",
    "duplicate_of": null,
    "estimated_resolution_hours": 36,
    "createdAt": new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString()
  },
  {
    "complaint_id": "CF-0006",
    "category": "damaged road sign",
    "confidence": 0.91,
    "severity": "low",
    "location": {"lat": 25.310, "lng": 82.960, "address": "Highway 10 Exit",
    "department": "Traffic Police",
    "suggested_action": "Replace speed limit sign",
    "complaint_text": "Damaged speed limit sign detected at Highway 10 Exit.",
    "status": "resolved",
    "duplicate_of": null,
    "estimated_resolution_hours": 72,
    "createdAt": new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString()}
  }
];

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const getComplaints = async () => {
  if (API_BASE_URL) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/complaints`);
      if (response.ok) return await response.json();
    } catch (e) {
      console.warn("Backend fetch failed, falling back to mock data", e);
    }
  }
  return new Promise((resolve) => setTimeout(() => resolve(mockComplaints), 800));
};

export const getComplaint = async (id) => {
  if (API_BASE_URL) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/complaints/${id}`);
      if (response.ok) return await response.json();
    } catch (e) {
      console.warn("Backend fetch failed, falling back to mock data", e);
    }
  }
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const complaint = mockComplaints.find(c => c.complaint_id === id);
      if (complaint) resolve(complaint);
      else reject(new Error("Complaint not found"));
    }, 500);
  });
};

export const submitComplaint = async (data) => {
  if (API_BASE_URL) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        body: data // assuming FormData
      });
      if (response.ok) return await response.json();
    } catch (e) {
      console.warn("Backend fetch failed, falling back to mock data", e);
    }
  }
  return new Promise((resolve) => {
    setTimeout(() => {
      const newComplaint = {
        complaint_id: `CF-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
        ...data,
        status: "submitted",
        createdAt: new Date().toISOString()
      };
      mockComplaints.unshift(newComplaint);
      resolve(newComplaint);
    }, 1500);
  });
};
