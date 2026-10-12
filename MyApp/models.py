from django.db import models


class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    transaction_type = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=100)
    date = models.DateField()
    payment_method = models.CharField(max_length=50)
    fund_type = models.CharField(max_length=20, default="Cash")
    category = models.CharField(max_length=100)

    # How the money will be handled
    allocation = models.CharField(max_length=50, default="Needs")
    money_plan = models.TextField(blank=True, default="")
    priority = models.CharField(max_length=20, default="Medium")

    def __str__(self):
        return self.description


class Budget(models.Model):
    budget_id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    spending_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.category


class SavingsGoal(models.Model):
    goal_id = models.AutoField(primary_key=True)
    goal_name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    target_date = models.DateField()

    def __str__(self):
        return self.goal_name