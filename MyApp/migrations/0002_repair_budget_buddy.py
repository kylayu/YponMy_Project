from django.db import migrations


def repair_budget_buddy_database(apps, schema_editor):
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        tables = connection.introspection.table_names(cursor)

    # Create the missing Budget table.
    if "MyApp_budget" not in tables:
        Budget = apps.get_model("MyApp", "Budget")
        schema_editor.create_model(Budget)

    # Create the missing SavingsGoal table.
    if "MyApp_savingsgoal" not in tables:
        SavingsGoal = apps.get_model("MyApp", "SavingsGoal")
        schema_editor.create_model(SavingsGoal)

    # Repair the old Transaction table while preserving its data.
    if "MyApp_transaction" in tables:
        archive = "MyApp_transaction_legacy"

        if archive in tables:
            raise RuntimeError(
                "The transaction archive already exists. "
                "Stop and inspect the database before proceeding."
            )

        with connection.cursor() as cursor:
            cursor.execute(
                'ALTER TABLE "MyApp_transaction" '
                'RENAME TO "MyApp_transaction_legacy"'
            )

        Transaction = apps.get_model("MyApp", "Transaction")
        schema_editor.create_model(Transaction)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO "MyApp_transaction" (
                    "transaction_id",
                    "transaction_type",
                    "amount",
                    "description",
                    "date",
                    "payment_method",
                    "fund_type",
                    "category"
                )
                SELECT
                    "id",
                    "transaction_type",
                    "amount",
                    "description",
                    "date",
                    "payment_method",
                    'Cash',
                    "category"
                FROM "MyApp_transaction_legacy"
            """)


class Migration(migrations.Migration):

    dependencies = [
        ("MyApp", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            repair_budget_buddy_database,
            reverse_code=migrations.RunPython.noop,
        ),
    ]