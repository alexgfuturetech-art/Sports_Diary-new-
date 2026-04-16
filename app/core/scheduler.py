"""
scheduler.py – APScheduler background jobs for automatic tournament status transitions.

Runs every 5 minutes and applies the following rules in order:

1. upcoming → registration_closed
   Condition: now > registration_deadline

2. registration_closed → cancelled (insufficient_registrations)
   Condition: now > registration_deadline AND current_teams < min_teams
   (min_teams defaults to 2 when not set)

3. upcoming | registration_closed | postponed → ongoing
   Condition: now >= start_date  (only if not already cancelled)

4. ongoing → completed
   Condition: now > end_date

5. upcoming | registration_closed → cancelled (no_show)
   Condition: now > end_date AND zero matches recorded
"""

from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import get_database

_scheduler: AsyncIOScheduler | None = None


# ─── helpers ──────────────────────────────────────────────────────────────────

def _now() -> datetime:
    """UTC-aware now, stripped to naive for MongoDB comparisons (stored naive)."""
    return datetime.utcnow()


async def _set_status(db, tournament_id, status: str, extra: dict | None = None) -> None:
    patch = {"status": status, "updated_at": _now(), **(extra or {})}
    await db.tournaments.update_one({"_id": tournament_id}, {"$set": patch})


# ─── main job ─────────────────────────────────────────────────────────────────

async def _run_transitions() -> None:
    db = get_database()
    now = _now()
    updated = 0

    # ── 1. upcoming → registration_closed ────────────────────────────────────
    result = await db.tournaments.update_many(
        {
            "status": "upcoming",
            "is_active": True,
            "registration_deadline": {"$lt": now},
        },
        {"$set": {"status": "registration_closed", "updated_at": now}},
    )
    updated += result.modified_count

    # ── 2. registration_closed → cancelled (insufficient_registrations) ───────
    # We must evaluate per-tournament because min_teams varies.
    async for t in db.tournaments.find(
        {
            "status": "registration_closed",
            "is_active": True,
            "registration_deadline": {"$lt": now},
        },
        {"_id": 1, "current_teams": 1, "min_teams": 1},
    ):
        min_teams = t.get("min_teams") or 2
        if (t.get("current_teams") or 0) < min_teams:
            await _set_status(
                db,
                t["_id"],
                "cancelled",
                {
                    "cancellation_reason": "insufficient_registrations",
                    "cancelled_at": now,
                },
            )
            updated += 1

    # ── 3. upcoming | registration_closed | postponed → ongoing ──────────────
    result = await db.tournaments.update_many(
        {
            "status": {"$in": ["upcoming", "registration_closed", "postponed"]},
            "is_active": True,
            "start_date": {"$lte": now},
        },
        {"$set": {"status": "ongoing", "updated_at": now}},
    )
    updated += result.modified_count

    # ── 4. ongoing → completed ────────────────────────────────────────────────
    result = await db.tournaments.update_many(
        {
            "status": "ongoing",
            "is_active": True,
            "end_date": {"$lt": now},
        },
        {"$set": {"status": "completed", "updated_at": now}},
    )
    updated += result.modified_count

    # ── 5. upcoming | registration_closed → cancelled (no_show) ──────────────
    # Tournaments whose end_date passed but never had a single match played.
    async for t in db.tournaments.find(
        {
            "status": {"$in": ["upcoming", "registration_closed"]},
            "is_active": True,
            "end_date": {"$lt": now},
        },
        {"_id": 1},
    ):
        match_count = await db.matches.count_documents(
            {"tournament_id": str(t["_id"])}
        )
        if match_count == 0:
            await _set_status(
                db,
                t["_id"],
                "cancelled",
                {
                    "cancellation_reason": "no_show",
                    "cancelled_at": now,
                },
            )
            updated += 1

    if updated:
        print(f"[SCHEDULER] Tournament transitions applied: {updated}")


# ─── public API ───────────────────────────────────────────────────────────────

def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")
    # Run once immediately on startup to process any backlog, then every 5 min.
    _scheduler.add_job(
        _run_transitions,
        trigger="interval",
        minutes=5,
        id="tournament_transitions",
        replace_existing=True,
        next_run_time=datetime.utcnow(),  # fire immediately on first tick
    )
    _scheduler.start()
    print("✅ Tournament scheduler started (runs now + every 5 minutes)")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("⏹  Tournament scheduler stopped")
