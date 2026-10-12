from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Transaction, Budget, SavingsGoal


PAYMENT_METHODS = [
    "Cash", "GCash", "Maya", "Bank Transfer", "Card", "Other"
]

FUND_TYPES = ["Cash", "Digital"]

ALLOCATIONS = [
    "Needs", "Savings", "Debt repayment", "Wants", "Investment", "Other"
]

PRIORITIES = ["High", "Medium", "Low"]

BUDGET_CATEGORIES = [
    "Food & Groceries",
    "Transportation",
    "Bills & Utilities",
    "Education",
    "Health",
    "Shopping",
    "Entertainment",
    "Housing",
    "Savings",
    "Others",
]

SAVINGS_GOAL_CATEGORIES = [
    "Emergency Fund",
    "Education",
    "Travel",
    "Gadgets",
    "House",
    "Vehicle",
    "Business",
    "Others",
]

def parse_amount(value, field_name="Amount", allow_zero=False):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Enter a valid {field_name.lower()}.")

    if not amount.is_finite():
        raise ValueError(f"Enter a valid {field_name.lower()}.")

    if amount < 0 or (amount == 0 and not allow_zero):
        raise ValueError(
            f"{field_name} must be "
            f"{'zero or greater' if allow_zero else 'greater than zero'}."
        )

    return amount


def parse_date(value, field_name):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(f"Select a valid {field_name.lower()}.")


