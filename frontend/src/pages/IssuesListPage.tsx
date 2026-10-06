import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { downloadCsv, fetchIssues, fetchSites, fetchStudies } from "../api";
import { SeverityChip } from "../components/SeverityChip";
import type { Issue, Site, Study } from "../types";
import { formatAge, formatDate, SEVERITIES, SEVERITY_LABELS, STATUS_LABELS, STATUSES } from "../vocab";

export function IssuesListPage() {
  const [params, setParams] = useSearchParams();
  const highlight = params.get("highlight");
  const [studies, setStudies] = useState<Study[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [error, setError] = useState("");

  const filters = {
    study_id: params.get("study_id") || "",
    site_id: params.get("site_id") || "",
    status: params.get("status") || "active",
    severity: params.get("severity") || "",
  };

  useEffect(() => {
    fetchStudies().then(setStudies).catch(() => setStudies([]));
  }, []);

  useEffect(() => {
    if (!filters.study_id) {
      fetchSites().then(setSites).catch(() => setSites([]));
      return;
    }
    fetchSites(Number(filters.study_id)).then(setSites).catch(() => setSites([]));
  }, [filters.study_id]);

  useEffect(() => {
    setError("");
    fetchIssues(filters)
      .then(setIssues)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load issues"));
  }, [filters.study_id, filters.site_id, filters.status, filters.severity]);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key === "study_id") next.delete("site_id");
    next.delete("highlight");
    setParams(next);
  }

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <p className="eyebrow">Inbox</p>
          <h2>Issues</h2>
        </div>
        <p className="lede">
          Sorted by severity, then oldest. Resolved issues stay hidden unless you filter to them.
        </p>
      </div>

      <div className="filters">
        <label>
          Study
          <select value={filters.study_id} onChange={(event) => setFilter("study_id", event.target.value)}>
            <option value="">All studies</option>
            {studies.map((study) => (
              <option key={study.id} value={study.id}>
                {study.code} · {study.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Site
          <select value={filters.site_id} onChange={(event) => setFilter("site_id", event.target.value)}>
            <option value="">All sites</option>
            {sites.map((site) => (
              <option key={site.id} value={site.id}>
                {site.code} · {site.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={filters.status} onChange={(event) => setFilter("status", event.target.value)}>
            <option value="active">Active (hide resolved)</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS[status]}
              </option>
            ))}
            <option value="ALL">All statuses</option>
          </select>
        </label>
        <label>
          Severity
          <select value={filters.severity} onChange={(event) => setFilter("severity", event.target.value)}>
            <option value="">All severities</option>
            {SEVERITIES.map((severity) => (
              <option key={severity} value={severity}>
                {SEVERITY_LABELS[severity]}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-secondary" onClick={() => downloadCsv(filters)}>
          Export CSV
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="table-wrap">
        <table className="issues">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Site</th>
              <th>Summary</th>
              <th>Status</th>
              <th>Owner</th>
              <th>Due</th>
              <th>Age</th>
            </tr>
          </thead>
          <tbody>
            {issues.length === 0 && (
              <tr>
                <td colSpan={7} className="empty">
                  No issues match these filters.
                </td>
              </tr>
            )}
            {issues.map((issue) => (
              <tr
                key={issue.id}
                className={highlight === String(issue.id) ? "is-highlight" : undefined}
              >
                <td>
                  <SeverityChip severity={issue.severity} />
                </td>
                <td>
                  <span className="cell-strong">
                    {issue.site.code} {issue.site.name}
                  </span>
                  <small>
                    {issue.study.code}
                  </small>
                </td>
                <td>
                  <Link to={`/issues/${issue.id}`}>{issue.summary || issue.description.slice(0, 80)}</Link>
                </td>
                <td>{STATUS_LABELS[issue.status]}</td>
                <td>{issue.owner || "—"}</td>
                <td className={issue.overdue ? "is-overdue" : undefined}>{formatDate(issue.due_date)}</td>
                <td>{formatAge(issue.age_days)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
