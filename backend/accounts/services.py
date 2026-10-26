
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

@db_transaction.atomic
def withdraw(account_id, amount):
    amount = Decimal(str(amount))

    if not amount.is_finite() or amount <= 0:
        raise ValidationError(
            "Withdrawal amount must be greater than zero."
        )

    account = Account.objects.select_for_update().get(
        pk=account_id
    )

    if account.status != Account.Status.ACTIVE:
        raise ValidationError("This account is inactive.")

    if account.balance < amount:
        raise ValidationError("Insufficient funds.")

    Account.objects.filter(pk=account.pk).update(
        balance=F("balance") - amount
    )

    account.refresh_from_db()

    transaction_record = Transaction.objects.create(
        account=account,
        transaction_type=Transaction.Type.WITHDRAWAL,
        amount=amount,
        status=Transaction.Status.COMPLETED,
        description="Account withdrawal",
    )

    return transaction_record

@db_transaction.atomic
def transfer(sender_account_id, recipient_account_id, amount):
    amount = Decimal(str(amount))

    # 1. Validate the amount
    if not amount.is_finite() or amount <= 0:
        raise ValidationError(
            "Transfer amount must be greater than zero."
        )

    # 2. Prevent transfers to the same account
    if sender_account_id == recipient_account_id:
        raise ValidationError(
            "Cannot transfer to the same account."
        )

    # 3. Lock both accounts in a consistent order
    accounts = list(
        Account.objects.select_for_update()
        .filter(
            pk__in=[sender_account_id, recipient_account_id]
        )
        .order_by("pk")
    )

    accounts_by_id = {account.pk: account for account in accounts}

    if sender_account_id not in accounts_by_id:
        raise Account.DoesNotExist("Sender account not found.")

    if recipient_account_id not in accounts_by_id:
        raise Account.DoesNotExist("Recipient account not found.")

    sender = accounts_by_id[sender_account_id]
    recipient = accounts_by_id[recipient_account_id]

    # 4. Validate both accounts
    if sender.status != Account.Status.ACTIVE:
        raise ValidationError("Sender account is inactive.")

    if recipient.status != Account.Status.ACTIVE:
        raise ValidationError("Recipient account is inactive.")

    if sender.balance < amount:
        raise ValidationError("Insufficient funds.")

    # 5. Update both balances
    Account.objects.filter(pk=sender.pk).update(
        balance=F("balance") - amount
    )

    Account.objects.filter(pk=recipient.pk).update(
        balance=F("balance") + amount
    )

    # 6. Record both sides of the transfer
    transfer_out = Transaction.objects.create(
        account=sender,
        transaction_type=Transaction.Type.TRANSFER_OUT,
        amount=amount,
        status=Transaction.Status.COMPLETED,
        description=f"Transfer to account {recipient.account_number}",
    )

    Transaction.objects.create(
        account=recipient,
        transaction_type=Transaction.Type.TRANSFER_IN,
        amount=amount,
        status=Transaction.Status.COMPLETED,
        description=f"Transfer from account {sender.account_number}",
    )

    return transfer_out