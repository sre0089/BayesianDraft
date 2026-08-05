import { describe, expect, it } from "vitest";

import {
  availablePlayers,
  candidateRollouts,
  explainRecommendation,
  initialDraftRoomState,
  pickSlot,
  recordPick,
  redo,
  loadDraftRoomState,
  rosterSummaries,
  saveDraftRoomState,
  teamBadgeForPlayer,
  undo,
} from "../src/draftRoom";

describe("draftRoom", () => {
  it("calculates snake draft slots", () => {
    expect(pickSlot(8)).toMatchObject({ managerId: "Your Team", round: 1, roundPick: 8 });
    expect(pickSlot(21)).toMatchObject({ managerId: "Your Team", round: 2, roundPick: 7 });
  });

  it("records picks and updates availability", () => {
    const state = recordPick(initialDraftRoomState, "rb_001");

    expect(state.completedPicks).toHaveLength(1);
    expect(availablePlayers(state).some((player) => player.playerId === "rb_001")).toBe(false);
  });

  it("supports undo and redo", () => {
    const picked = recordPick(initialDraftRoomState, "rb_001");
    const undone = undo(picked);
    const redone = redo(undone);

    expect(undone.completedPicks).toHaveLength(0);
    expect(redone.completedPicks).toHaveLength(1);
  });

  it("saves and loads state from storage", () => {
    const storage = new Map<string, string>();
    const fakeStorage = {
      get length() {
        return storage.size;
      },
      clear: () => storage.clear(),
      getItem: (key: string) => storage.get(key) ?? null,
      key: (index: number) => Array.from(storage.keys())[index] ?? null,
      removeItem: (key: string) => storage.delete(key),
      setItem: (key: string, value: string) => storage.set(key, value),
    } as Storage;
    const state = recordPick(initialDraftRoomState, "rb_001");

    saveDraftRoomState(state, fakeStorage);

    expect(loadDraftRoomState(fakeStorage)).toEqual(state);
  });

  it("explains the baseline recommendation", () => {
    const notes = explainRecommendation(availablePlayers(initialDraftRoomState)[0], 0);

    expect(notes.some((note) => note.includes("points over replacement"))).toBe(true);
    expect(notes.some((note) => note.includes("your next pick"))).toBe(true);
  });

  it("returns rollout candidates on the user pick", () => {
    const state = [
      "rb_001",
      "wr_001",
      "qb_001",
      "rb_002",
      "wr_002",
      "te_001",
      "wr_003",
    ].reduce((currentState, playerId) => recordPick(currentState, playerId), initialDraftRoomState);

    const rollouts = candidateRollouts(state, 2);

    expect(rollouts).toHaveLength(2);
    expect(rollouts[0].optimizerScore).toBeGreaterThan(0);
  });

  it("summarizes manager rosters and team badges", () => {
    const state = recordPick(initialDraftRoomState, "rb_001");
    const summaries = rosterSummaries(state);
    const firstManager = summaries[0];
    const badge = teamBadgeForPlayer(availablePlayers(initialDraftRoomState)[0]);

    expect(firstManager.managerId).toBe("Manager 01");
    expect(firstManager.roster).toHaveLength(1);
    expect(firstManager.counts.RB).toBe(1);
    expect(firstManager.projectedPoints).toBe(285);
    expect(badge.abbreviation).toBe("CCC");
    expect(badge.className).toMatch(/team-badge--/);
  });
});
