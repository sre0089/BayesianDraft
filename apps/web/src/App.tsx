import { useMemo, useState } from "react";

import {
  availablePlayers,
  initialDraftRoomState,
  pickSlot,
  players,
  recordPick,
  redo,
  rosterForManager,
  type Position,
  undo,
} from "./draftRoom";

const positions: Array<Position | "ALL"> = ["ALL", "QB", "RB", "WR", "TE", "DST", "K"];

export function App() {
  const [draftState, setDraftState] = useState(initialDraftRoomState);
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState<Position | "ALL">("ALL");
  const currentSlot = pickSlot(draftState.completedPicks.length + 1);
  const remainingPlayers = availablePlayers(draftState);
  const filteredPlayers = useMemo(
    () =>
      remainingPlayers.filter((player) => {
        const matchesPosition = position === "ALL" || player.position === position;
        const normalizedQuery = query.trim().toLowerCase();
        const matchesQuery =
          normalizedQuery.length === 0 ||
          player.fullName.toLowerCase().includes(normalizedQuery) ||
          player.team.toLowerCase().includes(normalizedQuery);
        return matchesPosition && matchesQuery;
      }),
    [position, query, remainingPlayers],
  );
  const primary = filteredPlayers[0] ?? remainingPlayers[0];
  const userRoster = rosterForManager(draftState, "Primary User");

  return (
    <main className="draft-room">
      <header className="top-bar">
        <div>
          <p className="eyebrow">Manual draft room</p>
          <h1>BayesianDraft</h1>
        </div>
        <div className="clock-grid" aria-label="Draft status">
          <Metric label="Round" value={String(currentSlot.round)} />
          <Metric label="Pick" value={String(currentSlot.overallPick)} />
          <Metric label="On clock" value={currentSlot.managerId} />
          <Metric
            label="User next"
            value={String(nextUserPick(draftState.completedPicks.length))}
          />
        </div>
      </header>

      <section className="recommendation-band" aria-labelledby="recommendation-title">
        <div>
          <p className="eyebrow">Baseline recommendation</p>
          <h2 id="recommendation-title">{primary?.fullName ?? "Draft complete"}</h2>
          <p>
            {primary
              ? `${primary.position} - ${primary.team} - Rank ${primary.overallRank} - Tier ${primary.tier}`
              : "No available players remain in the fixture."}
          </p>
        </div>
        {primary ? (
          <button
            className="primary-action"
            onClick={() => setDraftState(recordPick(draftState, primary.playerId))}
          >
            Draft
          </button>
        ) : null}
      </section>

      <section className="workspace">
        <section className="panel available-panel" aria-labelledby="available-title">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Available</p>
              <h2 id="available-title">Players</h2>
            </div>
            <div className="toolbar">
              <button aria-label="Undo pick" onClick={() => setDraftState(undo(draftState))}>
                Undo
              </button>
              <button aria-label="Redo pick" onClick={() => setDraftState(redo(draftState))}>
                Redo
              </button>
            </div>
          </div>

          <div className="filters">
            <input
              aria-label="Search players"
              placeholder="Search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <div className="segments" aria-label="Position filters">
              {positions.map((option) => (
                <button
                  key={option}
                  aria-pressed={position === option}
                  onClick={() => setPosition(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Player</th>
                  <th>Pos</th>
                  <th>Team</th>
                  <th>Proj</th>
                  <th>ADP</th>
                  <th>Tier</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredPlayers.map((player) => (
                  <tr key={player.playerId}>
                    <td>{player.overallRank}</td>
                    <td>{player.fullName}</td>
                    <td>{player.position}</td>
                    <td>{player.team}</td>
                    <td>{player.projectedPoints}</td>
                    <td>{player.adp}</td>
                    <td>{player.tier}</td>
                    <td>
                      <button
                        onClick={() => setDraftState(recordPick(draftState, player.playerId))}
                      >
                        Draft
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="side-stack">
          <section className="panel" aria-labelledby="board-title">
            <p className="eyebrow">Draft board</p>
            <h2 id="board-title">Recent picks</h2>
            <ol className="pick-list">
              {draftState.completedPicks.slice(-8).map((pick) => {
                const player = players.find((item) => item.playerId === pick.playerId);
                return (
                  <li key={pick.overallPick}>
                    <span>{pick.overallPick}</span>
                    <strong>{player?.fullName}</strong>
                    <small>{pick.managerId}</small>
                  </li>
                );
              })}
            </ol>
          </section>

          <section className="panel" aria-labelledby="roster-title">
            <p className="eyebrow">Roster</p>
            <h2 id="roster-title">Primary User</h2>
            <div className="roster-list">
              {userRoster.length === 0 ? (
                <p className="empty">No picks yet</p>
              ) : (
                userRoster.map((player) => (
                  <div key={player.playerId} className="roster-row">
                    <span>{player.position}</span>
                    <strong>{player.fullName}</strong>
                  </div>
                ))
              )}
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function nextUserPick(completedCount: number) {
  for (let pick = completedCount + 1; pick <= 192; pick += 1) {
    if (pickSlot(pick).managerId === "Primary User") {
      return pick;
    }
  }
  return "-";
}
