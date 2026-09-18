function ensureUTC(dateString: string): string {
  if (!dateString) return dateString;
  const str = dateString.trim();
  if (str.endsWith("Z") || /[+-]\d{2}:?\d{2}$/.test(str)) {
    return str;
  }
  return `${str}Z`;
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return "N/A";
  const formattedStr = ensureUTC(dateString);
  try {
    const d = new Date(formattedStr);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
  } catch {
    return dateString;
  }
}

export function formatTimeOnly(dateString: string | null | undefined): string {
  if (!dateString) return "N/A";
  const formattedStr = ensureUTC(dateString);
  try {
    const d = new Date(formattedStr);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
  } catch {
    return dateString;
  }
}

