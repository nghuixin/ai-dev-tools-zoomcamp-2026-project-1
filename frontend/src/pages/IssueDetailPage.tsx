import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { addNote, fetchIssue, fetchSites, fetchStudies, updateIssue } from "../api";
import { FieldTag } from "../components/FieldTag";
import { StatusButtons } from "../components/StatusButtons";
import { detectPhi } from "../phi";
import type { AiSuggestion, Category, Issue, Severity, Site, Status, Study } from "../types";
import {
  CATEGORIES,
  CATEGORY_LABELS,
  dueHint,
  formatDate,
  SEVERITIES,
  SEVERITY_LABELS,
} from "../vocab";

type FormState = {
  study_id: string;
  site_id: string;
  description: string;
  category: Category | "";
  severity: Severity | "";
  summary: string;
  recommended_action: string;
  owner: string;
  due_date: string;
};

function toForm(issue: Issue): FormState {
  return {
    study_id: String(issue.study_id),
    site_id: String(issue.site_id),
    description: issue.description,
    category: issue.category,
    severity: issue.severity,
    summary: issue.summary,
    recommended_action: issue.recommended_action,
    owner: issue.owner || "",
    due_date: issue.due_date || "",
  };
}

function tag(issue: Issue, field: string, current: string): "ai" | "edited" | undefined {
  const suggestion = issue.ai_suggestion;
  if (!suggestion) return undefined;
  const original = String(suggestion[field as keyof AiSuggestion] ?? "");
  if (current.trim() === original.trim()) return "ai";
  return "edited";
}

