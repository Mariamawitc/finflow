
import secrets

from django.conf import settings
from django.db import models
from django.db import IntegrityError, models, transaction


def generate_account_number():
    return str(secrets.randbelow(900_000_000_000) + 100_000_000_000)


class Account(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account",
    )

    account_number = models.CharField(
        max_length=20,
        unique=True,
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account_number

    
def save(self, *args, **kwargs):
    if self.account_number:
        super().save(*args, **kwargs)
        return

    for attempt in range(5):
        self.account_number = generate_account_number()

        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
            return
        except IntegrityError:
            if attempt == 4:
                raise

def __str__(self):
        return self.account_number

    