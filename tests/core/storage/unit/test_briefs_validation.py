"""Unit tests for brief lifecycle promotion validation."""

from src.core.storage.briefs import (
    PROMOTION_REQUIRED_SECTIONS,
    PROMOTION_STATUSES,
    validate_promotion_sections,
)


class TestValidatePromotionSections:
    """Tests for validate_promotion_sections()."""

    def test_non_promotion_status_always_valid(self):
        """Non-promotion statuses like draft/exploring should always pass."""
        data = {}  # completely empty
        result = validate_promotion_sections(data, "draft")
        assert result["valid"] is True
        assert result["missing"] == []
        assert result["checked_status"] == "draft"
        assert result["sections"] == {}

    def test_non_promotion_status_exploring(self):
        data = {}
        result = validate_promotion_sections(data, "exploring")
        assert result["valid"] is True
        assert result["missing"] == []
        assert result["sections"] == {}

    def test_promotion_status_all_sections_present(self):
        data = {
            "problem": "Users lose data",
            "goal": "Prevent data loss",
            "acceptance_criteria": "- [ ] AC item",
        }
        result = validate_promotion_sections(data, "implementation-ready")
        assert result["valid"] is True
        assert result["missing"] == []
        assert result["checked_status"] == "implementation-ready"
        assert result["sections"] == {
            "problem": "populated",
            "goal": "populated",
            "acceptance_criteria": "populated",
        }

    def test_promotion_status_missing_all_sections(self):
        data = {}
        result = validate_promotion_sections(data, "implementation-ready")
        assert result["valid"] is False
        assert set(result["missing"]) == set(PROMOTION_REQUIRED_SECTIONS)
        assert result["sections"] == {
            "problem": "blank",
            "goal": "blank",
            "acceptance_criteria": "blank",
        }

    def test_promotion_status_missing_one_section(self):
        data = {
            "problem": "A problem",
            "goal": "A goal",
            # acceptance_criteria missing
        }
        result = validate_promotion_sections(data, "architect-review")
        assert result["valid"] is False
        assert result["missing"] == ["acceptance_criteria"]

    def test_promotion_status_whitespace_only_counts_as_missing(self):
        data = {
            "problem": "   ",
            "goal": "A goal",
            "acceptance_criteria": "- [ ] AC",
        }
        result = validate_promotion_sections(data, "review-ready")
        assert result["valid"] is False
        assert result["missing"] == ["problem"]

    def test_promotion_status_empty_string_counts_as_missing(self):
        data = {
            "problem": "",
            "goal": "G",
            "acceptance_criteria": "AC",
        }
        result = validate_promotion_sections(data, "done")
        assert result["valid"] is False
        assert result["missing"] == ["problem"]

    def test_all_promotion_statuses_trigger_validation(self):
        """Every status in PROMOTION_STATUSES should trigger the check."""
        data = {}  # missing everything
        for status in PROMOTION_STATUSES:
            result = validate_promotion_sections(data, status)
            assert result["valid"] is False, f"Expected invalid for status '{status}'"

    def test_none_values_count_as_missing(self):
        data = {
            "problem": None,
            "goal": "G",
            "acceptance_criteria": "AC",
        }
        result = validate_promotion_sections(data, "implementation-ready")
        assert result["valid"] is False
        assert result["missing"] == ["problem"]
