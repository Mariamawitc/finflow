
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import F

from .models import Account, Transaction


@db_transaction.atomic
def deposit(account_id, amount):
    amount = Decimal(str(amount))

    if not amount.is_finite() or amount <= 0:
        raise ValidationError("Deposit amount must be greater than zero.")

    account = Account.objects.select_for_update().get(
        pk=account_id
    )

    if account.status != Account.Status.ACTIVE:
        raise ValidationError("This account is inactive.")

    Account.objects.filter(pk=account.pk).update(
        balance=F("balance") + amount
    )

    account.refresh_from_db()

    transaction_record = Transaction.objects.create(
        account=account,
        transaction_type=Transaction.Type.DEPOSIT,
        amount=amount,
        status=Transaction.Status.COMPLETED,
        description="Account deposit",
    )

    return transaction_record
