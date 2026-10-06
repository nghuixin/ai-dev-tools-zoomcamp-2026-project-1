import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeIssue, createIssue, createSite, fetchSites, fetchStudies } from "../api";
import { FieldTag } from "../components/FieldTag";
import { detectPhi } from "../phi";
import type { AiSuggestion, Category, Severity, Site, Study, Tweaks } from "../types";
import { CATEGORIES, CATEGORY_LABELS, DUE_DAYS, dueHint, SEVERITIES, SEVERITY_LABELS } from "../vocab";

type FieldKey = "category" | "severity" | "summary" | "recommended_action" | "rationale";

type Props = {
  tweaks?: Tweaks;
};

const EMPTY_FORM = {
  studyId: "",
  siteId: "",
  description: "",
  category: "" as Category | "",
  severity: "" as Severity | "",
  summary: "",
  recommended_action: "",
  rationale: "",
  owner: "",
  due_date: "",
};

export function LogIssuePage({ tweaks = {} }: Props) {
  const navigate = useNavigate();
  const [studies, setStudies] = useState<Study[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [suggestion, setSuggestion] = useState<AiSuggestion | null>(null);
  const [analyzeError, setAnalyzeError] = useState("");
  const [analyzeBusy, setAnalyzeBusy] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [addingSite, setAddingSite] = useState(false);
  const [newSiteName, setNewSiteName] = useState("");
  const [newSiteCode, setNewSiteCode] = useState("");
  const [siteError, setSiteError] = useState("");

  const study = studies.find((item) => String(item.id) === form.studyId);
  const site = sites.find((item) => String(item.id) === form.siteId);
  const phiWarning = detectPhi(form.description) || suggestion?.phi_flag;

  useEffect(() => {
    fetchStudies().then(setStudies).catch(() => setStudies([]));
  }, []);

  useEffect(() => {
    if (!form.studyId) {
      setSites([]);
      return;
    }
    fetchSites(Number(form.studyId)).then(setSites).catch(() => setSites([]));
  }, [form.studyId]);

  function patch<K extends keyof typeof EMPTY_FORM>(key: K, value: (typeof EMPTY_FORM)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function tagFor(field: FieldKey): "ai" | "edited" | undefined {
    if (!suggestion) return undefined;
    const current = form[field];
    const original = suggestion[field];
    if (current === original) return "ai";
    if (current) return "edited";
    return undefined;
  }

  const canAnalyze = Boolean(study && site && form.description.trim());
  const canSave = Boolean(
    form.studyId && form.siteId && form.description.trim() && form.category && form.severity,
  );

  async function onAnalyze() {
    setAnalyzeError("");
    if (tweaks.analyze === "unavailable") {
      setAnalyzeError("suggestion unavailable");
      return;
    }
    if (!study || !site) return;
    setAnalyzeBusy(true);
    try {
      const result = await analyzeIssue({
        study: `${study.code} ${study.name}`,
        site: `${site.code} ${site.name}`,
        description: form.description,
      });
      setSuggestion(result);
      setForm((current) => ({
        ...current,
        category: result.category,
        severity: result.severity,
        summary: result.summary,
        recommended_action: result.recommended_action,
        rationale: result.rationale,
      }));
    } catch (err) {
      setAnalyzeError(err instanceof Error ? err.message : "suggestion unavailable");
    } finally {
      setAnalyzeBusy(false);
    }
  }

  async function onAddSite() {
    setSiteError("");
    if (!form.studyId || !newSiteName.trim()) {
      setSiteError("Site name is required.");
      return;
    }
    try {
      const created = await createSite({
        study_id: Number(form.studyId),
        name: newSiteName.trim(),
        code: newSiteCode.trim() || undefined,
      });
      setSites((current) => [...current, created]);
      patch("siteId", String(created.id));
      setAddingSite(false);
      setNewSiteName("");
      setNewSiteCode("");
    } catch (err) {
      setSiteError(err instanceof Error ? err.message : "Could not add site");
    }
  }

  async function onSave() {
    setSaveError("");
    if (!canSave) return;
    setSaving(true);
    try {
      const created = await createIssue({
        study_id: Number(form.studyId),
        site_id: Number(form.siteId),
        description: form.description.trim(),
        category: form.category,
        severity: form.severity,
        summary: form.summary.trim(),
        recommended_action: form.recommended_action.trim(),
        owner: form.owner.trim() || null,
        due_date: form.due_date || null,
        ai_suggestion: suggestion,
        phi_flag: Boolean(phiWarning),
      });
      navigate(`/issues?highlight=${created.id}`);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Could not save issue");
    } finally {
      setSaving(false);
    }
  }

  const studyOptions = useMemo(() => studies, [studies]);

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <p className="eyebrow">Step 1</p>
          <h2>Log issue</h2>
        </div>
        <p className="lede">
          Describe the operational issue. Analyze is optional and never blocks save.
        </p>
      </div>

      <div className="log-grid">
        <div className="panel">
          <label className="field">
            <span>Study</span>
            <select
              value={form.studyId}
              onChange={(event) => {
                setForm((current) => ({
                  ...current,
                  studyId: event.target.value,
                  siteId: "",
                }));
                setAddingSite(false);
              }}
            >
              <option value="">Select study</option>
              {studyOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code} · {item.name}
                </option>
              ))}
            </select>
          </label>

          <div className="field">
            <span>Site</span>
            <div className="site-row">
              <select
                value={form.siteId}
                onChange={(event) => patch("siteId", event.target.value)}
                disabled={!form.studyId}
              >
                <option value="">Select site</option>
                {sites.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.code} · {item.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={!form.studyId}
                onClick={() => setAddingSite((open) => !open)}
              >
                + Site
              </button>
            </div>
            {addingSite && (
              <div className="inline-site">
                <input
                  placeholder="Site number (optional)"
                  value={newSiteCode}
                  onChange={(event) => setNewSiteCode(event.target.value)}
                />
                <input
                  placeholder="Site name"
                  value={newSiteName}
                  onChange={(event) => setNewSiteName(event.target.value)}
                />
                <button type="button" className="btn btn-secondary" onClick={onAddSite}>
                  Add
                </button>
              </div>
            )}
            {siteError && <p className="error">{siteError}</p>}
          </div>

          <label className="field">
            <span>Description</span>
            <textarea
              rows={8}
              value={form.description}
              onChange={(event) => patch("description", event.target.value)}
              placeholder="What happened, at which process step, and what is blocked."
            />
            <small className="hint">Do not include names, dates of birth, MRNs, or contact details.</small>
          </label>

          {phiWarning && (
            <div className="banner banner-warn" role="alert">
              This description looks like it contains identifiers. Remove names, DOBs, MRNs, or
              contact details before saving if you can.
            </div>
          )}

          <div className="analyze-row">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onAnalyze}
              disabled={!canAnalyze || analyzeBusy}
            >
              {analyzeBusy ? "Analyzing…" : "Analyze"}
            </button>
            <small className="hint">Pre-fills triage fields. You can still edit everything.</small>
          </div>
          {analyzeError && (
            <div className="banner banner-warn" role="status">
              {analyzeError}
            </div>
          )}
        </div>

        <div className="panel">
          <label className="field">
            <span>
              Category <FieldTag state={tagFor("category")} />
            </span>
            <select
              value={form.category}
              onChange={(event) => patch("category", event.target.value as Category | "")}
            >
              <option value="">Select category</option>
              {CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {CATEGORY_LABELS[item]}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>
              Severity <FieldTag state={tagFor("severity")} />
            </span>
            <select
              value={form.severity}
              onChange={(event) => patch("severity", event.target.value as Severity | "")}
            >
              <option value="">Select severity</option>
              {SEVERITIES.map((item) => (
                <option key={item} value={item}>
                  {SEVERITY_LABELS[item]} — due {DUE_DAYS[item]} {DUE_DAYS[item] === 1 ? "day" : "days"}
                </option>
              ))}
            </select>
            <small className="hint">{dueHint(form.severity)}</small>
          </label>

          <label className="field">
            <span>
              Summary <FieldTag state={tagFor("summary")} />
            </span>
            <input
              maxLength={200}
              value={form.summary}
              onChange={(event) => patch("summary", event.target.value)}
            />
            <small className="hint">{form.summary.length}/200</small>
          </label>

          <label className="field">
            <span>
              Recommended action <FieldTag state={tagFor("recommended_action")} />
            </span>
            <textarea
              rows={4}
              value={form.recommended_action}
              onChange={(event) => patch("recommended_action", event.target.value)}
            />
          </label>

          {(form.rationale || suggestion) && (
            <label className="field">
              <span>
                Rationale <FieldTag state={tagFor("rationale")} />
              </span>
              <input
                value={form.rationale}
                onChange={(event) => patch("rationale", event.target.value)}
              />
            </label>
          )}

          <div className="split">
            <label className="field">
              <span>Owner</span>
              <input
                value={form.owner}
                onChange={(event) => patch("owner", event.target.value)}
                placeholder="Optional"
              />
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
        </div>
      </div>

      {saveError && <p className="error">{saveError}</p>}

      <div className="actions">
        <button type="button" className="btn btn-primary" onClick={onSave} disabled={!canSave || saving}>
          {saving ? "Saving…" : "Save issue"}
        </button>
        {!canSave && (
          <small className="hint">Study, site, description, category, and severity are required.</small>
        )}
      </div>
    </section>
  );
}
