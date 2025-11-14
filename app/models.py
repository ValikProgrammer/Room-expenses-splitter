from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric

db = SQLAlchemy()


class Person(db.Model):
    __tablename__ = "people"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Person {self.name}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(Numeric(10, 2), nullable=False)
    comment = db.Column(db.Text)

    payer_id = db.Column(db.Integer, db.ForeignKey("people.id"), nullable=False)
    payer = db.relationship("Person", backref=db.backref("payments", lazy=True))

    shares = db.relationship(
        "TransactionShare",
        cascade="all, delete-orphan",
        back_populates="transaction",
        lazy=True,
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.description} {self.amount}>"


class TransactionShare(db.Model):
    __tablename__ = "transaction_shares"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(Numeric(10, 2), nullable=False)

    transaction_id = db.Column(
        db.Integer, db.ForeignKey("transactions.id"), nullable=False
    )
    transaction = db.relationship(
        "Transaction", back_populates="shares", lazy=True
    )

    person_id = db.Column(db.Integer, db.ForeignKey("people.id"), nullable=False)
    person = db.relationship("Person", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("transaction_id", "person_id", name="uq_share_transaction"),
    )

