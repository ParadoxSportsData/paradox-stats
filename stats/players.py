"""PDX-33: Temporally-gated player statistics aggregator — QB/RB/WR/TE/K."""
from typing import Optional

import pandas as pd


def _passer_rating(comp: int, att: int, yards: int, tds: int, ints: int) -> Optional[float]:
    if att == 0:
        return None
    a = ((comp / att) - 0.3) * 5
    b = ((yards / att) - 3) * 0.25
    c = (tds / att) * 20
    d = 2.375 - (ints / att) * 25
    raw = ((a + b + c + d) / 6) * 100
    return float(max(0.0, min(158.3, raw)))


def _isum(s: pd.Series) -> int:
    return int(s.fillna(0).sum())


def _imax(s: pd.Series) -> int:
    return int(s.max()) if len(s) > 0 else 0


def _aggregate_qbs(plays: pd.DataFrame) -> list:
    pass_plays = plays[plays["pass_attempt"] == 1]
    sack_plays = plays[plays["sack"] == 1]

    if pass_plays.empty:
        return []

    grp = (
        pass_plays.groupby(["passer_player_id", "passer_player_name"], dropna=True)
        .agg(
            completions=("complete_pass", "sum"),
            attempts=("pass_attempt", "sum"),
            pass_yards=("passing_yards", "sum"),
            pass_tds=("pass_touchdown", "sum"),
            interceptions=("interception", "sum"),
        )
        .reset_index()
    )

    sack_grp = (
        sack_plays.groupby("passer_player_id", dropna=True)
        .agg(sacks_taken=("sack", "sum"))
        .reset_index()
    ) if not sack_plays.empty else pd.DataFrame(columns=["passer_player_id", "sacks_taken"])

    # Rush stats for QBs
    rush_plays = plays[plays["rush_attempt"] == 1]
    rush_grp = (
        rush_plays.groupby("rusher_player_id", dropna=True)
        .agg(rush_yards=("rushing_yards", "sum"), rush_attempts=("rush_attempt", "sum"))
        .reset_index()
        .rename(columns={"rusher_player_id": "passer_player_id"})
    ) if not rush_plays.empty else pd.DataFrame(
        columns=["passer_player_id", "rush_yards", "rush_attempts"]
    )

    merged = grp.merge(sack_grp, on="passer_player_id", how="left")
    merged = merged.merge(rush_grp, on="passer_player_id", how="left")
    merged["sacks_taken"] = merged["sacks_taken"].fillna(0).astype(int)
    merged["rush_yards"] = merged["rush_yards"].fillna(0).astype(int)
    merged["rush_attempts"] = merged["rush_attempts"].fillna(0).astype(int)

    result = []
    for row in merged.itertuples(index=False):
        comp = int(row.completions)
        att = int(row.attempts)
        yards = int(row.pass_yards) if not pd.isna(row.pass_yards) else 0
        tds = int(row.pass_tds)
        ints = int(row.interceptions)
        result.append({
            "player_id": str(row.passer_player_id),
            "name": str(row.passer_player_name),
            "pass_yards": yards,
            "completions": comp,
            "attempts": att,
            "pass_tds": tds,
            "interceptions": ints,
            "passer_rating": _passer_rating(comp, att, yards, tds, ints),
            "sacks_taken": int(row.sacks_taken),
            "rush_yards": int(row.rush_yards),
            "rush_attempts": int(row.rush_attempts),
        })
    return result


