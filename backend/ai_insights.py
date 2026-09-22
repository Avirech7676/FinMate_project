"""
AI-powered financial insights and analysis
"""
import google.generativeai as genai
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import models
import json
from collections import defaultdict

def generate_subscription_email_template(merchant: str, action: str, gemini_key: str) -> Dict[str, str]:
    """
    Returns {subject, body}. Uses Gemini if configured, otherwise deterministic fallback.
    action: cancel | negotiate
    """
    merchant = (merchant or "the service").strip()
    action = (action or "").lower().strip()

    fallback = {
        "subject": f"Request regarding my {merchant} subscription",
        "body": (
            f"Hello {merchant} Support,\n\n"
            "I’m reaching out about my account/subscription. "
            + (
                "I would like to cancel effective immediately and confirm there will be no further charges.\n\n"
                "Please confirm cancellation and the date it takes effect.\n\n"
                "Thank you,\n"
                "[Your Name]\n"
                "[Your Account Email]\n"
                if action == "cancel"
                else
                "I’m considering cancelling, but I wanted to ask if you can offer a better rate or a retention discount. "
                "If not, please let me know the steps to cancel.\n\n"
                "Thank you,\n"
                "[Your Name]\n"
                "[Your Account Email]\n"
            )
        )
    }

    if not gemini_key:
        return fallback

    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
You write concise, professional customer emails.

Write a {action} email for this merchant/service: {merchant}

Return ONLY strict JSON with keys: subject, body
Constraints:
- body should be 120-220 words
- include placeholders: [Your Name], [Your Account Email]
- if action is negotiate: ask for a discount/retention offer politely
- if action is cancel: request confirmation of cancellation and that no further charges occur
"""
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        if isinstance(data, dict) and "subject" in data and "body" in data:
            return {"subject": str(data["subject"]), "body": str(data["body"])}
    except Exception:
        pass

    return fallback

def analyze_spending_anomalies(db: Session, user: models.User, gemini_key: str) -> Optional[str]:
    """
    Detect unusual spending patterns using AI
    Returns insight text or None if not enough data
    """
    if not gemini_key:
        return None
    
    try:
        genai.configure(api_key=gemini_key)
        
        # Get last 30 days of transactions
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user.user_id,
            models.Transaction.date >= thirty_days_ago
        ).all()
        
        if len(transactions) < 5:
            return None
        
        # Aggregate by category
        category_spending = defaultdict(float)
        daily_amounts = defaultdict(float)
        
        for t in transactions:
            category_spending[t.category] += t.amount
            day_key = t.date.strftime('%Y-%m-%d') if t.date else 'unknown'
            daily_amounts[day_key] += t.amount
        
        # Find high days
        high_spend_days = sorted(daily_amounts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Create analysis prompt
        analysis_data = {
            "total_transactions": len(transactions),
            "categories": dict(category_spending),
            "high_spend_days": high_spend_days,
            "average_daily": sum(daily_amounts.values()) / len(daily_amounts) if daily_amounts else 0
        }
        
        prompt = f"""
        Analyze this user's spending data and identify 2-3 key insights or anomalies:
        {json.dumps(analysis_data)}
        
        Be conversational, brief (2-3 sentences), and slightly humorous if possible.
        Focus on actionable insights, not facts they already know.
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        print(f"Error analyzing spending: {e}")
        return None

def generate_weekly_digest(db: Session, user: models.User, gemini_key: str) -> Optional[Dict]:
    """
    Generate a personalized weekly financial summary
    Returns dict with digest data or None
    """
    if not gemini_key:
        return None
    
    try:
        genai.configure(api_key=gemini_key)
        
        # Get last 7 days of transactions
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user.user_id,
            models.Transaction.date >= seven_days_ago
        ).all()
        
        if not transactions:
            return {
                "title": "Your Weekly Summary",
                "summary": "No transactions this week. Keep saving!",
                "total_spent": 0,
                "highlights": []
            }
        
        # Calculate metrics
        total_spent = sum(t.amount for t in transactions)
        by_category = defaultdict(float)
        
        for t in transactions:
            by_category[t.category] += t.amount
        
        top_category = max(by_category.items(), key=lambda x: x[1])[0] if by_category else "Unknown"
        
        # Get budget goal
        budget_goal = db.query(models.BudgetGoal).filter(
            models.BudgetGoal.user_id == user.user_id,
            models.BudgetGoal.status == "active"
        ).first()
        
        goal_status = ""
        if budget_goal:
            goal_status = f"Goal: ${budget_goal.target_amount:.2f}. Progress: ${budget_goal.current_progress:.2f}"
        
        # Generate insights via AI
        prompt = f"""
        Create a friendly, motivational weekly financial summary for a user:
        - Total spent this week: ${total_spent:.2f}
        - Top category: {top_category} (${by_category[top_category]:.2f})
        - Transactions: {len(transactions)}
        {goal_status}
        
        Provide a 1-2 sentence motivational message about their spending this week.
        Be encouraging but honest.
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        return {
            "title": "Your Weekly Summary",
            "summary": response.text.strip(),
            "total_spent": round(total_spent, 2),
            "top_category": top_category,
            "transaction_count": len(transactions),
            "highlights": [
                f"You spent most on {top_category}",
                f"Made {len(transactions)} transactions"
            ]
        }
    
    except Exception as e:
        print(f"Error generating weekly digest: {e}")
        return None

def suggest_budget_optimization(db: Session, user: models.User, gemini_key: str) -> Optional[str]:
    """
    AI-powered budget optimization suggestions
    """
    if not gemini_key:
        return None
    
    try:
        genai.configure(api_key=gemini_key)
        
        # Get last 90 days
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user.user_id,
            models.Transaction.date >= ninety_days_ago
        ).all()
        
        if len(transactions) < 10:
            return None
        
        # Calculate category averages
        category_avg = defaultdict(lambda: {"count": 0, "total": 0})
        for t in transactions:
            category_avg[t.category]["count"] += 1
            category_avg[t.category]["total"] += t.amount
        
        category_stats = {
            cat: round(data["total"] / data["count"], 2)
            for cat, data in category_avg.items()
        }
        
        prompt = f"""
        Given this user's spending patterns over 90 days, suggest 2 specific, actionable budget optimizations:
        
        Spending by category (average per transaction):
        {json.dumps(category_stats)}
        
        Be specific and practical. Avoid obvious advice.
        Format as bullet points, max 150 characters per suggestion.
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        print(f"Error suggesting budget optimization: {e}")
        return None

def detect_unusual_expenses(db: Session, user: models.User) -> List[Dict]:
    """
    Detect transactions that are outliers
    Returns list of unusual transactions
    """
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user.user_id
    ).order_by(models.Transaction.date.desc()).limit(100).all()
    
    if len(transactions) < 10:
        return []
    
    unusual = []
    
    # Get category averages
    by_category = defaultdict(list)
    for t in transactions:
        by_category[t.category].append(t.amount)
    
    # Check for outliers (amount > 2x the average in that category)
    for t in transactions[:20]:  # Check recent transactions
        category_avg = sum(by_category[t.category]) / len(by_category[t.category])
        if t.amount > category_avg * 2:
            unusual.append({
                "transaction_id": t.transaction_id,
                "description": t.description,
                "amount": t.amount,
                "category": t.category,
                "reason": f"${t.amount:.2f} is 2x+ your usual {t.category} spending (avg: ${category_avg:.2f})"
            })
    
    return unusual[:3]  # Return top 3 unusual expenses
