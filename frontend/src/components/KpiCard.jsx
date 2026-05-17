export function KpiCard({ title, value, note }) {
  return (
    <article className="kpi-card">
      <div className="kpi-title">{title}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-note">{note}</div>
    </article>
  );
}
