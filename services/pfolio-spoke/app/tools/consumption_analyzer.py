"""
Consumption Analyzer Tool - Analyze spending patterns and investment capacity
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .base_tool import BaseTool


class ConsumptionAnalyzer(BaseTool):
    """Tool for analyzing consumption patterns and investment capacity"""

    def __init__(self):
        super().__init__(
            tool_id="pfolio.analyze_consumption",
            name="Analyze Consumption",
            description="소비 패턴을 분석하고 투자 여력을 평가합니다"
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute consumption analysis"""
        try:
            # Validate required arguments
            self.validate_arguments(arguments, ["monthly_income", "expenses"])

            monthly_income = arguments["monthly_income"]
            expenses = arguments["expenses"]
            period_months = arguments.get("period_months", 12)
            savings_goal = arguments.get("savings_goal", 0.2)  # 20% default

            print(f"Analyzing consumption for income: ${monthly_income:,.2f}/month")

            # Analyze consumption patterns
            consumption_data = await self._analyze_consumption(
                monthly_income, expenses, period_months, savings_goal
            )

            return self.create_success_response(
                data=consumption_data,
                metadata={
                    "monthly_income": monthly_income,
                    "analysis_period": period_months,
                    "savings_goal": savings_goal,
                    "analysis_date": datetime.now().isoformat()
                }
            )

        except Exception as e:
            return await self.handle_error(e, "consumption_analysis")

    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "monthly_income": {
                        "type": "number",
                        "description": "Monthly after-tax income in USD",
                        "minimum": 1000
                    },
                    "expenses": {
                        "type": "object",
                        "description": "Monthly expenses by category",
                        "properties": {
                            "housing": {"type": "number", "minimum": 0},
                            "food": {"type": "number", "minimum": 0},
                            "transportation": {"type": "number", "minimum": 0},
                            "utilities": {"type": "number", "minimum": 0},
                            "healthcare": {"type": "number", "minimum": 0},
                            "entertainment": {"type": "number", "minimum": 0},
                            "shopping": {"type": "number", "minimum": 0},
                            "other": {"type": "number", "minimum": 0}
                        },
                        "required": ["housing", "food", "transportation"]
                    },
                    "period_months": {
                        "type": "integer",
                        "description": "Analysis period in months",
                        "minimum": 3,
                        "maximum": 24,
                        "default": 12
                    },
                    "savings_goal": {
                        "type": "number",
                        "description": "Target savings rate (0.2 = 20%)",
                        "minimum": 0.05,
                        "maximum": 0.5,
                        "default": 0.2
                    }
                },
                "required": ["monthly_income", "expenses"]
            }
        }

    async def _analyze_consumption(self, monthly_income: float, expenses: Dict[str, float],
                                 period_months: int, savings_goal: float) -> Dict[str, Any]:
        """Analyze consumption patterns and investment capacity"""

        # Calculate basic metrics
        total_expenses = sum(expenses.values())
        monthly_surplus = monthly_income - total_expenses
        current_savings_rate = monthly_surplus / monthly_income if monthly_income > 0 else 0
        target_savings_amount = monthly_income * savings_goal

        # Analyze expense categories
        expense_analysis = []
        for category, amount in expenses.items():
            percentage = (amount / monthly_income) if monthly_income > 0 else 0
            expense_analysis.append({
                "category": category,
                "amount": amount,
                "percentage": round(percentage, 4),
                "status": await self._categorize_expense(category, percentage)
            })

        expense_analysis.sort(key=lambda x: x["amount"], reverse=True)

        # Generate spending insights
        spending_insights = await self._generate_spending_insights(expenses, monthly_income)

        # Calculate investment capacity
        investment_capacity = await self._calculate_investment_capacity(
            monthly_surplus, target_savings_amount, monthly_income
        )

        # Generate recommendations
        recommendations = await self._generate_consumption_recommendations(
            current_savings_rate, savings_goal, expense_analysis, monthly_surplus
        )

        # Project future scenarios
        scenarios = await self._project_scenarios(monthly_income, expenses, savings_goal, period_months)

        # Generate budget optimization
        budget_optimization = await self._optimize_budget(expenses, monthly_income, savings_goal)

        return {
            "income_analysis": {
                "monthly_income": monthly_income,
                "annual_income": monthly_income * 12,
                "after_tax_rate": 0.75,  # Assumed
                "income_stability": "stable"  # Mock assessment
            },
            "expense_summary": {
                "total_monthly_expenses": round(total_expenses, 2),
                "expense_ratio": round(total_expenses / monthly_income, 4),
                "largest_expense": max(expense_analysis, key=lambda x: x["amount"])["category"],
                "expense_categories": len(expenses)
            },
            "expense_breakdown": expense_analysis,
            "savings_analysis": {
                "monthly_surplus": round(monthly_surplus, 2),
                "current_savings_rate": round(current_savings_rate, 4),
                "target_savings_rate": savings_goal,
                "savings_gap": round(target_savings_amount - monthly_surplus, 2),
                "meets_goal": monthly_surplus >= target_savings_amount
            },
            "investment_capacity": investment_capacity,
            "spending_insights": spending_insights,
            "budget_optimization": budget_optimization,
            "scenarios": scenarios,
            "recommendations": recommendations,
            "financial_health": {
                "emergency_fund_months": round(monthly_surplus * 6 / total_expenses, 1) if total_expenses > 0 else 0,
                "debt_to_income": random.uniform(0.1, 0.3),  # Mock data
                "liquidity_ratio": round(monthly_surplus / total_expenses, 2) if total_expenses > 0 else 0,
                "overall_score": self._calculate_financial_health_score(current_savings_rate, total_expenses / monthly_income)
            }
        }

    async def _categorize_expense(self, category: str, percentage: float) -> str:
        """Categorize expense as reasonable, high, or excessive"""
        # Rough guidelines for expense categories
        guidelines = {
            "housing": {"reasonable": 0.30, "high": 0.35},
            "food": {"reasonable": 0.12, "high": 0.15},
            "transportation": {"reasonable": 0.15, "high": 0.20},
            "utilities": {"reasonable": 0.08, "high": 0.12},
            "healthcare": {"reasonable": 0.08, "high": 0.12},
            "entertainment": {"reasonable": 0.05, "high": 0.10},
            "shopping": {"reasonable": 0.05, "high": 0.10},
            "other": {"reasonable": 0.05, "high": 0.10}
        }

        guide = guidelines.get(category, {"reasonable": 0.10, "high": 0.15})

        if percentage <= guide["reasonable"]:
            return "reasonable"
        elif percentage <= guide["high"]:
            return "above_average"
        else:
            return "excessive"

    async def _generate_spending_insights(self, expenses: Dict[str, float], income: float) -> List[Dict[str, Any]]:
        """Generate insights about spending patterns"""
        insights = []
        total_expenses = sum(expenses.values())

        # Housing insight
        housing_ratio = expenses.get("housing", 0) / income
        if housing_ratio > 0.35:
            insights.append({
                "category": "housing",
                "insight": "Housing costs exceed recommended 30% of income",
                "impact": "high",
                "recommendation": "Consider downsizing or refinancing"
            })

        # Food spending insight
        food_ratio = expenses.get("food", 0) / income
        if food_ratio > 0.15:
            insights.append({
                "category": "food",
                "insight": "Food expenses are above average",
                "impact": "medium",
                "recommendation": "Consider meal planning and cooking at home more"
            })

        # Entertainment/discretionary spending
        entertainment_ratio = expenses.get("entertainment", 0) / income
        shopping_ratio = expenses.get("shopping", 0) / income
        discretionary_ratio = entertainment_ratio + shopping_ratio

        if discretionary_ratio > 0.15:
            insights.append({
                "category": "discretionary",
                "insight": "Discretionary spending is high",
                "impact": "medium",
                "recommendation": "Review entertainment and shopping budgets"
            })

        # Overall spending pattern
        if total_expenses / income > 0.8:
            insights.append({
                "category": "overall",
                "insight": "Total expenses are very high relative to income",
                "impact": "high",
                "recommendation": "Focus on expense reduction to improve savings"
            })

        # Add positive insights if doing well
        if total_expenses / income < 0.7:
            insights.append({
                "category": "overall",
                "insight": "Excellent expense management",
                "impact": "positive",
                "recommendation": "Continue current spending discipline"
            })

        return insights

    async def _calculate_investment_capacity(self, monthly_surplus: float, target_savings: float,
                                           income: float) -> Dict[str, Any]:
        """Calculate investment capacity and recommendations"""

        # Conservative approach: don't invest all surplus
        emergency_fund_target = income * 0.25  # 3 months expenses (approx)
        conservative_investment = max(0, monthly_surplus - emergency_fund_target)
        moderate_investment = monthly_surplus * 0.8 if monthly_surplus > 0 else 0
        aggressive_investment = monthly_surplus * 0.95 if monthly_surplus > 0 else 0

        return {
            "monthly_surplus": round(monthly_surplus, 2),
            "investment_scenarios": {
                "conservative": {
                    "monthly_amount": round(max(0, conservative_investment), 2),
                    "annual_amount": round(max(0, conservative_investment) * 12, 2),
                    "description": "After emergency fund allocation"
                },
                "moderate": {
                    "monthly_amount": round(moderate_investment, 2),
                    "annual_amount": round(moderate_investment * 12, 2),
                    "description": "80% of surplus invested"
                },
                "aggressive": {
                    "monthly_amount": round(aggressive_investment, 2),
                    "annual_amount": round(aggressive_investment * 12, 2),
                    "description": "95% of surplus invested"
                }
            },
            "projected_wealth": {
                "5_year_conservative": round(conservative_investment * 12 * 5 * 1.35, 0),  # 7% return
                "10_year_conservative": round(conservative_investment * 12 * 10 * 2.0, 0),
                "5_year_aggressive": round(aggressive_investment * 12 * 5 * 1.45, 0),  # 9% return
                "10_year_aggressive": round(aggressive_investment * 12 * 10 * 2.3, 0)
            },
            "capacity_assessment": "good" if monthly_surplus > income * 0.15 else ("moderate" if monthly_surplus > 0 else "limited")
        }

    async def _optimize_budget(self, expenses: Dict[str, float], income: float,
                             savings_goal: float) -> Dict[str, Any]:
        """Suggest budget optimizations"""

        total_expenses = sum(expenses.values())
        target_expenses = income * (1 - savings_goal)
        needed_reduction = max(0, total_expenses - target_expenses)

        optimizations = []

        if needed_reduction > 0:
            # Prioritize categories for reduction
            reduction_potential = {
                "entertainment": expenses.get("entertainment", 0) * 0.3,
                "shopping": expenses.get("shopping", 0) * 0.4,
                "food": expenses.get("food", 0) * 0.15,
                "utilities": expenses.get("utilities", 0) * 0.1,
                "transportation": expenses.get("transportation", 0) * 0.2,
                "other": expenses.get("other", 0) * 0.25
            }

            for category, potential in sorted(reduction_potential.items(), key=lambda x: x[1], reverse=True):
                if potential > 0 and needed_reduction > 0:
                    reduction = min(potential, needed_reduction)
                    optimizations.append({
                        "category": category,
                        "current_amount": expenses.get(category, 0),
                        "suggested_reduction": round(reduction, 2),
                        "new_amount": round(expenses.get(category, 0) - reduction, 2),
                        "reduction_method": self._get_reduction_method(category)
                    })
                    needed_reduction -= reduction

        return {
            "current_total": round(total_expenses, 2),
            "target_total": round(target_expenses, 2),
            "reduction_needed": round(max(0, total_expenses - target_expenses), 2),
            "optimizations": optimizations,
            "feasibility": "achievable" if len(optimizations) <= 3 else "challenging"
        }

    def _get_reduction_method(self, category: str) -> str:
        """Get suggested method for reducing expenses in category"""
        methods = {
            "entertainment": "Reduce dining out and subscriptions",
            "shopping": "Implement 24-hour rule for purchases",
            "food": "Meal planning and bulk cooking",
            "utilities": "Energy efficiency improvements",
            "transportation": "Optimize routes and consider carpooling",
            "other": "Review and eliminate unnecessary expenses"
        }
        return methods.get(category, "Review and reduce expenses")

    async def _project_scenarios(self, income: float, expenses: Dict[str, float],
                                savings_goal: float, months: int) -> Dict[str, Any]:
        """Project different financial scenarios"""

        current_surplus = income - sum(expenses.values())

        scenarios = {
            "current_path": {
                "monthly_surplus": round(current_surplus, 2),
                "total_saved": round(current_surplus * months, 2),
                "final_savings_rate": round(current_surplus / income, 3) if income > 0 else 0
            },
            "optimized": {
                "monthly_surplus": round(income * savings_goal, 2),
                "total_saved": round(income * savings_goal * months, 2),
                "final_savings_rate": savings_goal
            }
        }

        # Add income growth scenario
        income_growth = 1.03  # 3% annual growth
        years = months / 12
        future_income = income * (income_growth ** years)

        scenarios["income_growth"] = {
            "monthly_surplus": round((future_income - sum(expenses.values())) * (1 + years * 0.02), 2),
            "total_saved": round(current_surplus * months * 1.2, 2),  # Approximate
            "final_savings_rate": round((future_income - sum(expenses.values())) / future_income, 3)
        }

        return scenarios

    async def _generate_consumption_recommendations(self, current_rate: float, goal_rate: float,
                                                  expense_analysis: List[Dict], surplus: float) -> List[str]:
        """Generate consumption recommendations"""
        recommendations = []

        if current_rate >= goal_rate:
            recommendations.append("Excellent! You're meeting your savings goal")
            recommendations.append("Consider increasing investment allocation")
        else:
            gap = goal_rate - current_rate
            recommendations.append(f"Need to improve savings rate by {gap:.1%}")

        # Specific expense recommendations
        excessive_expenses = [exp for exp in expense_analysis if exp["status"] == "excessive"]
        if excessive_expenses:
            top_excessive = excessive_expenses[0]
            recommendations.append(f"Priority: Reduce {top_excessive['category']} expenses")

        if surplus <= 0:
            recommendations.append("Critical: Expenses exceed income - immediate budget review needed")
        elif surplus < 1000:
            recommendations.append("Low surplus - focus on increasing income or reducing expenses")

        # Positive reinforcement
        reasonable_expenses = [exp for exp in expense_analysis if exp["status"] == "reasonable"]
        if len(reasonable_expenses) >= len(expense_analysis) * 0.6:
            recommendations.append("Good job managing most expense categories")

        return recommendations[:5]

    def _calculate_financial_health_score(self, savings_rate: float, expense_ratio: float) -> int:
        """Calculate overall financial health score (1-100)"""
        score = 50  # Base score

        # Savings rate component (0-30 points)
        if savings_rate >= 0.20:
            score += 30
        elif savings_rate >= 0.15:
            score += 25
        elif savings_rate >= 0.10:
            score += 20
        elif savings_rate >= 0.05:
            score += 10

        # Expense ratio component (0-20 points)
        if expense_ratio <= 0.70:
            score += 20
        elif expense_ratio <= 0.80:
            score += 15
        elif expense_ratio <= 0.90:
            score += 10
        elif expense_ratio <= 0.95:
            score += 5

        return max(0, min(100, score))