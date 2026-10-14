from django.contrib import admin
from .models import Account


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