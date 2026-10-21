from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from datetime import date
from decimal import Decimal, InvalidOperation
from django.db.models import Sum

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Transaction, Budget, SavingsGoal

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    form = SignUpForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            "Your account has been created successfully."
        )
        return redirect("index")

    return render(
        request,
        "InvApp/signup.html",
        {"form": form}
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    form = AuthenticationForm(
        request=request,
        data=request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Login successful.")
        return redirect("index")

    return render(
        request,
        "InvApp/login.html",
        {"form": form}
    )

@login_required
def index(request):
    if request.method == "POST":
        action = request.POST.get("action", "").strip()


        # -------------------------
        # ADD BUDGET OR EDIT BUDGET
        # -------------------------
        if action in ("add_budget", "edit_budget"):
            category = request.POST.get("budget_category", "").strip()
            custom_category = request.POST.get(
                "budget_category_other", ""
            ).strip()
            payment_method = request.POST.get(
                "payment_method", ""
            ).strip()

            if category.lower() == "others":
                category = custom_category

            try:
                amount = Decimal(request.POST.get("budget_amount", "0"))
                spending_limit = Decimal(
                    request.POST.get("spending_limit", "0")
                )
                start_date = date.fromisoformat(
                    request.POST.get("start_date", "")
                )
                end_date = date.fromisoformat(
                    request.POST.get("end_date", "")
                )

                if not category:
                    raise ValueError("Please enter a budget category.")

                if amount <= 0 or spending_limit <= 0:
                    raise ValueError("Amounts must be greater than zero.")

                if spending_limit > amount:
                    raise ValueError(
                        "The spending limit cannot exceed the total budget."
                    )

                if end_date < start_date:
                    raise ValueError(
                        "The end date cannot be before the start date."
                    )

                if action == "add_budget":
                    Budget.objects.create(
                        user=request.user,
                        category=category,
                        amount=amount,
                        spending_limit=spending_limit,
                        start_date=start_date,
                        end_date=end_date,
                        payment_method=payment_method,
                    )
                    messages.success(request, "Budget added successfully.")

                else:
                    budget = Budget.objects.get(
                        budget_id=request.POST.get("budget_id"),
                        user=request.user,
                    )
                    budget.category = category
                    budget.amount = amount
                    budget.spending_limit = spending_limit
                    budget.start_date = start_date
                    budget.end_date = end_date
                    budget.payment_method = payment_method
                    budget.save()

                    messages.success(request, "Budget updated successfully.")

            except (InvalidOperation, ValueError, TypeError):
                messages.error(
                    request,
                    "Please check your budget details and enter valid amounts and dates.",
                )
            except Budget.DoesNotExist:
                messages.error(request, "Budget not found.")

            return redirect("/#budgets")

        # -------------------------
        # DELETE BUDGET
        # -------------------------
        elif action == "delete_budget":
            budget = Budget.objects.filter(
                budget_id=request.POST.get("budget_id"),
                user=request.user,
            ).first()

            if budget:
                budget.delete()
                messages.success(request, "Budget deleted successfully.")
            else:
                messages.error(request, "Budget not found.")

            return redirect("/#budgets")

        # -------------------------
        # ADD OR EDIT SAVINGS GOAL
        # -------------------------
        elif action in ("add_goal", "edit_goal"):
            goal_name = request.POST.get("goal_category", "").strip()
            custom_name = request.POST.get(
                "goal_name_other", ""
            ).strip()

            if goal_name.lower() == "others":
                goal_name = custom_name

            try:
                target_amount = Decimal(
                    request.POST.get("target_amount", "0")
                )
                current_amount = Decimal(
                    request.POST.get("current_amount", "0")
                )
                target_date = date.fromisoformat(
                    request.POST.get("target_date", "")
                )

                if not goal_name:
                    raise ValueError("Please enter a savings goal.")

                if target_amount <= 0 or current_amount < 0:
                    raise ValueError("Please enter valid savings amounts.")

                if current_amount > target_amount:
                    raise ValueError(
                        "Current savings cannot exceed the target amount."
                    )

                if action == "add_goal":
                    SavingsGoal.objects.create(
                        user=request.user,
                        goal_name=goal_name,
                        target_amount=target_amount,
                        current_amount=current_amount,
                        target_date=target_date,
                    )
                    messages.success(
                        request, "Savings goal added successfully."
                    )

                else:
                    goal = SavingsGoal.objects.get(
                        goal_id=request.POST.get("goal_id"),
                        user=request.user,
                    )
                    goal.goal_name = goal_name
                    goal.target_amount = target_amount
                    goal.current_amount = current_amount
                    goal.target_date = target_date
                    goal.save()

                    messages.success(
                        request, "Savings goal updated successfully."
                    )

            except (InvalidOperation, ValueError, TypeError):
                messages.error(
                    request,
                    "Please check your savings goal details and enter valid amounts and a date.",
                )
            except SavingsGoal.DoesNotExist:
                messages.error(request, "Savings goal not found.")

            return redirect("/#goals")

        # -------------------------
        # ADD MONEY TO A GOAL
        # -------------------------
        elif action == "contribute_goal":
            goal = SavingsGoal.objects.filter(
                goal_id=request.POST.get("goal_id"),
                user=request.user,
            ).first()

            if not goal:
                messages.error(request, "Savings goal not found.")
                return redirect("/#goals")

            try:
                contribution = Decimal(
                    request.POST.get("contribution_amount", "0")
                )

                if contribution <= 0:
                    raise ValueError

                goal.current_amount += contribution
                goal.save(update_fields=["current_amount"])

                messages.success(
    request,
    f"₱{contribution:,.2f} added to your "
    f"{goal.goal_name} savings goal.",
)

            except (InvalidOperation, ValueError, TypeError):
                messages.error(
                    request,
                    "Enter a valid contribution greater than zero.",
                )

            return redirect("/#goals")


        # -------------------------
        # ADD EXPENSE DIRECTLY TO A BUDGET
        # -------------------------
        elif action == "add_budget_expense":
            try:
                budget = Budget.objects.filter(
                    budget_id=request.POST.get("budget_id"),
                    user=request.user,
                ).first()

                if not budget:
                    messages.error(request, "Budget not found.")
                    return redirect("/#budgets")

                amount = Decimal(request.POST.get("amount", "0"))

                if not amount.is_finite() or amount <= 0:
                    raise ValueError("Enter a valid expense amount.")

                # Budget expenses must be recorded within the budget period.
                expense_date = date.today()

                if not (budget.start_date <= expense_date <= budget.end_date):
                    messages.error(
                        request,
                        "Today's date is outside this budget's date range.",
                    )
                    return redirect("/#budgets")

                # Calculate how much has already been spent in this budget.
                spending_limit = budget.spending_limit or budget.amount

                spent = (
                    Transaction.objects.filter(
                        user=request.user,
                        transaction_type__iexact="expense",
                        category__iexact=budget.category,
                        date__gte=budget.start_date,
                        date__lte=budget.end_date,
                    ).aggregate(total=Sum("amount"))["total"]
                    or Decimal("0.00")
                )

                remaining = spending_limit - spent

                if remaining <= 0:
                    messages.error(
                        request,
                        "This budget has no remaining balance.",
                    )
                    return redirect("/#budgets")

                if amount > remaining:
                    messages.error(
                        request,
                        f"Expense exceeds the remaining budget of "
                        f"₱{remaining:,.2f}.",
                    )
                    return redirect("/#budgets")

                # Save the expense as a real transaction.
                Transaction.objects.create(
                    user=request.user,
                    transaction_type="Expense",
                    amount=amount,
                    description=f"Budget expense - {budget.category}",
                    date=expense_date,
                    payment_method=budget.payment_method or "Cash",
                    fund_type="Cash",
                    category=budget.category,
                    allocation="Needs",
                    money_plan="",
                    priority="Medium",
                )

                messages.success(
                    request,
                    f"₱{amount:,.2f} expense added to your "
                    f"{budget.category} budget.",
                )

            except (InvalidOperation, ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter a valid expense amount.",
                )

            return redirect("/#budgets")

        # -------------------------
        # DELETE TRANSACTION
        # -------------------------
        elif action == "delete":
            transaction = Transaction.objects.filter(
                transaction_id=request.POST.get("transaction_id"),
                user=request.user,
            ).first()

            if transaction:
                transaction.delete()
                messages.success(
                    request, "Transaction deleted successfully."
                )
            else:
                messages.error(request, "Transaction not found.")

            return redirect("/#transactions")

       
        # -------------------------
        # ADD TRANSACTION
        # -------------------------
        elif action == "add":
            try:
                amount = Decimal(request.POST.get("amount", "0"))
                transaction_date = date.fromisoformat(
                    request.POST.get("date", "")
                )

                transaction_type = request.POST.get(
                    "transaction_type", ""
                ).strip()
                description = request.POST.get("description", "").strip()
                category = request.POST.get("category", "").strip()
                payment_method = request.POST.get(
                    "payment_method", ""
                ).strip()

                if amount <= 0:
                    raise ValueError("Amount must be greater than zero.")

                if transaction_type.lower() not in ("income", "expense"):
                    raise ValueError("Select Income or Expense.")

                if not all((description, category, payment_method)):
                    raise ValueError("Please complete all required fields.")

                # Block expenses if the matching budget is exhausted.
                if transaction_type.lower() == "expense":
                    matching_budgets = Budget.objects.filter(
                        user=request.user,
                        category__iexact=category,
                        start_date__lte=transaction_date,
                        end_date__gte=transaction_date,
                    )

                    for budget in matching_budgets:
                        spending_limit = (
                            budget.spending_limit or budget.amount
                        )

                        spent = sum(
                            Transaction.objects.filter(
                                user=request.user,
                                transaction_type__iexact="expense",
                                category__iexact=budget.category,
                                date__gte=budget.start_date,
                                date__lte=budget.end_date,
                            ).values_list("amount", flat=True),
                            Decimal("0.00"),
                        )

                        remaining = spending_limit - spent

                        if remaining <= 0:
                            messages.error(
                                request,
                                f"The {budget.category} budget is exhausted. "
                                "You cannot add more expenses to this budget.",
                            )
                            return redirect("/#budgets")

                Transaction.objects.create(
                    user=request.user,
                    transaction_type=transaction_type,
                    amount=amount,
                    description=description,
                    date=transaction_date,
                    payment_method=payment_method,
                    fund_type=request.POST.get("fund_type", "Cash"),
                    category=category,
                    allocation=request.POST.get("allocation", "Needs"),
                    money_plan=request.POST.get("money_plan", "").strip(),
                    priority=request.POST.get("priority", "Medium"),
                )

                messages.success(
                    request, "Transaction added successfully."
                )

            except (InvalidOperation, ValueError, TypeError):
                messages.error(
                    request,
                    "Please check the transaction details and try again.",
                )

            return redirect("/#transactions")


    # -------------------------
    # LOAD DASHBOARD DATA
    # -------------------------
    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by("-date", "-transaction_id")

    budgets = Budget.objects.filter(
        user=request.user
    ).order_by("-start_date")

    savings_goals = SavingsGoal.objects.filter(
        user=request.user
    ).order_by("-goal_id")

    # Calculate totals from the logged-in user's actual transactions.
    income = (
        transactions.filter(
            transaction_type__iexact="income"
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    expenses = (
        transactions.filter(
            transaction_type__iexact="expense"
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    balance = income - expenses

    # Calculate each budget's spending and progress.
    for budget in budgets:
        spending_limit = budget.spending_limit or budget.amount

        spent = sum(
            (
                transaction.amount
                for transaction in transactions
                if transaction.transaction_type.lower() == "expense"
                and transaction.category.lower() == budget.category.lower()
                and budget.start_date <= transaction.date <= budget.end_date
            ),
            Decimal("0.00"),
        )

        budget.spent = spent
        budget.remaining = spending_limit - spent
        budget.percent = min(
            100,
            int((spent / spending_limit * 100))
            if spending_limit > 0 else 0,
        )
        budget.over_budget = spent > budget.amount
        budget.over_limit = spent > spending_limit

    # Calculate each savings goal's progress.
    for goal in savings_goals:
        goal.remaining = max(
            Decimal("0.00"),
            goal.target_amount - goal.current_amount,
        )
        goal.percent = min(
            100,
            int((goal.current_amount / goal.target_amount * 100))
            if goal.target_amount > 0 else 0,
        )

    context = {
        "transactions": transactions,
        "budgets": budgets,
        "savings_goals": savings_goals,
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "today": date.today().isoformat(),
        "budget_categories": [
            "Food", "Transport", "Housing", "Utilities",
            "Education", "Health", "Entertainment",
            "Shopping", "Savings", "Others",
        ],
        "savings_goal_categories": [
            "Emergency Fund", "Travel", "Education",
            "New Gadget", "Vehicle", "House",
            "Retirement", "Others",
        ],
    }

    return render(request, "InvApp/dashboard.html", context)


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have logged out.")
        return redirect("login")

    return redirect("index")