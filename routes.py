from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Iterable

from flask import (flash,jsonify,redirect,render_template,request,url_for)
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from models import Person, Transaction, TransactionShare, db
from utils import (DEFAULT_CURRENCY_SYMBOL,build_transaction_from_form,compute_balances,compute_person_to_person_debts,split_amount,)


def register_routes(app):
    @app.before_request
    def log_request_info():
        client_ip = request.remote_addr
        method = request.method
        path = request.path
        app.logger.info(f"before_request: {method} {path} from {client_ip}")

    @app.template_filter("currency")
    def format_currency(value: Decimal | None) -> str:
        if value is None:
            return "-"
        return f"{DEFAULT_CURRENCY_SYMBOL}{Decimal(value):,.2f}"


    @app.route("/", methods=["GET", "POST"])
    def index():
        members = Person.query.order_by(Person.name).all()
        if request.method == "POST":
            try:
                new_transaction = build_transaction_from_form(request.form, members)
            except ValueError as exc:
                flash(str(exc), "danger")
            else:
                db.session.add(new_transaction)
                db.session.commit()
                flash("Transaction recorded successfully.", "success")
                return redirect(url_for("transactions"))

        return render_template(
            "index.html",
            members=members,
            default_date=date.today().strftime("%Y-%m-%d"),
        )

    @app.route("/transactions")
    def transactions():
        sort = request.args.get("sort", "-date")

        sort_mapping = {
            "date": Transaction.date.asc(),
            "-date": Transaction.date.desc(),
            "amount": Transaction.amount.asc(),
            "-amount": Transaction.amount.desc(),
            "payer": func.lower(Person.name).asc(),
            "-payer": func.lower(Person.name).desc(),
        }
        order_by_clause = sort_mapping.get(sort, Transaction.date.desc())

        query = (
            Transaction.query.options(
                joinedload(Transaction.shares).joinedload(TransactionShare.person),
                joinedload(Transaction.payer),
            )
            .join(Person, Transaction.payer)
            .order_by(order_by_clause)
        )

        member_filter = request.args.get("member_id")
        if member_filter:
            query = query.join(
                TransactionShare,
                TransactionShare.transaction_id == Transaction.id,
            ).filter(TransactionShare.person_id == int(member_filter))

        transactions_list = query.all()
        members = Person.query.order_by(Person.name).all()
        balances = compute_balances()

        return render_template(
            "transactions.html",
            transactions=transactions_list,
            members=members,
            balances=balances,
            selected_sort=sort,
            selected_member=member_filter,
            currency_symbol=DEFAULT_CURRENCY_SYMBOL,
        )

    @app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
    def edit_transaction(transaction_id):
        transaction = Transaction.query.get_or_404(transaction_id)
        members = Person.query.order_by(Person.name).all()

        if request.method == "POST":
            try:
                updated_transaction = build_transaction_from_form(request.form, members)
                # Update existing transaction
                transaction.date = updated_transaction.date
                transaction.description = updated_transaction.description
                transaction.amount = updated_transaction.amount
                transaction.comment = updated_transaction.comment
                transaction.payer = updated_transaction.payer

                # Clear old shares and add new ones
                transaction.shares.clear()
                db.session.flush()
                for share in updated_transaction.shares:
                    transaction.shares.append(
                        TransactionShare(person_id=share.person_id, amount=share.amount)
                    )
                
                db.session.commit()
                flash("Transaction updated successfully.", "success")
                return redirect(url_for("transactions"))
            except ValueError as exc:
                flash(str(exc), "danger")

        # Pre-fill form with existing data
        participant_ids = [share.person_id for share in transaction.shares]
        return render_template(
            "edit_transaction.html",
            transaction=transaction,
            members=members,
            participant_ids=participant_ids,
            default_date=transaction.date.strftime("%Y-%m-%d"),
        )

    @app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
    def delete_transaction(transaction_id):
        transaction = Transaction.query.get_or_404(transaction_id)
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted successfully.", "success")
        return redirect(url_for("transactions"))

    @app.route("/balances")
    def balances():
        """Page showing person-to-person debt relationships."""
        members = Person.query.order_by(Person.name).all()
        debts_raw = compute_person_to_person_debts()
        settlements: Dict[int, Dict[str, list]] = {
            member.id: {"owes": [], "owed": []} for member in members
        }

        for index, person in enumerate(members):
            for other in members[index + 1 :]:
                net = debts_raw[person.id][other.id] - debts_raw[other.id][person.id]
                net = net.quantize(Decimal("0.01"))
                if net > 0:
                    settlements[person.id]["owes"].append(
                        {"member": other, "amount": net}
                    )
                    settlements[other.id]["owed"].append(
                        {"member": person, "amount": net}
                    )
                elif net < 0:
                    amount = (-net).quantize(Decimal("0.01"))
                    settlements[person.id]["owed"].append(
                        {"member": other, "amount": amount}
                    )
                    settlements[other.id]["owes"].append(
                        {"member": person, "amount": amount}
                    )
        balances_dict = compute_balances()

        return render_template(
            "balances.html",
            members=members,
            settlements=settlements,
            balances=balances_dict,
            currency_symbol=DEFAULT_CURRENCY_SYMBOL,
        )

    @app.route("/members/add", methods=["GET", "POST"])
    def add_member():
        members = Person.query.order_by(Person.name).all()
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            if not name:
                flash("Name is required.", "danger")
            else:
                # Check if member already exists
                existing = Person.query.filter_by(name=name).first()
                if existing:
                    flash(f"Member '{name}' already exists.", "danger")
                else:
                    new_member = Person(name=name)
                    db.session.add(new_member)
                    db.session.commit()
                    flash(f"Member '{name}' added successfully.", "success")
                    return redirect(url_for("add_member"))

        return render_template("add_member.html", members=members)

    @app.post("/members/<int:member_id>/edit")
    def edit_member(member_id):
        member = Person.query.get_or_404(member_id)
        new_name = (request.form.get("name") or "").strip()
        if not new_name:
            flash("Name cannot be empty.", "danger")
            return redirect(url_for("add_member"))

        if Person.query.filter(
            Person.id != member.id, func.lower(Person.name) == new_name.lower()
        ).first():
            flash(f"Member '{new_name}' already exists.", "danger")
            return redirect(url_for("add_member"))

        member.name = new_name
        db.session.commit()
        flash("Member renamed successfully.", "success")
        return redirect(url_for("add_member"))

    @app.post("/members/<int:member_id>/delete")
    def delete_member(member_id):
        member = Person.query.get_or_404(member_id)

        has_transactions = (
            Transaction.query.filter_by(payer_id=member.id).first()
            or TransactionShare.query.filter_by(person_id=member.id).first()
        )
        if has_transactions:
            flash(
                "Cannot delete member who is linked to existing transactions.",
                "danger",
            )
            return redirect(url_for("add_member"))

        db.session.delete(member)
        db.session.commit()
        flash("Member deleted successfully.", "success")
        return redirect(url_for("add_member"))

    @app.route("/diagrams")
    def diagrams():
        """Page with circle diagrams for transactions count and volume paid."""
        members = Person.query.order_by(Person.name).all()
        
        # Count transactions per person
        transaction_counts = {}
        transaction_volumes = {}
        
        for member in members:
            count = Transaction.query.filter_by(payer_id=member.id).count()
            total = db.session.query(func.sum(Transaction.amount)).filter_by(payer_id=member.id).scalar() or Decimal("0.00")
            transaction_counts[member.name] = count
            transaction_volumes[member.name] = float(total)

        # Convert to lists for easier template rendering
        count_labels = list(transaction_counts.keys())
        count_values = list(transaction_counts.values())
        volume_labels = list(transaction_volumes.keys())
        volume_values = list(transaction_volumes.values())

        return render_template(
            "diagrams.html",
            members=members,
            transaction_counts=transaction_counts,
            transaction_volumes=transaction_volumes,
            count_labels=count_labels,
            count_values=count_values,
            volume_labels=volume_labels,
            volume_values=volume_values,
            currency_symbol=DEFAULT_CURRENCY_SYMBOL,
        )

    @app.route("/api/members")
    def api_members():
        members = Person.query.order_by(Person.name).all()
        return jsonify([{"id": member.id, "name": member.name} for member in members])

    @app.route("/api/transactions", methods=["GET", "POST"])
    def api_transactions():
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            form_like = _payload_to_form(payload)
            try:
                transaction = build_transaction_from_form(
                    form_like, Person.query.order_by(Person.name).all()
                )
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            db.session.add(transaction)
            db.session.commit()
            return jsonify(serialize_transaction(transaction)), 201

        sort = request.args.get("sort", "-date")
        sort_mapping = {
            "date": Transaction.date.asc(),
            "-date": Transaction.date.desc(),
            "amount": Transaction.amount.asc(),
            "-amount": Transaction.amount.desc(),
        }
        order_by_clause = sort_mapping.get(sort, Transaction.date.desc())

        query = Transaction.query.options(
            joinedload(Transaction.shares).joinedload(TransactionShare.person),
            joinedload(Transaction.payer),
        ).order_by(order_by_clause)

        member_filter = request.args.get("member_id")
        if member_filter:
            query = query.join(
                TransactionShare,
                TransactionShare.transaction_id == Transaction.id,
            ).filter(TransactionShare.person_id == int(member_filter))

        transactions_list = query.all()
        return jsonify([serialize_transaction(txn) for txn in transactions_list])

    @app.route("/health")
    def health():
        try:
            # Quick DB check
            Person.query.count()
            return {"status": "ok", "database": "connected"}
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500


