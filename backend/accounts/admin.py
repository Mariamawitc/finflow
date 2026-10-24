
from django.contrib import admin
from .models import Account, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "account_number",
        "user",
        "balance",
        "status",
        "created_at",
       
    )
    search_fields = (
        "account_number",
        "user__email",
    )
    list_filter = ("status",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "account",
        "transaction_type",
        "amount",
        "status",
        "created_at",
    )
    search_fields = (
        "reference",
        "account__account_number",
    )
    list_filter = (
        "transaction_type",
        "status",
    )
    readonly_fields = (
        "reference",
        "created_at",
    )
