import type { Status } from "../types";
import { STATUSES, STATUS_LABELS } from "../vocab";

type Props = {
  value: Status;
  onSelect: (status: Status) => void;
  disabled?: boolean;
};

export function StatusButtons({ value, onSelect, disabled }: Props) {
  return (
    <div className="status-row" role="group" aria-label="Issue status">
      {STATUSES.map((status) => (
        <button
          key={status}
          type="button"
          className={`status-btn ${value === status ? "is-active" : ""}`}
          onClick={() => onSelect(status)}
          disabled={disabled}
        >
          {STATUS_LABELS[status]}
        </button>
      ))}
    </div>
  );
}
