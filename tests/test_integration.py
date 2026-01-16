"""Integration tests for API endpoints."""

import pytest
from datetime import date
from decimal import Decimal

from models import Person, Transaction, TransactionShare, db


class TestAPIMembers:
    """Test /api/members endpoint."""

    def test_get_members(self, client, app):
        """Test getting list of members."""
        with app.app_context():
            # Clean up and add test data
            db.session.query(Person).delete()
            db.session.commit()
            
            member1 = Person(name="Alice")
            member2 = Person(name="Bob")
            db.session.add(member1)
            db.session.add(member2)
            db.session.commit()
        
        response = client.get("/api/members")
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 2
        
        names = [m["name"] for m in data]
        assert "Alice" in names
        assert "Bob" in names
        
        # Check structure
        assert "id" in data[0]
        assert "name" in data[0]


class TestAPITransactions:
    """Test /api/transactions endpoint."""

    @pytest.fixture
    def sample_data(self, app):
        """Create sample transaction data."""
        with app.app_context():
            # Clean up
            db.session.query(TransactionShare).delete()
            db.session.query(Transaction).delete()
            db.session.query(Person).delete()
            db.session.commit()
            
            # Create members
            payer = Person(name="Alice")
            participant = Person(name="Bob")
            db.session.add(payer)
            db.session.add(participant)
            db.session.commit()
            
            # Store IDs to avoid detached instance errors
            payer_id = payer.id
            participant_id = participant.id
            
            # Create transaction
            transaction = Transaction(
                description="Groceries",
                date=date(2025, 1, 1),
                amount=Decimal("100.00"),
                payer_id=payer_id,
            )
            db.session.add(transaction)
            db.session.commit()
            
            transaction_id = transaction.id
            
            share = TransactionShare(
                transaction_id=transaction_id,
                person_id=participant_id,
                amount=Decimal("50.00"),
            )
            db.session.add(share)
            db.session.commit()
            
            return {
                "payer_id": payer_id,
                "participant_id": participant_id,
                "transaction_id": transaction_id,
            }

    def test_get_transactions(self, client, sample_data):
        """Test getting list of transactions."""
        response = client.get("/api/transactions")
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        txn = data[0]
        assert txn["description"] == "Groceries"
        assert txn["amount"] == 100.0
        assert "payer" in txn
        assert "shares" in txn

    def test_create_transaction(self, client, app):
        """Test creating a new transaction via API."""
        payer_id = None
        participant_id = None
        with app.app_context():
            # Clean up and create members
            db.session.query(TransactionShare).delete()
            db.session.query(Transaction).delete()
            db.session.query(Person).delete()
            db.session.commit()
            
            payer = Person(name="Alice")
            participant = Person(name="Bob")
            db.session.add(payer)
            db.session.add(participant)
            db.session.commit()
            
            # Store IDs to avoid detached instance errors
            payer_id = payer.id
            participant_id = participant.id
        
        payload = {
            "description": "Dinner",
            "date": "2025-01-15",
            "amount": "75.50",
            "payer_id": payer_id,
            "participants": [payer_id, participant_id],
            "comment": "Restaurant bill",
        }
        
        response = client.post(
            "/api/transactions",
            json=payload,
            content_type="application/json",
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["description"] == "Dinner"
        assert data["amount"] == 75.5
        assert len(data["shares"]) == 2

    def test_create_transaction_validation_error(self, client, app):
        """Test API returns 400 for invalid transaction data."""
        with app.app_context():
            db.session.query(Person).delete()
            db.session.commit()
        
        payload = {
            "description": "",  # Invalid: empty description
            "date": "2025-01-15",
            "amount": "100.00",
        }
        
        response = client.post(
            "/api/transactions",
            json=payload,
            content_type="application/json",
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_get_transactions_with_filter(self, client, sample_data):
        """Test filtering transactions by member."""
        response = client.get(f"/api/transactions?member_id={sample_data['participant_id']}")
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        # Should return transactions where this member is a participant
        if len(data) > 0:
            assert any(
                share["member"]["id"] == sample_data["participant_id"]
                for txn in data
                for share in txn["shares"]
            )


