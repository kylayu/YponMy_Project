from django.contrib import admin
from .models import Transaction, Budget, SavingsGoal

admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(SavingsGoal)