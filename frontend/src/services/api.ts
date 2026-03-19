import { supabase } from '../lib/supabase';

const API_BASE_URL = 'http://localhost:8000'; // Change in production

// Helper to get auth token
async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  return {
    'Authorization': session?.access_token ? `Bearer ${session.access_token}` : '',
  };
}

/**
 * Analyze an image and optionally link it to a specific field.
 */
export async function analyzeImage(file: File, fieldId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Auto-inject authenticated user context if active
    const { data: { session } } = await supabase.auth.getSession();
    
    let finalFieldId = fieldId;

    if (session?.user?.id) {
       formData.append('user_id', session.user.id);
       
       // Fallback active field resolution 
       if (!finalFieldId) {
           try {
               const fieldsObj = await getFields(session.user.id);
               finalFieldId = fieldsObj.fields?.[0]?.id;
               if (!finalFieldId) {
                   const newField = await createField(session.user.id, "Main Farmland");
                   finalFieldId = newField.id;
               }
           } catch (e) {
               console.error("Auto field generation failed:", e);
           }
       }
    }
    
    if (finalFieldId) {
      formData.append('field_id', finalFieldId);
    }

    const headers = await getAuthHeaders();
    
    // Note: Do not stringify FormData or set Content-Type header manually
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: headers, // omitting Content-Type allows browser to auto-set boundary
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Image analysis failed');
    }
    return response.json();
}

/**
 * Trigger analysis for an existing drone-ingested scan.
 */
export async function analyzeExistingScan(scanId: string) {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/analyze/scan/${scanId}`, {
      method: 'POST',
      headers: headers,
    });
    if (!response.ok) {
      throw new Error('Analysis of existing scan failed');
    }
    return response.json();
}

/**
 * Fetch all registered fields for the logged in user.
 */
export async function getFields(userId: string) {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/fields?user_id=${userId}`, {
      headers,
    });
    if (!response.ok) throw new Error('Failed to fetch fields');
    return response.json();
}

/**
 * Create a new field logically binding future scans.
 */
export async function createField(userId: string, name: string) {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/fields`, {
      method: 'POST',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId, name }),
    });
    if (!response.ok) throw new Error('Failed to create field');
    return response.json();
}

/**
 * Get all historical scans for a chosen field layout.
 */
export async function getHistoricalScans(fieldId: string) {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/fields/${fieldId}/scans`, {
      headers,
    });
    if (!response.ok) throw new Error('Failed to fetch historical scans');
    return response.json();
}

/**
 * Launch backend time-series comparison heuristics on two recorded scans.
 */
export async function compareScans(fieldId: string, prevId: string, currId: string) {
    const headers = await getAuthHeaders();
    const response = await fetch(
      `${API_BASE_URL}/api/fields/${fieldId}/compare?prev_id=${prevId}&curr_id=${currId}`,
      { headers }
    );
    if (!response.ok) throw new Error('Comparison failed');
    return response.json();
}

/**
 * Retrieve the generated HTML Report link for a given scan configuration.
 */
export async function getReportUrl(scanId: string) {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/report/${scanId}`, {
      headers,
    });
    if (!response.ok) throw new Error('Report not found or still generating. Try again in a few seconds.');
    return response.json();
}

/**
 * Return the raw URL string to trigger a standalone HTML Comparison compilation directly from FastAPI.
 */
export function getComparisonReportUrl(prevId: string, currId: string, token: string) {
    return `${API_BASE_URL}/api/report/compare/${prevId}/${currId}?token=${token}`;
}

/**
 * Fetch overall dashboard statistics for the logged in user.
 */
export async function getDashboardStats(userId: string) {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/stats?user_id=${userId}`, {
      headers,
    });
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
}

export const cropSightApi = {
  analyzeImage,
  getFields,
  createField,
  getHistoricalScans,
  compareScans,
  getReportUrl,
  getComparisonReportUrl,
  getDashboardStats,
  analyzeExistingScan
};

