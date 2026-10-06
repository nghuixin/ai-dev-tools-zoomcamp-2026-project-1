import { NavLink } from "react-router-dom";
import type { Tweaks } from "../types";

type Props = {
  tweaks: Tweaks;
  onTweaksChange: (next: Tweaks) => void;
};

export function AppHeader({ tweaks, onTweaksChange }: Props) {
  return (
    <header className="topbar">
      <div className="brand">
        <p className="eyebrow">Local · single user · prototype</p>
        <h1>Site Issue Triage</h1>
      </div>
      <nav className="nav">
        <NavLink to="/log">Log issue</NavLink>
        <NavLink to="/issues" end>
          Issues
        </NavLink>
      </nav>
      <label className="tweaks">
        <span>Tweaks</span>
        <select
          value={tweaks.analyze || "normal"}
          onChange={(event) =>
            onTweaksChange({ ...tweaks, analyze: event.target.value as Tweaks["analyze"] })
          }
        >
          <option value="normal">Analyze: normal</option>
          <option value="unavailable">Analyze: unavailable</option>
        </select>
      </label>
    </header>
  );
}
