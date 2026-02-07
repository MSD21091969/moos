"""Quota management service for tracking and enforcing usage limits."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from google.cloud import firestore

from src.core.logging import get_logger
from src.models.permissions import Tier, get_quota_limit

if TYPE_CHECKING:
    from src.models.quota import QuotaUsageSummary, DailyUsage

logger = get_logger(__name__)


class QuotaService:
    """Service for managing user quota."""

    def __init__(self, db: firestore.Client):
        """
        Initialize quota service.

        Args:
            db: Firestore client
        """
        self.db = db

    async def get_remaining_quota(self, user_id: str, tier: str) -> int:
        """
        Get remaining quota for user today.

        Args:
            user_id: User identifier
            tier: User tier (free/pro/enterprise)

        Returns:
            Remaining quota units

        Note:
            Quota resets daily at midnight UTC.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"{user_id}_{today}"

        try:
            doc_ref = self.db.collection("quota").document(quota_doc_id)
            doc = await doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                used = data.get("used", 0)
            else:
                used = 0

            # Get daily limit from tier
            tier_enum = Tier(tier) if isinstance(tier, str) else tier
            daily_limit = get_quota_limit(tier_enum)

            return max(0, daily_limit - used)

        except Exception as e:
            logger.error(
                "Failed to get quota for user", extra={"user_id": user_id, "error": str(e)}
            )
            # Return safe default on error
            return 0

    async def deduct_quota(self, user_id: str, tier: str, amount: int) -> int:
        """
        Deduct quota from user's daily allowance.

        Args:
            user_id: User identifier
            tier: User tier
            amount: Quota units to deduct

        Returns:
            Remaining quota after deduction

        Raises:
            ValueError: If insufficient quota

        Note:
            Uses Firestore transaction to prevent race conditions.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"{user_id}_{today}"

        try:
            doc_ref = self.db.collection("quota").document(quota_doc_id)

            @firestore.transactional
            async def deduct_in_transaction(transaction):
                """Deduct quota atomically."""
                snapshot = await doc_ref.get(transaction=transaction)

                if snapshot.exists:
                    data = snapshot.to_dict()
                    used = data.get("used", 0)
                else:
                    used = 0

                # Check if deduction would exceed limit
                tier_enum = Tier(tier) if isinstance(tier, str) else tier
                daily_limit = get_quota_limit(tier_enum)
                new_used = used + amount

                if new_used > daily_limit:
                    remaining = daily_limit - used
                    raise ValueError(f"Insufficient quota: need {amount}, have {remaining}")

                # Update quota usage
                transaction.set(
                    doc_ref,
                    {
                        "user_id": user_id,
                        "tier": tier,
                        "date": today,
                        "used": new_used,
                        "daily_limit": daily_limit,
                        "updated_at": datetime.now(timezone.utc),
                    },
                )

                return daily_limit - new_used

            # Execute transaction
            transaction = self.db.transaction()
            remaining = await deduct_in_transaction(transaction)

            logger.info(
                "Deducted quota from user",
                extra={"amount": amount, "user_id": user_id, "remaining": remaining},
            )

            return remaining

        except ValueError:
            # Re-raise quota errors
            raise
        except Exception as e:
            logger.error(
                "Failed to deduct quota for user", extra={"user_id": user_id, "error": str(e)}
            )
            raise

    async def get_quota_usage(self, user_id: str, days: int = 7) -> list[dict]:
        """
        Get quota usage history for user.

        Args:
            user_id: User identifier
            days: Number of days to retrieve

        Returns:
            List of daily usage records
        """
        try:
            docs = (
                self.db.collection("quota")
                .where("user_id", "==", user_id)
                .order_by("date")
                .limit(days)
                .stream()
            )

            usage = []
            async for doc in docs:
                data = doc.to_dict()
                usage.append(
                    {
                        "date": data.get("date"),
                        "used": data.get("used", 0),
                        "daily_limit": data.get("daily_limit", 100),
                        "tier": data.get("tier", "free"),
                    }
                )

            return usage

        except Exception as e:
            logger.error(
                "Failed to get quota usage for user", extra={"user_id": user_id, "error": str(e)}
            )
            return []

    async def get_usage(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> "QuotaUsageSummary":
        """
        Get quota usage summary for date range.

        Args:
            user_id: User identifier
            start_date: Start of range (default: today)
            end_date: End of range (default: today)

        Returns:
            QuotaUsageSummary with aggregated usage
        """
        from src.models.quota import QuotaUsageSummary

        # Default to today if not specified
        if not start_date:
            start_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if not end_date:
            end_date = datetime.now(timezone.utc)

        start_date_str = start_date.date().isoformat()
        end_date_str = end_date.date().isoformat()

        try:
            # Query quota records in date range
            docs = (
                self.db.collection("quota")
                .where("user_id", "==", user_id)
                .where("date", ">=", start_date_str)
                .where("date", "<=", end_date_str)
                .stream()
            )

            total_used = 0
            total_limit = 0
            daily_breakdown = []

            async for doc in docs:
                data = doc.to_dict()
                used = data.get("used", 0)
                limit = data.get("daily_limit", 100)

                total_used += used
                total_limit += limit

                daily_breakdown.append({"date": data.get("date"), "used": used, "limit": limit})

            # If no records, use tier defaults
            if total_limit == 0:
                # Get user tier
                user_ref = self.db.collection("users").document(user_id)
                user_doc = await user_ref.get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    tier_str = user_data.get("tier", "free")
                    tier = Tier(tier_str)
                    total_limit = get_quota_limit(tier)

            return QuotaUsageSummary(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                total_used=total_used,
                total_limit=total_limit,
                remaining=max(0, total_limit - total_used),
                breakdown_by_day=daily_breakdown,
            )

        except Exception as e:
            logger.error(
                "Failed to get usage for user", extra={"user_id": user_id, "error": str(e)}
            )
            # Return empty summary on error
            from src.models.quota import QuotaUsageSummary

            return QuotaUsageSummary(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                total_used=0,
                total_limit=100,
                remaining=100,
                breakdown_by_day=[],
            )

    async def get_usage_history(self, user_id: str, days: int = 30) -> list["DailyUsage"]:
        """
        Get daily quota usage history.

        Args:
            user_id: User identifier
            days: Number of days to retrieve (default: 30)

        Returns:
            List of DailyUsage records, newest first
        """
        from src.models.quota import DailyUsage

        try:
            docs = (
                self.db.collection("quota")
                .where("user_id", "==", user_id)
                .order_by("date")
                .limit(days)
                .stream()
            )

            history = []
            async for doc in docs:
                data = doc.to_dict()
                history.append(
                    DailyUsage(
                        date=data.get("date"),
                        quota_used=data.get("used", 0),
                        quota_limit=data.get("daily_limit", 100),
                        tier=data.get("tier", "free"),
                    )
                )

            return history

        except Exception as e:
            logger.error(
                "Failed to get usage history for user", extra={"user_id": user_id, "error": str(e)}
            )
            return []
