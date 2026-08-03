export type Position = "QB" | "RB" | "WR" | "TE" | "DST" | "K";

export type Player = {
  playerId: string;
  fullName: string;
  position: Position;
  team: string;
  projectedPoints: number;
  overallRank: number;
  positionRank: number;
  tier: number;
  adp: number;
  vorp: number;
};

export type Pick = {
  overallPick: number;
  round: number;
  roundPick: number;
  managerId: string;
  playerId: string;
};

export type DraftRoomState = {
  completedPicks: Pick[];
  undoStack: Pick[][];
  redoStack: Pick[][];
};

export type CandidateRollout = {
  playerId: string;
  optimizerScore: number;
  averageProjectedPoints: number;
  averageVorp: number;
  explanation: string[];
};

const storageKey = "bayesiandraft.draftRoomState";

export const managers = [
  "Manager 01",
  "Manager 02",
  "Manager 03",
  "Manager 04",
  "Manager 05",
  "Manager 06",
  "Manager 07",
  "Primary User",
  "Manager 09",
  "Manager 10",
  "Manager 11",
  "Manager 12",
  "Manager 13",
  "Manager 14",
];

export const totalDraftPicks = managers.length * 16;

export const players: Player[] = [
  {
    playerId: "rb_001",
    fullName: "Example RB One",
    position: "RB",
    team: "CCC",
    projectedPoints: 285,
    overallRank: 1,
    positionRank: 1,
    tier: 1,
    adp: 5,
    vorp: 100,
  },
  {
    playerId: "wr_001",
    fullName: "Example WR One",
    position: "WR",
    team: "FFF",
    projectedPoints: 270,
    overallRank: 2,
    positionRank: 1,
    tier: 1,
    adp: 8,
    vorp: 65,
  },
  {
    playerId: "qb_001",
    fullName: "Example QB One",
    position: "QB",
    team: "AAA",
    projectedPoints: 330,
    overallRank: 3,
    positionRank: 1,
    tier: 1,
    adp: 32,
    vorp: 35,
  },
  {
    playerId: "rb_002",
    fullName: "Example RB Two",
    position: "RB",
    team: "DDD",
    projectedPoints: 245,
    overallRank: 4,
    positionRank: 2,
    tier: 2,
    adp: 18,
    vorp: 60,
  },
  {
    playerId: "wr_002",
    fullName: "Example WR Two",
    position: "WR",
    team: "GGG",
    projectedPoints: 238,
    overallRank: 5,
    positionRank: 2,
    tier: 2,
    adp: 24,
    vorp: 33,
  },
  {
    playerId: "te_001",
    fullName: "Example TE One",
    position: "TE",
    team: "III",
    projectedPoints: 205,
    overallRank: 6,
    positionRank: 1,
    tier: 1,
    adp: 28,
    vorp: 60,
  },
  {
    playerId: "wr_003",
    fullName: "Example WR Three",
    position: "WR",
    team: "HHH",
    projectedPoints: 205,
    overallRank: 7,
    positionRank: 3,
    tier: 3,
    adp: 48,
    vorp: 0,
  },
  {
    playerId: "rb_003",
    fullName: "Example RB Three",
    position: "RB",
    team: "EEE",
    projectedPoints: 185,
    overallRank: 8,
    positionRank: 3,
    tier: 3,
    adp: 62,
    vorp: 0,
  },
  {
    playerId: "te_002",
    fullName: "Example TE Two",
    position: "TE",
    team: "JJJ",
    projectedPoints: 145,
    overallRank: 9,
    positionRank: 2,
    tier: 3,
    adp: 95,
    vorp: 0,
  },
  {
    playerId: "k_001",
    fullName: "Example K One",
    position: "K",
    team: "LLL",
    projectedPoints: 135,
    overallRank: 10,
    positionRank: 1,
    tier: 1,
    adp: 155,
    vorp: 0,
  },
  {
    playerId: "dst_001",
    fullName: "Example DST One",
    position: "DST",
    team: "KKK",
    projectedPoints: 118,
    overallRank: 11,
    positionRank: 1,
    tier: 1,
    adp: 150,
    vorp: 0,
  },
  {
    playerId: "qb_002",
    fullName: "Example QB Two",
    position: "QB",
    team: "BBB",
    projectedPoints: 295,
    overallRank: 12,
    positionRank: 2,
    tier: 2,
    adp: 78,
    vorp: 0,
  },
];

export const initialDraftRoomState: DraftRoomState = {
  completedPicks: [],
  undoStack: [],
  redoStack: [],
};

export function pickSlot(overallPick: number) {
  const round = Math.floor((overallPick - 1) / managers.length) + 1;
  const indexInRound = (overallPick - 1) % managers.length;
  const managerIndex = round % 2 === 1 ? indexInRound : managers.length - indexInRound - 1;
  return {
    overallPick,
    round,
    roundPick: indexInRound + 1,
    managerId: managers[managerIndex],
  };
}

export function availablePlayers(state: DraftRoomState) {
  const draftedIds = new Set(state.completedPicks.map((pick) => pick.playerId));
  return players.filter((player) => !draftedIds.has(player.playerId));
}

