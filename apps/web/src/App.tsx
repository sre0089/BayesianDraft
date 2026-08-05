import { useMemo, useState } from "react";

import {
  availablePlayers,
  candidateRollouts,
  explainRecommendation,
  initialDraftRoomState,
  loadDraftRoomState,
  pickSlot,
  players,
  recordPick,
  redo,
  rosterSummaries,
  rosterForManager,
  saveDraftRoomState,
  teamBadgeForPlayer,
  nextUserPick,
  managers,
  type ManagerRosterSummary,
  type Player,
  type Position,
  undo,
  userManagerName,
} from "./draftRoom";

const positions: Array<Position | "ALL"> = ["ALL", "QB", "RB", "WR", "TE", "DST", "K"];

export function App() {
  const [draftState, setDraftState] = useState(() => loadDraftRoomState() ?? initialDraftRoomState);
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState<Position | "ALL">("ALL");
  const [selectedManager, setSelectedManager] = useState(userManagerName);
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
  const explanation = primary
    ? explainRecommendation(primary, draftState.completedPicks.length)
    : [];
  const userRoster = rosterForManager(draftState, userManagerName);
  const rolloutCandidates = candidateRollouts(draftState);
  const playerById = new Map(players.map((player) => [player.playerId, player]));
  const managerSummaries = rosterSummaries(draftState);
  const selectedManagerSummary =
    managerSummaries.find((summary) => summary.managerId === selectedManager) ??
    managerSummaries[0];
  const completedPickCount = draftState.completedPicks.length;
  const progress = Math.round((completedPickCount / 224) * 100);

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
        <div className="recommendation-copy">
          <p className="eyebrow">Baseline recommendation</p>
          <h2 id="recommendation-title">
            {primary ? <PlayerName player={primary} size="large" /> : "Draft complete"}
          </h2>
          {primary ? (
            <div className="recommendation-metrics" aria-label="Recommendation metrics">
              <Metric label="Rank" value={String(primary.overallRank)} compact />
              <Metric label="Tier" value={String(primary.tier)} compact />
              <Metric label="Proj" value={String(primary.projectedPoints)} compact />
              <Metric label="VORP" value={String(primary.vorp)} compact />
            </div>
          ) : (
            <p>No available players remain in the fixture.</p>
          )}
          <ul className="explanation-list">
            {explanation.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
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
              <button aria-label="Save draft" onClick={() => saveDraftRoomState(draftState)}>
                Save
              </button>
              <button aria-label="Restore draft" onClick={() => setDraftState(loadDraftRoomState() ?? draftState)}>
                Restore
              </button>
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

          <div className="draft-progress" aria-label="Draft progress">
            <span>{completedPickCount} picks complete</span>
            <div>
              <i style={{ width: `${progress}%` }} />
            </div>
            <span>{remainingPlayers.length} available</span>
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
                    <td>
                      <PlayerName player={player} />
                    </td>
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
          <section className="panel competitor-panel" aria-labelledby="competitor-title">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Managers</p>
                <h2 id="competitor-title">Rosters</h2>
              </div>
              <span className="on-clock-pill">On clock: {currentSlot.managerId}</span>
            </div>
            <div className="manager-tabs" aria-label="Manager roster tabs">
              {managerSummaries.map((summary) => (
                <button
                  key={summary.managerId}
                  aria-pressed={summary.managerId === selectedManagerSummary.managerId}
                  onClick={() => setSelectedManager(summary.managerId)}
                >
                  <span>{managerLabel(summary.managerId)}</span>
                  <small>{summary.roster.length}</small>
                </button>
              ))}
            </div>
            <ManagerRoster summary={selectedManagerSummary} />
          </section>

          <section className="panel" aria-labelledby="board-title">
            <p className="eyebrow">Draft board</p>
            <h2 id="board-title">Recent picks</h2>
            <ol className="pick-list">
              {draftState.completedPicks.slice(-8).map((pick) => {
                const player = players.find((item) => item.playerId === pick.playerId);
                return (
                  <li key={pick.overallPick}>
                    <span>{pick.overallPick}</span>
                    {player ? <PlayerName player={player} /> : <strong>Unknown player</strong>}
                    <small>{pick.managerId}</small>
                  </li>
                );
              })}
            </ol>
          </section>

          <section className="panel" aria-labelledby="roster-title">
            <p className="eyebrow">Roster</p>
          <h2 id="roster-title">Your Team</h2>
            <div className="roster-list">
              {userRoster.length === 0 ? (
                <p className="empty">No picks yet</p>
              ) : (
                userRoster.map((player) => (
                  <div key={player.playerId} className="roster-row">
                    <span>{player.position}</span>
                    <PlayerName player={player} />
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="panel" aria-labelledby="simulator-title">
            <p className="eyebrow">Simulator</p>
            <h2 id="simulator-title">Candidate rollouts</h2>
            {rolloutCandidates.length === 0 ? (
              <p className="empty">Available on your pick</p>
            ) : (
              <div className="rollout-list">
                {rolloutCandidates.map((candidate) => {
                  const player = playerById.get(candidate.playerId);
                  return (
                    <article key={candidate.playerId} className="rollout-row">
                      <div>
                        {player ? <PlayerName player={player} /> : <strong>Unknown player</strong>}
                        <span>
                          {player?.position} - Score {candidate.optimizerScore}
                        </span>
                      </div>
                      <dl>
                        <div>
                          <dt>Proj</dt>
                          <dd>{candidate.averageProjectedPoints}</dd>
                        </div>
                        <div>
                          <dt>VORP</dt>
                          <dd>{candidate.averageVorp}</dd>
                        </div>
                      </dl>
                      <ul>
                        {candidate.explanation.slice(0, 2).map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </aside>
      </section>
    </main>
  );
}

function Metric({
  label,
  value,
  compact = false,
}: {
  label: string;
  value: string;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "metric metric--compact" : "metric"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PlayerName({ player, size = "default" }: { player: Player; size?: "default" | "large" }) {
  const badge = teamBadgeForPlayer(player);
  return (
    <span className={size === "large" ? "player-name player-name--large" : "player-name"}>
      <span className={`team-badge ${badge.className}`} aria-hidden="true">
        {badge.abbreviation}
      </span>
      <span>{player.fullName}</span>
    </span>
  );
}

function ManagerRoster({ summary }: { summary: ManagerRosterSummary }) {
  return (
    <div className="manager-roster">
      <div className="manager-roster__header">
        <div>
          <h3>{summary.managerId}</h3>
          <span>{summary.roster.length} picks</span>
        </div>
        <dl>
          <div>
            <dt>Proj</dt>
            <dd>{summary.projectedPoints}</dd>
          </div>
          <div>
            <dt>VORP</dt>
            <dd>{summary.vorp}</dd>
          </div>
        </dl>
      </div>
      <div className="position-counts" aria-label={`${summary.managerId} position counts`}>
        {positions
          .filter((position): position is Position => position !== "ALL")
          .map((position) => (
            <span key={position}>
              {position} {summary.counts[position]}
            </span>
          ))}
      </div>
      <div className="manager-roster__list">
        {summary.roster.length === 0 ? (
          <p className="empty">No picks yet</p>
        ) : (
          summary.roster.map((player) => (
            <div key={player.playerId} className="competitor-player">
              <PlayerName player={player} />
              <small>
                {player.position} - Rank {player.overallRank}
              </small>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function managerLabel(managerId: string) {
  if (managerId === userManagerName) {
    return "You";
  }
  const index = managers.indexOf(managerId) + 1;
  return index > 0 ? String(index).padStart(2, "0") : managerId;
}
