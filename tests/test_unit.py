"""Unit tests for input validation and error handling."""

import pytest
from decimal import Decimal

from utils import split_amount, build_transaction_from_form
from models import Person, db


class TestSplitAmount:
    """Test amount splitting logic."""

    def test_split_amount_even(self):
        """Test splitting amount evenly."""
        result = split_amount(Decimal("100.00"), 4)
        assert len(result) == 4
        assert sum(result) == Decimal("100.00")
        assert all(share == Decimal("25.00") for share in result)

    def test_split_amount_uneven(self):
        """Test splitting amount with remainder."""
        result = split_amount(Decimal("100.00"), 3)
        assert len(result) == 3
        assert sum(result) == Decimal("100.00")
        # First two should be equal, last one gets remainder
        assert result[0] == result[1]
        assert result[0] == Decimal("33.33")
        assert result[2] == Decimal("33.34")

    def test_split_amount_invalid_portions(self):
        """Test error handling for invalid portion count."""
        with pytest.raises(ValueError, match="portions must be a positive integer"):
            split_amount(Decimal("100.00"), 0)
        
        with pytest.raises(ValueError, match="portions must be a positive integer"):
            split_amount(Decimal("100.00"), -1)

    def test_split_amount_small_amount(self):
        """Test splitting very small amounts."""
        result = split_amount(Decimal("0.03"), 3)
        assert len(result) == 3
        assert sum(result) == Decimal("0.03")
        # Should handle rounding correctly
        assert result[0] == Decimal("0.01")
        assert result[1] == Decimal("0.01")
        assert result[2] == Decimal("0.01")


class TestBuildTransactionValidation:
    """Test transaction form validation."""

    @pytest.fixture
    def sample_members(self, app):
        """Create sample members for testing."""
        with app.app_context():
            # Clean up any existing data
            db.session.query(Person).delete()
            db.session.commit()
            
            member1 = Person(name="Alice")
            member2 = Person(name="Bob")
            db.session.add(member1)
            db.session.add(member2)
            db.session.commit()
            
            # Store IDs to avoid detached instance errors
            member1_id = member1.id
            member2_id = member2.id
            
            return [member1_id, member2_id]

    def test_missing_description(self, app, sample_members):
        """Test validation error when description is missing."""
        with app.app_context():
            # Get fresh members from DB
            members = Person.query.filter(Person.id.in_(sample_members)).all()
            form_data = {
                "date": "2025-01-01",
                "amount": "100.00",
                "payer_id": str(sample_members[0]),
                "participants": [str(sample_members[0])],
            }
            
            with pytest.raises(ValueError, match="Description is required"):
                build_transaction_from_form(form_data, members)

    def test_invalid_date_format(self, app, sample_members):
        """Test validation error for invalid date format."""
        with app.app_context():
            # Get fresh members from DB
            members = Person.query.filter(Person.id.in_(sample_members)).all()
            form_data = {
                "description": "Test",
                "date": "invalid-date",
                "amount": "100.00",
                "payer_id": str(sample_members[0]),
                "participants": [str(sample_members[0])],
            }
            
            with pytest.raises(ValueError, match="Date must be provided"):
                build_transaction_from_form(form_data, members)

    def test_invalid_amount(self, app, sample_members):
        """Test validation error for invalid amount."""
        with app.app_context():
            # Get fresh members from DB
            members = Person.query.filter(Person.id.in_(sample_members)).all()
            form_data = {
                "description": "Test",
                "date": "2025-01-01",
                "amount": "not-a-number",
                "payer_id": str(sample_members[0]),
                "participants": [str(sample_members[0])],
            }
            
            with pytest.raises(ValueError, match="Amount must be a valid number"):
                build_transaction_from_form(form_data, members)

    def test_negative_amount(self, app, sample_members):
        """Test validation error for negative amount."""
        with app.app_context():
            # Get fresh members from DB
            members = Person.query.filter(Person.id.in_(sample_members)).all()
            form_data = {
                "description": "Test",
                "date": "2025-01-01",
                "amount": "-10.00",
                "payer_id": str(sample_members[0]),
                "participants": [str(sample_members[0])],
            }
            
            with pytest.raises(ValueError, match="Amount must be greater than zero"):
                build_transaction_from_form(form_data, members)

    def test_missing_participants(self, app, sample_members):
        """Test validation error when no participants selected."""
        with app.app_context():
            # Get fresh members from DB
            members = Person.query.filter(Person.id.in_(sample_members)).all()
            form_data = {
                "description": "Test",
                "date": "2025-01-01",
                "amount": "100.00",
                "payer_id": str(sample_members[0]),
                "participants": [],
            }
            
            with pytest.raises(ValueError, match="Select at least one participant"):
                build_transaction_from_form(form_data, members)