export function recordPick(state: DraftRoomState, playerId: string): DraftRoomState {
  if (state.completedPicks.some((pick) => pick.playerId === playerId)) {
    throw new Error("player already drafted");
  }
  const slot = pickSlot(state.completedPicks.length + 1);
  return {
    completedPicks: [
      ...state.completedPicks,
      {
        overallPick: slot.overallPick,
        round: slot.round,
        roundPick: slot.roundPick,
        managerId: slot.managerId,
        playerId,
      },
    ],
    undoStack: [...state.undoStack, state.completedPicks],
    redoStack: [],
  };
}

export function undo(state: DraftRoomState): DraftRoomState {
  const previous = state.undoStack[state.undoStack.length - 1];
  if (!previous) {
    return state;
  }
  return {
    completedPicks: previous,
    undoStack: state.undoStack.slice(0, -1),
    redoStack: [state.completedPicks, ...state.redoStack],
  };
}

export function redo(state: DraftRoomState): DraftRoomState {
  const next = state.redoStack[0];
  if (!next) {
    return state;
  }
  return {
    completedPicks: next,
    undoStack: [...state.undoStack, state.completedPicks],
    redoStack: state.redoStack.slice(1),
  };
}

export function rosterForManager(state: DraftRoomState, managerId: string) {
  const playerById = new Map(players.map((player) => [player.playerId, player]));
  return state.completedPicks
    .filter((pick) => pick.managerId === managerId)
    .map((pick) => playerById.get(pick.playerId))
    .filter((player): player is Player => player !== undefined);
}

export function explainRecommendation(player: Player, completedPickCount: number) {
  const nextPick = nextUserPick(completedPickCount);
  const picksUntilUser = typeof nextPick === "number" ? nextPick - completedPickCount - 1 : 0;
  const availability = Math.max(
    2,
    Math.min(98, Math.round(((player.adp - completedPickCount) / Math.max(picksUntilUser, 1) / 3) * 100)),
  );
  const notes = [
    `${player.position}${player.positionRank} with ${player.projectedPoints} projected points.`,
    `${player.vorp.toFixed(1)} points over replacement in the baseline model.`,
    `Estimated ${availability}% chance to last to the next user pick.`,
  ];
  if (player.tier === 1) {
    notes.push("Top tier at the position.");
  }
  if (player.position === "K" || player.position === "DST") {
    notes.push("Early K/DST penalty applies.");
  }
  return notes;
}

export function candidateRollouts(state: DraftRoomState, limit = 4): CandidateRollout[] {
  const slot = pickSlot(state.completedPicks.length + 1);
  if (slot.managerId !== "Primary User") {
    return [];
  }

  const draftedByUser = rosterForManager(state, "Primary User");
  const rosterVorp = draftedByUser.reduce((total, player) => total + player.vorp, 0);
  return availablePlayers(state)
    .slice(0, Math.max(limit * 2, limit))
    .map((player) => {
      const needBoost = starterNeedBoost(player, draftedByUser);
      const marketBoost = Math.max(player.adp - player.overallRank, 0) * 0.2;
      const averageVorp = rosterVorp + player.vorp + needBoost;
      const averageProjectedPoints =
        draftedByUser.reduce((total, rosterPlayer) => total + rosterPlayer.projectedPoints, 0) +
        player.projectedPoints;
      return {
        playerId: player.playerId,
        optimizerScore: Number((averageVorp + marketBoost).toFixed(2)),
        averageProjectedPoints: Number(averageProjectedPoints.toFixed(2)),
        averageVorp: Number(averageVorp.toFixed(2)),
        explanation: [
          `${player.position}${player.positionRank} rollout candidate.`,
          `${averageVorp.toFixed(1)} projected roster VORP after this pick.`,
          `${marketBoost.toFixed(1)} market value boost versus ADP.`,
        ],
      };
    })
    .sort((left, right) => right.optimizerScore - left.optimizerScore || left.averageProjectedPoints - right.averageProjectedPoints)
    .slice(0, limit);
}

function starterNeedBoost(player: Player, roster: Player[]) {
  const starterTargets: Record<Position, number> = {
    QB: 1,
    RB: 2,
    WR: 2,
    TE: 1,
    DST: 1,
    K: 1,
  };
  const currentCount = roster.filter((item) => item.position === player.position).length;
  return currentCount < starterTargets[player.position] ? 12 : 0;
}

export function nextUserPick(completedPickCount: number) {
  for (let pick = completedPickCount + 1; pick <= totalDraftPicks; pick += 1) {
    if (pickSlot(pick).managerId === "Primary User") {
      return pick;
    }
  }
  return "-";
}

export function saveDraftRoomState(state: DraftRoomState, storage: Storage = localStorage) {
  storage.setItem(storageKey, JSON.stringify(state));
}

export function loadDraftRoomState(storage: Storage = localStorage): DraftRoomState | null {
  const rawState = storage.getItem(storageKey);
  if (!rawState) {
    return null;
  }

  const parsed = JSON.parse(rawState) as DraftRoomState;
  if (!Array.isArray(parsed.completedPicks)) {
    return null;
  }
  return {
    completedPicks: parsed.completedPicks,
    undoStack: Array.isArray(parsed.undoStack) ? parsed.undoStack : [],
    redoStack: Array.isArray(parsed.redoStack) ? parsed.redoStack : [],
  };
}
