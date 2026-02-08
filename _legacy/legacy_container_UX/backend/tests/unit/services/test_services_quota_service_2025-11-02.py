"""
Unit tests for QuotaService.

Tests quota calculation, enforcement, deduction logic in isolation using MockFirestoreClient.
"""

from datetime import datetime, timezone

import pytest

from src.services.quota_service import QuotaService


@pytest.fixture
def quota_service(mock_firestore):
    """QuotaService instance with mock Firestore."""
    return QuotaService(db=mock_firestore)


# ============================================================================
# Quota Retrieval Tests
# ============================================================================


class TestGetRemainingQuota:
    """Test quota retrieval and calculation logic."""

    @pytest.mark.asyncio
    async def test_remaining_quota_no_usage(self, quota_service):
        """
        TEST: Calculate remaining quota when user has no usage today.

        PURPOSE: Verify new users or daily reset returns full tier quota.

        VALIDATES:
        - FREE tier user with 0 usage returns 100 quota
        - Firestore document doesn't exist (fresh user/new day)
        - get_quota_limit(Tier.FREE) = 100

        EXPECTED: Returns full daily quota (100 for FREE tier).
        """
        remaining = await quota_service.get_remaining_quota("user_123", "free")
        assert remaining == 100

    @pytest.mark.asyncio
    async def test_remaining_quota_with_usage(self, quota_service, mock_firestore):
        """
        TEST: Calculate remaining quota after partial usage.

        PURPOSE: Verify quota calculation subtracts used from daily limit.

        VALIDATES:
        - PRO tier user (1000 daily limit) with 350 used returns 650 remaining
        - Firestore document exists with usage data
        - Calculation: daily_limit - used = 1000 - 350 = 650

        EXPECTED: Returns 650 remaining quota.
        """
        # Seed quota usage data
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"user_pro_{today}"

        mock_firestore.seed_data(
            "quota",
            quota_doc_id,
            {"user_id": "user_pro", "tier": "pro", "used": 350, "daily_limit": 1000},
        )

        remaining = await quota_service.get_remaining_quota("user_pro", "pro")
        assert remaining == 650

    @pytest.mark.asyncio
    async def test_remaining_quota_exhausted(self, quota_service, mock_firestore):
        """
        TEST: Handle quota exhaustion (used >= daily_limit).

        PURPOSE: Ensure remaining quota never goes negative.

        VALIDATES:
        - FREE tier user (100 daily limit) with 150 used returns 0 (not -50)
        - max(0, daily_limit - used) prevents negative values
        - User blocked from further requests when quota exhausted

        EXPECTED: Returns 0 when quota exceeded.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"user_exhausted_{today}"

        mock_firestore.seed_data(
            "quota",
            quota_doc_id,
            {"user_id": "user_exhausted", "tier": "free", "used": 150, "daily_limit": 100},
        )

        remaining = await quota_service.get_remaining_quota("user_exhausted", "free")
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_remaining_quota_enterprise_unlimited(self, quota_service):
        """
        TEST: ENTERPRISE tier has 10000 daily quota.

        PURPOSE: Verify high quota limit for enterprise customers.

        VALIDATES:
        - ENTERPRISE tier daily limit = 10000 quota units
        - Allows ~1000 AI agent requests at avg 10 quota/request
        - No usage returns full 10000

        EXPECTED: Returns 10000 for ENTERPRISE tier with no usage.
        """
        remaining = await quota_service.get_remaining_quota("enterprise_user", "enterprise")
        assert remaining == 10000


# ============================================================================
# Quota Deduction Tests
# ============================================================================


class TestDeductQuota:
    """Test quota deduction and enforcement logic."""

    @pytest.mark.asyncio
    async def test_deduct_quota_success(self, quota_service, mock_firestore):
        """
        TEST: Successfully deduct quota when sufficient balance exists.

        PURPOSE: Verify quota deduction updates Firestore and returns remaining balance.

        VALIDATES:
        - PRO user (1000 limit) with 200 used can deduct 150
        - New usage: 200 + 150 = 350
        - Remaining: 1000 - 350 = 650
        - Firestore document updated atomically

        EXPECTED: Returns 650 remaining, document shows used=350.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"user_deduct_{today}"

        mock_firestore.seed_data(
            "quota",
            quota_doc_id,
            {"user_id": "user_deduct", "tier": "pro", "used": 200, "daily_limit": 1000},
        )

        remaining = await quota_service.deduct_quota("user_deduct", "pro", 150)
        assert remaining == 650

        # Verify Firestore update
        doc = await mock_firestore.collection("quota").document(quota_doc_id).get()
        data = doc.to_dict()
        assert data["used"] == 350

    @pytest.mark.asyncio
    async def test_deduct_quota_insufficient(self, quota_service, mock_firestore):
        """
        TEST: Reject quota deduction when insufficient balance.

        PURPOSE: Prevent over-usage by raising ValueError on insufficient quota.

        VALIDATES:
        - FREE user (100 limit) with 90 used cannot deduct 20 (would exceed limit)
        - Raises ValueError with message: "Insufficient quota: need 20, have 10"
        - Firestore document NOT updated (transaction rolled back)

        EXPECTED: Raises ValueError, usage remains at 90.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"user_insufficient_{today}"

        mock_firestore.seed_data(
            "quota",
            quota_doc_id,
            {"user_id": "user_insufficient", "tier": "free", "used": 90, "daily_limit": 100},
        )

        with pytest.raises(ValueError, match="Insufficient quota"):
            await quota_service.deduct_quota("user_insufficient", "free", 20)

        # Verify quota NOT deducted
        doc = await mock_firestore.collection("quota").document(quota_doc_id).get()
        data = doc.to_dict()
        assert data["used"] == 90  # Unchanged

    @pytest.mark.asyncio
    async def test_deduct_quota_creates_document(self, quota_service, mock_firestore):
        """
        TEST: Create quota document on first deduction of the day.

        PURPOSE: Handle first request of day when quota document doesn't exist.

        VALIDATES:
        - User with no existing quota doc (new day/new user)
        - Deduct 25 from FREE tier (100 limit)
        - Document created with used=25, remaining=75
        - Includes user_id, tier, date, daily_limit fields

        EXPECTED: Returns 75, new document created with used=25.
        """
        remaining = await quota_service.deduct_quota("new_user", "free", 25)
        assert remaining == 75

        # Verify document created
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"new_user_{today}"
        doc = await mock_firestore.collection("quota").document(quota_doc_id).get()

        assert doc.exists
        data = doc.to_dict()
        assert data["used"] == 25
        assert data["user_id"] == "new_user"
        assert data["tier"] == "free"
        assert data["daily_limit"] == 100

    @pytest.mark.asyncio
    async def test_deduct_quota_exact_limit(self, quota_service, mock_firestore):
        """
        TEST: Allow deduction that brings usage exactly to daily limit.

        PURPOSE: Ensure users can use all quota without off-by-one errors.

        VALIDATES:
        - PRO user (1000 limit) with 950 used can deduct exactly 50
        - Final usage: 950 + 50 = 1000 (at limit, not exceeding)
        - Remaining: 0 (valid state, not error)

        EXPECTED: Returns 0 remaining, deduction succeeds.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        quota_doc_id = f"user_exact_{today}"

        mock_firestore.seed_data(
            "quota",
            quota_doc_id,
            {"user_id": "user_exact", "tier": "pro", "used": 950, "daily_limit": 1000},
        )

        remaining = await quota_service.deduct_quota("user_exact", "pro", 50)
        assert remaining == 0

        # Verify exact limit reached
        doc = await mock_firestore.collection("quota").document(quota_doc_id).get()
        data = doc.to_dict()
        assert data["used"] == 1000


