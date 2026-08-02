import { describe, expect, it } from "vitest";

import {
  availablePlayers,
  initialDraftRoomState,
  pickSlot,
  recordPick,
  redo,
  undo,
} from "../src/draftRoom";

describe("draftRoom", () => {
  it("calculates snake draft slots", () => {
    expect(pickSlot(9)).toMatchObject({ managerId: "Primary User", round: 1, roundPick: 9 });
    expect(pickSlot(16)).toMatchObject({ managerId: "Primary User", round: 2, roundPick: 4 });
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
});