def index(request):
    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        try:
            # TRANSACTIONS
            if action in ["add", "edit"]:
                transaction_id = request.POST.get("transaction_id")

                if action == "edit":
                    transaction = get_object_or_404(
                        Transaction, pk=transaction_id
                    )
                else:
                    transaction = Transaction()

                transaction_type = request.POST.get("transaction_type", "")
                description = request.POST.get("description", "").strip()
                category = request.POST.get("category", "").strip()
                payment_method = request.POST.get("payment_method", "")
                fund_type = request.POST.get("fund_type", "")
                allocation = request.POST.get("allocation", "Needs")
                money_plan = request.POST.get("money_plan", "").strip()
                priority = request.POST.get("priority", "Medium")

                amount = parse_amount(request.POST.get("amount", ""))
                transaction_date = parse_date(
                    request.POST.get("date"), "transaction date"
                )

                if transaction_type not in ["Income", "Expense"]:
                    raise ValueError("Choose Income or Expense.")

                if not description or not category:
                    raise ValueError("Description and category are required.")

                if len(description) > 100 or len(category) > 100:
                    raise ValueError("Description or category is too long.")

                if payment_method not in PAYMENT_METHODS:
                    raise ValueError("Choose a valid payment method.")

                if fund_type not in FUND_TYPES:
                    raise ValueError("Choose Cash or Digital.")

                if allocation not in ALLOCATIONS:
                    raise ValueError("Choose a valid money allocation.")

                if priority not in PRIORITIES:
                    raise ValueError("Choose a valid priority.")

                transaction.transaction_type = transaction_type
                transaction.amount = amount
                transaction.description = description
                transaction.date = transaction_date
                transaction.payment_method = payment_method
                transaction.fund_type = fund_type
                transaction.category = category
                transaction.allocation = allocation
                transaction.money_plan = money_plan
                transaction.priority = priority
                transaction.save()

                messages.success(request, "Transaction saved successfully.")

            elif action == "add_budget_expense":
                budget = get_object_or_404(
                    Budget,
                    pk=request.POST.get("budget_id")
                )

                expense_amount = parse_amount(
                    request.POST.get("expense_amount", ""),
                    field_name="Expense amount",
                )

                expense_date = timezone.localdate()

                if not (
                    budget.start_date <= expense_date <= budget.end_date
                ):
                    raise ValueError(
                        "Today's date must be within this budget's date range."
                    )

                Transaction.objects.create(
                    transaction_type="Expense",
                    amount=expense_amount,
                    description=f"{budget.category} expense",
                    date=expense_date,
                    payment_method="Other",
                    fund_type="Cash",
                    category=budget.category,
                    allocation="Needs",
                    money_plan="",
                    priority="Medium",
                )

                messages.success(
                    request,
                    f"₱{expense_amount:,.2f} expense added to "
                    f"{budget.category}. Your remaining budget has been updated."
                )

            elif action == "delete":
                transaction = get_object_or_404(
                    Transaction, pk=request.POST.get("transaction_id")
                )
                transaction.delete()
                messages.success(request, "Transaction deleted successfully.")


                        # BUDGETS
            elif action in ["add_budget", "edit_budget"]:
                budget_id = request.POST.get("budget_id")

                if action == "edit_budget":
                    budget = get_object_or_404(
                        Budget, pk=budget_id
                    )
                else:
                    budget = Budget()

                category = request.POST.get(
                    "budget_category", ""
                ).strip()

                if category == "Others":
                    category = request.POST.get(
                        "budget_category_other", ""
                    ).strip()

                amount = parse_amount(
                    request.POST.get("budget_amount", ""),
                    field_name="Budget amount",
                )

                spending_limit = parse_amount(
                    request.POST.get("spending_limit", ""),
                    field_name="Spending limit",
                )

                start_date = parse_date(
                    request.POST.get("start_date"),
                    "start date",
                )

                end_date = parse_date(
                    request.POST.get("end_date"),
                    "end date",
                )

                if not category:
                    raise ValueError(
                        "Please select or enter a budget category."
                    )

                if len(category) > 100:
                    raise ValueError(
                        "Budget category cannot exceed 100 characters."
                    )

                if end_date < start_date:
                    raise ValueError(
                        "End date cannot be before start date."
                    )

                if spending_limit > amount:
                    raise ValueError(
                        "The spending limit cannot exceed the total budget."
                    )

                budget.category = category
                budget.amount = amount
                budget.spending_limit = spending_limit
                budget.start_date = start_date
                budget.end_date = end_date
                budget.save()

                messages.success(
                    request,
                    "Budget saved successfully."
                )

            elif action == "delete_budget":
                budget = get_object_or_404(
                    Budget,
                    pk=request.POST.get("budget_id")
                )
                budget.delete()

                messages.success(
                    request,
                    "Budget deleted successfully."
                )

            
            # SAVINGS GOALS
            elif action in ["add_goal", "edit_goal"]:
                goal_id = request.POST.get("goal_id")

                if action == "edit_goal":
                    goal = get_object_or_404(
                        SavingsGoal, pk=goal_id
                    )
                else:
                    goal = SavingsGoal()

                selected_category = request.POST.get(
                    "goal_category", ""
                ).strip()

                if selected_category == "Others":
                    goal_name = request.POST.get(
                        "goal_name_other", ""
                    ).strip()
                else:
                    goal_name = selected_category

                target_amount = parse_amount(
                    request.POST.get("target_amount", ""),
                    field_name="Target amount",
                )

                current_amount = parse_amount(
                    request.POST.get("current_amount", "0"),
                    field_name="Current savings",
                    allow_zero=True,
                )

                target_date = parse_date(
                    request.POST.get("target_date"),
                    "target date",
                )

                if selected_category not in SAVINGS_GOAL_CATEGORIES:
                    raise ValueError("Choose a valid savings-goal category.")

                if not goal_name:
                    raise ValueError(
                        "Please select a goal or enter a custom goal name."
                    )

                if len(goal_name) > 100:
                    raise ValueError("Goal name cannot exceed 100 characters.")

                goal.goal_name = goal_name
                goal.target_amount = target_amount
                goal.current_amount = current_amount
                goal.target_date = target_date
                goal.save()

                messages.success(request, "Savings goal saved successfully.")

            elif action == "contribute_goal":
                goal = get_object_or_404(
                    SavingsGoal,
                    pk=request.POST.get("goal_id"),
                )

                contribution = parse_amount(
                    request.POST.get("contribution_amount", ""),
                    field_name="Contribution",
                )

                goal.current_amount += contribution
                goal.save(update_fields=["current_amount"])

                messages.success(
                    request,
                    f"₱{contribution:,.2f} added to {goal.goal_name}.",
                )

            elif action == "delete_goal":
                goal = get_object_or_404(
                    SavingsGoal,
                    pk=request.POST.get("goal_id"),
                )
                goal.delete()
                messages.success(request, "Savings goal deleted successfully.")

            else:
                messages.error(request, "Unknown action.")

        except ValueError as error:
            messages.error(request, str(error))
        except InvalidOperation:
            messages.error(request, "Please enter a valid amount.")

        return redirect("index")

    # DASHBOARD TOTALS
    income = (
        Transaction.objects.filter(
            transaction_type__iexact="Income"
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    expenses = (
        Transaction.objects.filter(
            transaction_type__iexact="Expense"
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    transactions = Transaction.objects.order_by("-date", "-transaction_id")

        # BUDGET SPENDING AND PROGRESS
    budgets = list(
        Budget.objects.order_by("end_date", "category")
    )

    for budget in budgets:
        spent = (
            Transaction.objects.filter(
                transaction_type__iexact="Expense",
                category__iexact=budget.category,
                date__range=(
                    budget.start_date,
                    budget.end_date,
                ),
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Existing budgets without a limit use their budget amount.
        limit = (
            budget.spending_limit
            if budget.spending_limit is not None
            else budget.amount
        )

        budget.spent = spent
        budget.effective_limit = limit

        # Money left from the full allocated budget.
        budget.remaining = budget.amount - spent

        # Money left before reaching the spending limit.
        budget.limit_remaining = limit - spent

        if limit > 0:
            budget.percent = min(
                100,
                int(spent / limit * 100)
            )
        else:
            budget.percent = 100 if spent > 0 else 0

        budget.over_limit = spent > limit
        budget.over_budget = spent > budget.amount

    
    # SAVINGS GOAL PROGRESS
    savings_goals = list(SavingsGoal.objects.order_by("target_date"))

    for goal in savings_goals:
        goal.percent = (
            min(100, int(goal.current_amount / goal.target_amount * 100))
            if goal.target_amount
            else 0
        )

        goal.remaining = max(
            Decimal("0.00"),
            goal.target_amount - goal.current_amount
        )

    # DASHBOARD CONTEXT
    # Keep this OUTSIDE the savings_goals loop.
    context = {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
        "transactions": transactions,
        "budgets": budgets,
        "savings_goals": savings_goals,
        "today": timezone.localdate().isoformat(),
        "budget_categories": BUDGET_CATEGORIES,
        "savings_goal_categories": SAVINGS_GOAL_CATEGORIES,
    }

    return render(request, "InvApp/dashboard.html", context)