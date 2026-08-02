const pillars = [
  "Live draft state",
  "Roster-aware recommendations",
  "Seeded simulation",
  "Manual-first workflow",
];

export function App() {
  return (
    <main className="app-shell">
      <section className="status-panel" aria-labelledby="app-title">
        <p className="eyebrow">Milestone 0</p>
        <h1 id="app-title">BayesianDraft</h1>
        <p className="summary">
          A local-first probabilistic draft optimizer for the user&apos;s 2026 ESPN
          full-PPR league.
        </p>
        <ul className="pillar-list">
          {pillars.map((pillar) => (
            <li key={pillar}>{pillar}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
