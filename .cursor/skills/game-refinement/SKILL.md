---
name: game-refinement
description: Guides game design and implementation using a refinement checklist and agent rules. Use when creating or improving browser games, puzzle games, or when the user asks for game polish, UX, or playability improvements.
---

# Game Refinement Skill

## When to use

- User is building or refining a game (especially HTML/JS puzzle or casual games).
- User mentions playability, UX, scoring feedback, or documentation for games.
- User refers to "game-refinement checklist", "agent-game", or "Apple Sum 10" style rules.

## Instructions

1. **Read project docs** (if present):
   - [docs/game-refinement-checklist.md](../../docs/game-refinement-checklist.md) – refinement questions and categories.
   - [docs/agent-game.md](../../docs/agent-game.md) – role, checklist, rules, and example project.

2. **Apply the checklist** when implementing or changing game logic/UI:
   - Playability: at least one valid move always possible; refresh/hint strategy; clear game-over.
   - Input UX: no drag/selection residue; correct selection model (e.g. snake path).
   - Visuals: simple icons, readable numbers, clear selection feedback.
   - Feedback: floating score, sound, score formula (e.g. more cells = more points).
   - Docs: spec + full source in one md for exact reproduction.

3. **Follow agent-game rules** for puzzle/casual games:
   - Guarantee valid combos on init and after refill (e.g. seed + hasValidMove).
   - Use user-select/user-drag none and preventDefault for drag.
   - Floating score at last-removed position, high z-index, box style.
   - Document in md with full HTML/JS so another AI can rebuild the same game.

4. **Suggest or implement** only what the user asked for; use the checklist to spot gaps and offer one concrete improvement at a time if relevant.

## Quick reference

| Category        | Key points |
|----------------|------------|
| Playability    | Min 1 valid combo; refresh limit; game over when no moves. |
| Input UX       | Snake/adjacent selection; no selection residue. |
| Visuals        | Simple CSS icon; selection = border + scale + shadow. |
| Feedback       | Score = f(cell count); floating score + sound. |
| Documentation  | One md: rules + full source for reproducibility. |

## Example prompt for user

> "`docs/game-refinement-checklist.md` 기준으로 이 게임 설계/구현/고도화해 줘. 필요하면 `docs/agent-game.md` 참고해."
