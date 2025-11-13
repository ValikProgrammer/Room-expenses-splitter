from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN # to the closest Z number 
from typing import Dict, Iterable, List

from sqlalchemy.orm import joinedload

from models import Person, Transaction, TransactionShare, db

DEFAULT_MEMBERS = ["Valentine", "Savel", "Sasha", "Matvei"]
DEFAULT_CURRENCY_SYMBOL = "£"


def ensure_default_members() -> None:
    """Create default members if the database is empty."""
    if Person.query.count():
        return

    for member_name in DEFAULT_MEMBERS:
        person = Person(name=member_name)
        db.session.add(person)
    db.session.commit()


def split_amount(total: Decimal, portions: int) -> List[Decimal]:
    """
    Evenly split ``total`` into ``portions`` pieces using bankers rounding and
    keep the sum equal to the original total.
    """
    if portions <= 0:
        raise ValueError("portions must be a positive integer")

    quantizer = Decimal("0.01")
    base_share = (total / portions).quantize(quantizer, rounding=ROUND_HALF_EVEN)
    shares = [base_share for _ in range(portions)]

    difference = total - sum(shares)
    if difference:
        # If there is any small leftover 
        # adjust the last share to ensure the sum matches the total
        shares[-1] = (shares[-1] + difference).quantize(
            quantizer, rounding=ROUND_HALF_EVEN
        )
    return shares


def compute_balances() -> Dict[int, Decimal]:
    """Return net balance per person."""
    balances: Dict[int, Decimal] = {
        member.id: Decimal("0.00") for member in Person.query.all()
    }

    transactions = Transaction.query.options(
        joinedload(Transaction.shares).joinedload(TransactionShare.person),
        joinedload(Transaction.payer),
    )
    for txn in transactions:
        balances[txn.payer_id] += Decimal(txn.amount)
        for share in txn.shares:
            balances[share.person_id] -= Decimal(share.amount)
    return balances


def compute_person_to_person_debts() -> Dict[int, Dict[int, Decimal]]:
    """
    Compute debt relationships: debts[person_a_id][person_b_id] = amount
    means person_a owes person_b that amount.
    """
    all_people = Person.query.all()
    debts: Dict[int, Dict[int, Decimal]] = {
        person.id: {p.id: Decimal("0.00") for p in all_people} for person in all_people
    }

    transactions = Transaction.query.options(
        joinedload(Transaction.shares).joinedload(TransactionShare.person),
        joinedload(Transaction.payer),
    )

    for txn in transactions:
        payer_id = txn.payer_id
        for share in txn.shares:
            debtor_id = share.person_id
            if debtor_id == payer_id:
                continue
            amount = Decimal(share.amount)
            debts[debtor_id][payer_id] += amount

    return debts


def build_transaction_from_form(form_data, members: Iterable[Person]) -> Transaction:
    description = (form_data.get("description") or "").strip()
    if not description:
        raise ValueError("Description is required.")

    date_str = form_data.get("date") or ""
    try:
        txn_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Date must be provided in YYYY-MM-DD format.") from None

    amount_raw = (form_data.get("amount") or "0").replace(",", ".")
    try:
        amount = Decimal(amount_raw)
    except Exception as exc:  # noqa: BLE001 - broad to wrap invalid decimal
        raise ValueError("Amount must be a valid number.") from exc

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    payer_id = form_data.get("payer_id")
    if not payer_id:
        raise ValueError("Select who paid for this expense.")

    payer = Person.query.get(int(payer_id))
    if not payer:
        raise ValueError("Selected payer does not exist.")

    participant_ids = [int(pid) for pid in form_data.getlist("participants")]
    participant_ids = list(dict.fromkeys(participant_ids))  # Remove duplicates

    if len(participant_ids) == 0:
        raise ValueError("Select at least one participant to split the expense.")

    known_member_ids = {member.id for member in members}
    if not set(participant_ids).issubset(known_member_ids):
        raise ValueError("Some participants are invalid.")

    comment = (form_data.get("comment") or "").strip()
    shares = split_amount(amount, len(participant_ids))

    transaction = Transaction(
        description=description,
        date=txn_date,
        amount=amount,
        comment=comment,
        payer=payer,
    )

    for member_id, share_amount in zip(participant_ids, shares, strict=True):
        transaction.shares.append(
            TransactionShare(person_id=member_id, amount=share_amount)
        )

    return transaction


def initialize_database() -> None:
    """Create tables and seed default members if needed."""
    db.create_all()
    ensure_default_members()