export function IssueDetailPage() {
  const { id } = useParams();
  const [issue, setIssue] = useState<Issue | null>(null);
  const [form, setForm] = useState<FormState | null>(null);
  const [studies, setStudies] = useState<Study[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [note, setNote] = useState("");
  const [resolveOpen, setResolveOpen] = useState(false);
  const [resolutionNote, setResolutionNote] = useState("");
  const [statusBusy, setStatusBusy] = useState(false);

  useEffect(() => {
    fetchStudies().then(setStudies).catch(() => setStudies([]));
  }, []);

  useEffect(() => {
    if (!id) return;
    fetchIssue(id)
      .then((loaded) => {
        setIssue(loaded);
        setForm(toForm(loaded));
        setResolutionNote(loaded.resolution_note || "");
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Not found"));
  }, [id]);

  useEffect(() => {
    if (!form?.study_id) {
      setSites([]);
      return;
    }
    fetchSites(Number(form.study_id)).then(setSites).catch(() => setSites([]));
  }, [form?.study_id]);

  function patch<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => (current ? { ...current, [key]: value } : current));
  }

  async function saveFields() {
    if (!issue || !form || !form.category || !form.severity) return;
    setSaving(true);
    setError("");
    try {
      const updated = await updateIssue(issue.id, {
        ...form,
        study_id: Number(form.study_id),
        site_id: Number(form.site_id),
        owner: form.owner.trim() || null,
        due_date: form.due_date || null,
        phi_flag: detectPhi(form.description),
      });
      setIssue(updated);
      setForm(toForm(updated));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  async function onStatus(status: Status) {
    if (!issue) return;
    if (status === "RESOLVED") {
      setResolveOpen(true);
      return;
    }
    setStatusBusy(true);
    setError("");
    try {
      const updated = await updateIssue(issue.id, { status });
      setIssue(updated);
      setResolveOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update status");
    } finally {
      setStatusBusy(false);
    }
  }

  async function confirmResolve() {
    if (!issue) return;
    if (!resolutionNote.trim()) {
      setError("Resolution note required");
      return;
    }
    setStatusBusy(true);
    setError("");
    try {
      const updated = await updateIssue(issue.id, {
        status: "RESOLVED",
        resolution_note: resolutionNote.trim(),
      });
      setIssue(updated);
      setResolveOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resolve");
    } finally {
      setStatusBusy(false);
    }
  }

  async function onAddNote() {
    if (!issue || !note.trim()) return;
    try {
      const created = await addNote(issue.id, note.trim());
      setIssue({ ...issue, notes: [...(issue.notes || []), created] });
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add note");
    }
  }

  if (error && !issue) {
    return (
      <section className="page">
        <p className="error">{error}</p>
        <Link to="/issues">Back to issues</Link>
      </section>
    );
  }

  if (!issue || !form) {
    return (
      <section className="page">
        <p className="hint">Loading issue…</p>
      </section>
    );
  }

  const suggestion = issue.ai_suggestion;

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <p className="eyebrow">
            <Link to="/issues">Issues</Link> · #{issue.id}
          </p>
          <h2>{issue.summary || "Issue"}</h2>
        </div>
        <p className="lede">
          Edit any field, move status in any order, and append notes. Resolving requires a note.
        </p>
      </div>

      <div className="status-panel">
        <span className="status-label">Status</span>
        <StatusButtons value={issue.status} onSelect={onStatus} disabled={statusBusy} />
        {issue.resolved_at && (
          <small className="hint">First resolved {formatDate(issue.resolved_at.slice(0, 10))}</small>
        )}
      </div>

      {resolveOpen && (
        <div className="panel gate">
          <h3>Resolution note</h3>
          <p className="hint">Required to mark this issue resolved.</p>
          <textarea
            rows={4}
            value={resolutionNote}
            onChange={(event) => setResolutionNote(event.target.value)}
            placeholder="What was done, and what remains (if anything)."
          />
          <div className="actions">
            <button type="button" className="btn btn-primary" onClick={confirmResolve} disabled={statusBusy}>
              Confirm resolved
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setResolveOpen(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="log-grid">
        <div className="panel">
          <label className="field">
            <span>Study</span>
            <select
              value={form.study_id}
              onChange={(event) =>
                setForm((current) =>
                  current ? { ...current, study_id: event.target.value, site_id: "" } : current,
                )
              }
            >
              {studies.map((study) => (
                <option key={study.id} value={study.id}>
                  {study.code} · {study.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Site</span>
            <select value={form.site_id} onChange={(event) => patch("site_id", event.target.value)}>
              {sites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.code} · {site.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Description</span>
            <textarea
              rows={7}
              value={form.description}
              onChange={(event) => patch("description", event.target.value)}
            />
            <small className="hint">Do not include names, dates of birth, MRNs, or contact details.</small>
          </label>
          {detectPhi(form.description) && (
            <div className="banner banner-warn">This description looks like it contains identifiers.</div>
          )}
        </div>

        <div className="panel">
          <label className="field">
            <span>
              Category <FieldTag state={tag(issue, "category", form.category)} />
            </span>
            <select
              value={form.category}
              onChange={(event) => patch("category", event.target.value as Category)}
            >
              {CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {CATEGORY_LABELS[item]}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>
              Severity <FieldTag state={tag(issue, "severity", form.severity)} />
            </span>
            <select
              value={form.severity}
              onChange={(event) => patch("severity", event.target.value as Severity)}
            >
              {SEVERITIES.map((item) => (
                <option key={item} value={item}>
                  {SEVERITY_LABELS[item]}
                </option>
              ))}
            </select>
            <small className="hint">{dueHint(form.severity)}</small>
          </label>
          <label className="field">
            <span>
              Summary <FieldTag state={tag(issue, "summary", form.summary)} />
            </span>
            <input
              maxLength={200}
              value={form.summary}
              onChange={(event) => patch("summary", event.target.value)}
            />
          </label>
          <label className="field">
            <span>
              Recommended action <FieldTag state={tag(issue, "recommended_action", form.recommended_action)} />
            </span>
            <textarea
              rows={4}
              value={form.recommended_action}
              onChange={(event) => patch("recommended_action", event.target.value)}
            />
          </label>
          <div className="split">
            <label className="field">
              <span>Owner</span>
              <input value={form.owner} onChange={(event) => patch("owner", event.target.value)} />
            </label>
            <label className="field">
              <span>Due date</span>
              <input
                type="date"
                value={form.due_date}
                onChange={(event) => patch("due_date", event.target.value)}
              />
            </label>
          </div>
          <button type="button" className="btn btn-primary" onClick={saveFields} disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </button>
        </div>
      </div>

      {suggestion ? (
        <aside className="panel suggestion">
          <h3>Original AI suggestion</h3>
          <dl>
            <div>
              <dt>Category</dt>
              <dd>
                {CATEGORY_LABELS[suggestion.category]}
                {issue.edited_fields.includes("category") && <FieldTag state="edited" />}
              </dd>
            </div>
            <div>
              <dt>Severity</dt>
              <dd>
                {SEVERITY_LABELS[suggestion.severity]}
                {issue.edited_fields.includes("severity") && <FieldTag state="edited" />}
              </dd>
            </div>
            <div>
              <dt>Summary</dt>
              <dd>{suggestion.summary}</dd>
            </div>
            <div>
              <dt>Recommended action</dt>
              <dd>{suggestion.recommended_action}</dd>
            </div>
            <div>
              <dt>Rationale</dt>
              <dd>{suggestion.rationale}</dd>
            </div>
            <div>
              <dt>PHI flag</dt>
              <dd>{suggestion.phi_flag ? "Possible identifiers" : "None detected"}</dd>
            </div>
          </dl>
        </aside>
      ) : (
        <p className="hint">No original AI suggestion stored for this issue.</p>
      )}

      <div className="panel notes">
        <h3>Notes</h3>
        <ul className="note-list">
          {(issue.notes || []).length === 0 && <li className="hint">No notes yet.</li>}
          {(issue.notes || []).map((item) => (
            <li key={item.id}>
              <time>{new Date(item.created_at).toLocaleString()}</time>
              <p>{item.body}</p>
            </li>
          ))}
        </ul>
        <div className="note-compose">
          <textarea
            rows={3}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Append a note. Notes cannot be edited later."
          />
          <button type="button" className="btn btn-secondary" onClick={onAddNote} disabled={!note.trim()}>
            Append note
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
    </section>
  );
}
