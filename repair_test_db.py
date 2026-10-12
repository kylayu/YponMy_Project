import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MyProject.settings")

import django
from django.conf import settings

# Use a separate database connection for the test copy.
settings.DATABASES["repair"] = settings.DATABASES["default"].copy()
settings.DATABASES["repair"]["NAME"] = str(
    Path("db_repair_test.sqlite3").resolve()
)

django.setup()

from django.db import connections
from MyApp.models import SavingsGoal, CategoryBudget, BudgetAllocation, Transaction

connection = connections["repair"]

print("Repairing test database:", connection.settings_dict["NAME"])

with connection.schema_editor() as editor:
    existing_tables = set(connection.introspection.table_names())

    # Create missing tables in dependency order.
    for model in (SavingsGoal, CategoryBudget, BudgetAllocation):
        table_name = model._meta.db_table

        if table_name not in existing_tables:
            print("Creating table:", table_name)
            editor.create_model(model)
            existing_tables.add(table_name)
        else:
            print("Table already exists:", table_name)

    # Check the existing Transaction table for missing columns.
    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, Transaction._meta.db_table
            )
        }

    # Add missing fields without replacing existing transaction records.
    for field_name in ("notes", "budget"):
        field = Transaction._meta.get_field(field_name)

        if field.column not in columns:
            print("Adding Transaction field:", field_name)
            editor.add_field(Transaction, field)
            columns.add(field.column)
        else:
            print("Field already exists:", field_name)

# Verify the result using the test database connection.
tables = set(connection.introspection.table_names())

print("\nVerification:")
for model in (SavingsGoal, CategoryBudget, BudgetAllocation, Transaction):
    print(
        model._meta.db_table,
        "exists:", model._meta.db_table in tables
    )

with connection.cursor() as cursor:
    transaction_columns = {
        column.name
        for column in connection.introspection.get_table_description(
            cursor, Transaction._meta.db_table
        )
    }

print("Transaction.notes exists:", "notes" in transaction_columns)
print("Transaction.budget_id exists:", "budget_id" in transaction_columns)

print("\nTest database repair script finished.")