def _aggregate_rbs(plays: pd.DataFrame) -> list:
    rush_plays = plays[plays["rush_attempt"] == 1]
    if rush_plays.empty:
        return []

    rush_grp = (
        rush_plays.groupby(["rusher_player_id", "rusher_player_name"], dropna=True)
        .agg(
            carries=("rush_attempt", "sum"),
            rush_yards=("rushing_yards", "sum"),
            rush_tds=("rush_touchdown", "sum"),
        )
        .reset_index()
    )

    rb_ids = set(rush_grp["rusher_player_id"].tolist())

    pass_plays = plays[plays["pass_attempt"] == 1]
    rec_grp = (
        pass_plays[pass_plays["receiver_player_id"].isin(rb_ids)]
        .groupby("receiver_player_id", dropna=True)
        .agg(
            receptions=("complete_pass", "sum"),
            rec_yards=("receiving_yards", "sum"),
            rec_tds=("pass_touchdown", "sum"),
        )
        .reset_index()
        .rename(columns={"receiver_player_id": "rusher_player_id"})
    ) if not pass_plays.empty else pd.DataFrame(
        columns=["rusher_player_id", "receptions", "rec_yards", "rec_tds"]
    )

    merged = rush_grp.merge(rec_grp, on="rusher_player_id", how="left")
    merged["receptions"] = merged["receptions"].fillna(0).astype(int)
    merged["rec_yards"] = merged["rec_yards"].fillna(0).astype(int)
    merged["rec_tds"] = merged["rec_tds"].fillna(0).astype(int)

    result = []
    for row in merged.itertuples(index=False):
        carries = int(row.carries)
        receptions = int(row.receptions)
        if carries == 0 and receptions == 0:
            continue
        result.append({
            "player_id": str(row.rusher_player_id),
            "name": str(row.rusher_player_name),
            "carries": carries,
            "rush_yards": int(row.rush_yards) if not pd.isna(row.rush_yards) else 0,
            "rush_tds": int(row.rush_tds),
            "receptions": receptions,
            "rec_yards": int(row.rec_yards),
            "rec_tds": int(row.rec_tds),
        })
    return result


def _aggregate_wr_te(plays: pd.DataFrame, rb_ids: set) -> list:
    pass_plays = plays[plays["pass_attempt"] == 1]
    if pass_plays.empty:
        return []

    grp = (
        pass_plays[~pass_plays["receiver_player_id"].isin(rb_ids)]
        .groupby(["receiver_player_id", "receiver_player_name"], dropna=True)
        .agg(
            targets=("pass_attempt", "sum"),
            receptions=("complete_pass", "sum"),
            rec_yards=("receiving_yards", "sum"),
            rec_tds=("pass_touchdown", "sum"),
        )
        .reset_index()
    )

    result = []
    for row in grp.itertuples(index=False):
        targets = int(row.targets)
        if targets == 0:
            continue
        result.append({
            "player_id": str(row.receiver_player_id),
            "name": str(row.receiver_player_name),
            "targets": targets,
            "receptions": int(row.receptions),
            "rec_yards": int(row.rec_yards) if not pd.isna(row.rec_yards) else 0,
            "rec_tds": int(row.rec_tds),
        })
    return result


def _aggregate_kickers(plays: pd.DataFrame) -> list:
    k_plays = plays[
        (plays["field_goal_attempt"] == 1) | (plays["extra_point_attempt"] == 1)
    ]
    if k_plays.empty:
        return []

    grp = (
        k_plays.groupby(["kicker_player_id", "kicker_player_name"], dropna=True)
        .agg(
            fg_att=("field_goal_attempt", "sum"),
            xp_att=("extra_point_attempt", "sum"),
        )
        .reset_index()
    )

    result = []
    for _, row in grp.iterrows():
        kid = row["kicker_player_id"]
        fg_att = int(row["fg_att"])
        xp_att = int(row["xp_att"])
        if fg_att == 0 and xp_att == 0:
            continue

        player_plays = k_plays[k_plays["kicker_player_id"] == kid]
        made_fgs = player_plays[player_plays["field_goal_result"] == "made"]
        fg_made = len(made_fgs)
        fg_long = _imax(made_fgs["kick_distance"]) if not made_fgs.empty else 0
        xp_made = int((player_plays["extra_point_result"] == "good").sum())

        result.append({
            "player_id": str(kid),
            "name": str(row["kicker_player_name"]),
            "fg_made": fg_made,
            "fg_att": fg_att,
            "fg_long": fg_long,
            "xp_made": xp_made,
            "xp_att": xp_att,
        })
    return result


def aggregate_player_stats(
    pbp: pd.DataFrame, game_id: str, tick: int, team: str
) -> dict:
    """Return {qb, rb, wr_te, k} lists for team at elapsed tick in game_id."""
    plays = pbp[
        (pbp["game_id"] == game_id)
        & (pbp["game_clock_total_seconds"] <= tick)
        & (pbp["posteam"] == team)
    ]

    qbs = _aggregate_qbs(plays)
    rbs = _aggregate_rbs(plays)
    rb_ids = {rb["player_id"] for rb in rbs}
    wr_tes = _aggregate_wr_te(plays, rb_ids)
    ks = _aggregate_kickers(plays)

    return {"qb": qbs, "rb": rbs, "wr_te": wr_tes, "k": ks}