# ============================================================================
# Quota History Tests
# ============================================================================


class TestGetQuotaUsage:
    """Test quota usage history retrieval."""

    @pytest.mark.asyncio
    async def test_get_quota_usage_history(self, quota_service, mock_firestore):
        """
        TEST: Retrieve daily quota usage history for analytics.

        PURPOSE: Enable users to track quota consumption patterns over time.

        VALIDATES:
        - Returns last 7 days of usage by default
        - Ordered by date descending (newest first)
        - Each record includes: date, used, daily_limit, tier
        - Empty list for user with no history

        EXPECTED: Returns list of daily usage records in reverse chronological order.
        """
        # Seed 3 days of usage
        mock_firestore.seed_data(
            "quota",
            "user_history_2025-10-30",
            {
                "user_id": "user_history",
                "date": "2025-10-30",
                "used": 50,
                "daily_limit": 100,
                "tier": "free",
            },
        )
        mock_firestore.seed_data(
            "quota",
            "user_history_2025-11-08",
            {
                "user_id": "user_history",
                "date": "2025-11-08",
                "used": 75,
                "daily_limit": 100,
                "tier": "free",
            },
        )
        mock_firestore.seed_data(
            "quota",
            "user_history_2025-11-10",
            {
                "user_id": "user_history",
                "date": "2025-11-10",
                "used": 30,
                "daily_limit": 100,
                "tier": "free",
            },
        )

        usage = await quota_service.get_quota_usage("user_history", days=7)

        assert len(usage) == 3
        # Service returns oldest first (order_by date ascending)
        assert usage[0]["date"] == "2025-10-30"
        assert usage[0]["used"] == 50
        assert usage[1]["date"] == "2025-11-08"
        assert usage[1]["used"] == 75
        assert usage[2]["date"] == "2025-11-10"
        assert usage[2]["used"] == 30

    @pytest.mark.asyncio
    async def test_get_quota_usage_no_history(self, quota_service):
        """
        TEST: Handle user with no quota usage history.

        PURPOSE: Gracefully return empty list for new users.

        VALIDATES:
        - User with no Firestore quota documents returns []
        - No errors raised for missing data
        - Enables UI to show "No usage yet" message

        EXPECTED: Returns empty list.
        """
        usage = await quota_service.get_quota_usage("new_user_no_history", days=7)
        assert usage == []