def serialize_transaction(txn: Transaction) -> Dict[str, object]:
    return {
        "id": txn.id,
        "date": txn.date.isoformat(),
        "description": txn.description,
        "amount": float(txn.amount),
        "comment": txn.comment,
        "payer": {
            "id": txn.payer.id,
            "name": txn.payer.name,
        },
        "shares": [
            {
                "member": {
                    "id": share.person.id,
                    "name": share.person.name,
                },
                "amount": float(share.amount),
            }
            for share in txn.shares
        ],
    }


def _payload_to_form(payload: Dict[str, object]):
    """Convert JSON payload to structure compatible with the form helper."""

    class FormAdapter(dict):
        def getlist(self, key):
            value = self.get(key, [])
            if isinstance(value, list):
                return [str(item) for item in value]
            return [str(value)]

    adapter = FormAdapter()
    adapter.update(
        {
            "description": payload.get("description", ""),
            "date": payload.get("date", ""),
            "amount": str(payload.get("amount", "")),
            "comment": payload.get("comment", ""),
        }
    )

    payer_id = payload.get("payer_id") or payload.get("payerId")
    if payer_id is not None:
        adapter["payer_id"] = str(payer_id)

    participants = payload.get("participant_ids") or payload.get("participants") or []
    adapter["participants"] = [str(member_id) for member_id in participants]

    return adapter

