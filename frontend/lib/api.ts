const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const errorText = await res.text();
    let errorMessage = `API Error ${res.status}: ${res.statusText}`;
    try {
      const jsonErr = JSON.parse(errorText);
      errorMessage = jsonErr.detail || errorMessage;
    } catch {}
    throw new Error(errorMessage);
  }

  return res.json();
}

export async function parseCsvFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_BASE}/batches/parse`;
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const jsonErr = await res.json().catch(() => ({ detail: 'Failed to parse CSV' }));
    throw new Error(jsonErr.detail || 'CSV parsing error');
  }

  return res.json();
}

export async function validateCsvMapping(payload: {
  headers: string[];
  rows: Record<string, string>[];
  column_mapping: Record<string, string>;
}) {
  return fetchApi('/batches/validate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function confirmBatchImport(payload: {
  filename: string;
  headers: string[];
  rows: Record<string, string>[];
  column_mapping: Record<string, string>;
}) {
  return fetchApi('/batches/create', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getDashboardMetrics() {
  return fetchApi('/metrics');
}

export async function getBatchesList() {
  return fetchApi('/batches');
}

export async function getBatchDetail(batchId: string) {
  return fetchApi(`/batches/${batchId}`);
}

export async function getJobDetail(jobId: string) {
  return fetchApi(`/jobs/${jobId}`);
}

export async function getJobFilePreview(jobId: string, filename: string) {
  return fetchApi(`/jobs/${jobId}/files/${filename}`);
}

export async function getJobActivity(jobId: string) {
  return fetchApi(`/jobs/${jobId}/activity`);
}

export async function getReviewQueue() {
  return fetchApi('/articles/review-queue');
}

export async function approveArticle(jobId: string) {
  return fetchApi(`/articles/${jobId}/approve`, { method: 'POST' });
}

export async function requestRevision(jobId: string, notes: string) {
  return fetchApi(`/articles/${jobId}/request-revision`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  });
}

export async function editArticle(jobId: string, contentBody: string) {
  return fetchApi(`/articles/${jobId}/edit`, {
    method: 'POST',
    body: JSON.stringify({ content_body: contentBody }),
  });
}

export function rejectArticle(jobId: string) {
  return fetchApi(`/articles/${jobId}/reject`, { method: 'POST' });
}

export function humanizeArticle(jobId: string) {
  return fetchApi(`/articles/${jobId}/humanize`, { method: 'POST' });
}

export async function retryJob(jobId: string) {
  return fetchApi(`/jobs/${jobId}/retry`, { method: 'POST' });
}

export async function retryPublishing(jobId: string) {
  return fetchApi(`/jobs/${jobId}/publish-retry`, { method: 'POST' });
}

export async function getSystemConfig() {
  return fetchApi('/websites/config');
}

export async function updateSystemConfig(configData: any) {
  return fetchApi('/websites/config', {
    method: 'POST',
    body: JSON.stringify(configData),
  });
}

export async function deleteBatch(batchId: string) {
  return fetchApi(`/batches/${batchId}`, { method: 'DELETE' });
}

export async function resumeBatch(batchId: string) {
  return fetchApi(`/batches/${batchId}/resume`, { method: 'POST' });
}

export async function regenerateJobStep(jobId: string, stepFilename: string) {
  return fetchApi(`/jobs/${jobId}/regenerate-step`, {
    method: 'POST',
    body: JSON.stringify({ step_filename: stepFilename }),
  });
}

export async function forceFinalizeJob(jobId: string) {
  return fetchApi(`/jobs/${jobId}/force-finalize`, { method: 'POST' });
}

export async function reviseJob(jobId: string) {
  return fetchApi(`/jobs/${jobId}/revise`, { method: 'POST' });
}




