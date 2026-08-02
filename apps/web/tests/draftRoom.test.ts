import { describe, expect, it } from "vitest";

import {
  availablePlayers,
  explainRecommendation,
  initialDraftRoomState,
  pickSlot,
  recordPick,
  redo,
  loadDraftRoomState,
  saveDraftRoomState,
  undo,
} from "../src/draftRoom";

describe("draftRoom", () => {
  it("calculates snake draft slots", () => {
    expect(pickSlot(8)).toMatchObject({ managerId: "Primary User", round: 1, roundPick: 8 });
    expect(pickSlot(21)).toMatchObject({ managerId: "Primary User", round: 2, roundPick: 7 });
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
    expect(notes.some((note) => note.includes("next user pick"))).toBe(true);
  });
});
