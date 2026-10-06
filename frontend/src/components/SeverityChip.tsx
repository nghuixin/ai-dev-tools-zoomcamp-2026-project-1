import type { Severity } from "../types";
import { SEVERITY_LABELS } from "../vocab";

export function SeverityChip({ severity }: { severity: Severity }) {
  return <span className={`chip chip-${severity.toLowerCase()}`}>{SEVERITY_LABELS[severity]}</span>;
}
