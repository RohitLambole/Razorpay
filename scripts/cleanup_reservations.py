"""A small cleanup script to release expired inventory reservations.
Run periodically (cron/runner) to avoid locking inventory forever.
"""
from datetime import datetime
from app import db


def cleanup_expired_reservations():
    now_iso = datetime.utcnow().isoformat()
    # select expired reservations
    resp = db.supabase.table("inventory_reservations").select("*").lt("expires_at", now_iso).execute()
    rows = resp.data or []
    for r in rows:
        # delete reservation
        try:
            db.supabase.table("inventory_reservations").delete().eq("reservation_id", r["reservation_id"]).execute()
        except Exception:
            continue
        # create audit event for release
        try:
            db.create_audit_event({
                "merchant_id": r.get("merchant_id"),
                "session_id": None,
                "actor": "system",
                "action": "release_expired_reservation",
                "payload": r
            })
        except Exception:
            pass


if __name__ == "__main__":
    cleanup_expired_reservations()
