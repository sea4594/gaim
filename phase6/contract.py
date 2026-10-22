"""Executable Phase 6 planning contract against the frozen Phase 5 engine.

This module does NOT implement network rooms, identity, persistence, timers, or
security. It validates proposed shared plans and creates public player views.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from reference.charge_loom_v01 import State, Token, arrivals, step


RULESET = "charge-loom/v0.1"
PROTOCOL_VERSION = 1


class ContractError(ValueError):
    """A command or planned edit fails the Phase 6 contract."""


def require_integer(value: Any, label: str) -> int:
    if type(value) is not int:
        raise ContractError(f"{label} must be an integer")
    return value


def slot_owners(player_count: int, round_number: int) -> tuple[int, int, int, int]:
    """Four team slots: equitable round-robin ownership for 1..4 seats.

    The second slot assigned to one seat in three-player games rotates each
    round. Seat numbers are fixed from game start and zero indexed.
    """
    require_integer(player_count, "player_count")
    require_integer(round_number, "round_number")
    if not 1 <= player_count <= 4 or not 1 <= round_number <= 9:
        raise ContractError("player_count or round_number out of range")
    start = (round_number - 1) % player_count
    return tuple((start + offset) % player_count for offset in range(4))


def normalize_edit(action: dict[str, Any]) -> tuple:
    if not isinstance(action, dict) or not isinstance(action.get("kind"), str):
        raise ContractError("action must include a kind")
    kind = action["kind"]
    if kind == "SHIFT":
        if set(action) != {"kind", "tokenId", "direction"}:
            raise ContractError("SHIFT fields invalid")
        token_id = require_integer(action["tokenId"], "tokenId")
        direction = require_integer(action["direction"], "direction")
        if direction not in (-1, 1):
            raise ContractError("SHIFT direction must be -1 or +1")
        return ("shift", token_id, direction)
    if kind in ("HOLD", "DAMP"):
        if set(action) != {"kind", "tokenId"}:
            raise ContractError(f"{kind} fields invalid")
        return (kind.lower(), require_integer(action["tokenId"], "tokenId"))
    raise ContractError("unknown action kind")


def validate_plan(
    state: State, player_count: int, drafts: list[dict[str, Any]]
) -> tuple[tuple, ...]:
    """Validate all slot proposals atomically, return engine actions in slot order.

    Missing slots are PASS. Ready state/seat authentication must be enforced
    by the room server before it calls this function.
    """
    if state.over or state.round >= 9:
        raise ContractError("game ended")
    if not isinstance(drafts, list) or len(drafts) > 4:
        raise ContractError("at most four slot proposals")
    owners = slot_owners(player_count, state.round + 1)
    seen_slots: set[int] = set()
    edits: list[tuple[int, tuple]] = []
    for draft in drafts:
        if not isinstance(draft, dict) or set(draft) != {"slot", "seat", "action"}:
            raise ContractError("draft fields invalid")
        slot = require_integer(draft["slot"], "slot")
        seat = require_integer(draft["seat"], "seat")
        if not 0 <= slot < 4 or slot in seen_slots:
            raise ContractError("duplicate or out-of-range slot")
        if owners[slot] != seat:
            raise ContractError("slot not owned by submitting seat")
        seen_slots.add(slot)
        edits.append((slot, normalize_edit(draft["action"])))
    actions = tuple(action for _, action in sorted(edits))
    try:
        step(state, actions)
    except (ValueError, IndexError, TypeError, KeyError) as exc:
        raise ContractError(f"illegal combined plan: {exc}") from exc
    return actions


def current_charges(state: State) -> tuple[Token, ...]:
    """Show the next round's arrivals as editable BEFORE the team commits.

    IDs are reserved deterministically; this view must never mutate state.
    """
    if state.over:
        return tuple(sorted(state.tokens))
    next_id = state.next_id
    incoming = tuple(
        Token(next_id + i, lane, 2, polarity, size)
        for i, (lane, polarity, size) in enumerate(arrivals(state.seed, state.round + 1))
    )
    return tuple(sorted(state.tokens + incoming))


def public_view(state: State, player_count: int) -> dict[str, Any]:
    """Stable, seed-free projection; excludes private wavebook and witness path."""
    finished = bool(state.over)
    charges = [
        {
            "id": token.id,
            "lane": token.lane,
            "band": token.row,
            "polarity": "POSITIVE" if token.sign == 1 else "NEGATIVE",
            "strength": token.size,
            "alreadyHeld": bool(token.held),
        }
        for token in current_charges(state)
    ]
    preview = [] if finished else [
        {
            "lane": lane,
            "polarity": "POSITIVE" if sign == 1 else "NEGATIVE",
            "strength": size,
        }
        for lane, sign, size in arrivals(state.seed, state.round + 2)
    ]
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "ruleset": RULESET,
        "completedRound": state.round,
        "planningRound": None if finished else state.round + 1,
        "hull": state.hp,
        "capacitors": list(state.progress),
        "coolant": state.coolant,
        "charges": charges,
        "nextWave": preview,
        "slotOwners": [] if finished else list(slot_owners(player_count, state.round + 1)),
        "outcome": state.over if finished else None,
    }
