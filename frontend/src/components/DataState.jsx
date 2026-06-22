export function DataState({ loading, error, empty, children }) {
  if (loading) {
    return <div className="state-box">Loading data...</div>;
  }
  if (error) {
    return <div className="state-box error">{error}</div>;
  }
  if (empty) {
    return <div className="state-box">No records found.</div>;
  }
  return children;
}
