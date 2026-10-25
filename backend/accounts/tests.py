
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from users.models import User
from .models import Account, Transaction

from .services import deposit, withdraw


class DepositServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="test-password-123",
        )

        self.account = Account.objects.create(
            user=self.user,
        )

    def test_successful_deposit(self):
        transaction_record = deposit(
            self.account.pk,
            "500.00",
        )

        self.account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal("500.00"),
        )
        self.assertEqual(
            transaction_record.amount,
            Decimal("500.00"),
        )
        self.assertEqual(
            transaction_record.transaction_type,
            Transaction.Type.DEPOSIT,
        )
        self.assertEqual(
            transaction_record.status,
            Transaction.Status.COMPLETED,
        )

    def test_zero_deposit_is_rejected(self):
        with self.assertRaises(ValidationError):
            deposit(self.account.pk, "0.00")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("0.00"))
        self.assertEqual(self.account.transactions.count(), 0)

    def test_negative_deposit_is_rejected(self):
        with self.assertRaises(ValidationError):
            deposit(self.account.pk, "-10.00")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("0.00"))
        self.assertEqual(self.account.transactions.count(), 0)

    def test_inactive_account_rejects_deposit(self):
    # Give the account an initial balance of 500.00
      deposit(self.account.pk, "500.00")
      self.account.refresh_from_db()

    # Make the account inactive
      self.account.status = Account.Status.INACTIVE
      self.account.save()

    # A deposit into an inactive account must be rejected
      with self.assertRaises(ValidationError):
        deposit(self.account.pk, "100.00")

    # The original balance must remain unchanged
      self.account.refresh_from_db()
      self.assertEqual(self.account.balance, Decimal("500.00"))

    def test_balance_rolls_back_if_transaction_creation_fails(self):
        with patch(
            "accounts.services.Transaction.objects.create",
            side_effect=RuntimeError("Simulated database failure"),
        ):
            with self.assertRaises(RuntimeError):
                deposit(self.account.pk, "200.00")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("0.00"))
        self.assertEqual(self.account.transactions.count(), 0)

class WithdrawalServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="withdrawuser",
            email="withdraw@example.com",
            password="test-password-123",
        )

        self.account = Account.objects.create(
            user=self.user,
        )

        deposit(self.account.pk, "500.00")

    def test_successful_withdrawal(self):
        transaction_record = withdraw(
            self.account.pk,
            "120.00",
        )

        self.account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal("380.00"),
        )
        self.assertEqual(
            transaction_record.amount,
            Decimal("120.00"),
        )
        self.assertEqual(
            transaction_record.transaction_type,
            Transaction.Type.WITHDRAWAL,
        )
        self.assertEqual(
            transaction_record.status,
            Transaction.Status.COMPLETED,
        )

    def test_insufficient_funds_is_rejected(self):
        with self.assertRaises(ValidationError):
            withdraw(self.account.pk, "600.00")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500.00"))

        self.assertEqual(
            self.account.transactions.filter(
                transaction_type=Transaction.Type.WITHDRAWAL
            ).count(),
            0,
        )

    def test_zero_withdrawal_is_rejected(self):
        with self.assertRaises(ValidationError):
            withdraw(self.account.pk, "0.00")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500.00"))

    def test_negative_withdrawal_is_rejected(self):
        with self.assertRaises(ValidationError):
            withdraw(self.account.pk, "-10.00")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500.00"))

    def test_inactive_account_rejects_withdrawal(self):
      self.account.refresh_from_db()

      self.account.status = Account.Status.INACTIVE
      self.account.save()

      with self.assertRaises(ValidationError):
        withdraw(self.account.pk, "100.00")

      self.account.refresh_from_db()
      self.assertEqual(self.account.balance, Decimal("500.00"))
    def test_balance_rolls_back_if_transaction_creation_fails(self):
        with patch(
            "accounts.services.Transaction.objects.create",
            side_effect=RuntimeError("Simulated database failure"),
        ):
            with self.assertRaises(RuntimeError):
                withdraw(self.account.pk, "100.00")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500.00"))
