"""Simple approval store for recommendations."""
import json
import os
import threading
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime


_STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "approvals.json")
_LOCK = threading.Lock()


def _ensure_store() -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    if not os.path.exists(_STORE_PATH):
        with open(_STORE_PATH, "w", encoding="utf-8") as handle:
            json.dump([], handle)


def _load() -> List[Dict[str, Any]]:
    _ensure_store()
    with open(_STORE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _save(items: List[Dict[str, Any]]) -> None:
    _ensure_store()
    with open(_STORE_PATH, "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2)


def list_recommendations(status: Optional[str] = None) -> List[Dict[str, Any]]:
    with _LOCK:
        items = _load()
        if status:
            return [i for i in items if i.get("status") == status]
        return items


def add_recommendations(recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    with _LOCK:
        items = _load()
        existing_ids = {item.get("id") for item in items if item.get("id")}
        new_items = []
        for rec in recs:
            def _format_savings(value: Any) -> Optional[str]:
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    return f"${value:,.2f}"
                if isinstance(value, str) and value.strip():
                    return value
                return None

            estimated_savings = rec.get("estimated_savings")
            if estimated_savings is None:
                for key in ("estimated_savings_monthly", "estimated_monthly_savings_usd", "estimated_savings_annual", "estimated_annual_savings_usd"):
                    if isinstance(rec.get(key), (int, float)):
                        estimated_savings = rec.get(key)
                        break

            rec_id = rec.get("id") or f"rec_{uuid4().hex}"
            if rec_id in existing_ids:
                continue
            enriched = {
                **rec,
                "estimated_savings": _format_savings(estimated_savings) or rec.get("estimated_savings"),
                "id": rec_id,
                "status": rec.get("status", "PENDING"),
                "created_at": rec.get("created_at", now),
                "updated_at": rec.get("updated_at", now),
            }
            items.append(enriched)
            new_items.append(enriched)
        _save(items)
        return new_items


def update_status(rec_id: str, status: str, note: Optional[str] = None) -> Optional[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    with _LOCK:
        items = _load()
        for item in items:
            if item.get("id") == rec_id:
                item["status"] = status
                item["updated_at"] = now
                if note:
                    item["status_note"] = note
                _save(items)
                return item
        return None


def get_recommendation(rec_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        items = _load()
        for item in items:
            if item.get("id") == rec_id:
                return item
        return None
