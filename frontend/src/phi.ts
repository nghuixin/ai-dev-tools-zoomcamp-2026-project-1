export function detectPhi(text: string) {
  const value = text || "";
  const patterns = [
    /\b[\w.+-]+@[\w.-]+\.\w+\b/,
    /\b(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/,
    /\b(mrn|medical record( number)?)\s*[:#]?\s*\d+/i,
    /\b(dob|date of birth)\b/i,
    /\b\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}\b/,
    /\b(ssn|social security)\b/i,
    /\b(patient|subject)\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)?\b/,
  ];
  return patterns.some((re) => re.test(value));
}
