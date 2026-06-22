export function MiniBarChart({ items, labelKey, valueKey = "count" }) {
  const max = Math.max(1, ...items.map((item) => Number(item[valueKey] || 0)));

  return (
    <div className="bar-chart">
      {items.map((item) => {
        const value = Number(item[valueKey] || 0);
        const label = item[labelKey] || item.status || item.zone_id || "unknown";
        return (
          <div className="bar-row" key={label}>
            <span>{label}</span>
            <div className="bar-track">
              <div style={{ width: `${(value / max) * 100}%` }} />
            </div>
            <strong>{value}</strong>
          </div>
        );
      })}
    </div>
  );
}
