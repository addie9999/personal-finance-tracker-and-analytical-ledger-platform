"""Twelve portable SQL reports. Amounts are integer paise; net values carry a sign."""
BASE = """
WITH lines AS (
    SELECT e.id, e.posted, substr(CAST(e.posted AS VARCHAR),1,7) AS month,
           a.name AS account, c.name AS category, c.kind, e.amount_minor, e.note,
           CASE WHEN c.kind='income' THEN e.amount_minor ELSE -e.amount_minor END AS net
    FROM entries e JOIN accounts a ON e.account_id=a.id JOIN categories c ON e.category_id=c.id
)
"""
REPORTS = {name: BASE + sql for name, sql in {
    "totals": """SELECT COALESCE(SUM(CASE WHEN kind='income' THEN amount_minor ELSE 0 END),0) AS income,
                 COALESCE(SUM(CASE WHEN kind='expense' THEN amount_minor ELSE 0 END),0) AS expense,
                 COALESCE(SUM(net),0) AS balance FROM lines""",
    "monthly_flow": """SELECT month, SUM(CASE WHEN kind='income' THEN amount_minor ELSE 0 END) AS income,
                 SUM(CASE WHEN kind='expense' THEN amount_minor ELSE 0 END) AS expense,
                 SUM(net) AS net FROM lines GROUP BY month ORDER BY month""",
    "account_balances": "SELECT account,SUM(net) AS balance FROM lines GROUP BY account ORDER BY account",
    "spending_by_category": """SELECT category,SUM(amount_minor) AS expense FROM lines WHERE kind='expense'
                 GROUP BY category ORDER BY expense DESC,category""",
    "income_sources": """SELECT category,SUM(amount_minor) AS income FROM lines WHERE kind='income'
                 GROUP BY category ORDER BY income DESC,category""",
    "recent_entries": """SELECT id,posted,account,category,note,net FROM lines ORDER BY posted DESC,id DESC LIMIT 30""",
    "daily_flow": "SELECT posted,SUM(net) AS net FROM lines GROUP BY posted ORDER BY posted DESC",
    "running_balance": """SELECT posted,id,SUM(net) OVER (ORDER BY posted,id ROWS UNBOUNDED PRECEDING)
                 AS balance FROM lines ORDER BY posted DESC,id DESC LIMIT 30""",
    "largest_expenses": """SELECT posted,note,category,amount_minor AS expense FROM lines WHERE kind='expense'
                 ORDER BY amount_minor DESC,id DESC LIMIT 5""",
    "monthly_change": """, months AS (SELECT month,SUM(net) AS net FROM lines GROUP BY month)
                 SELECT month,net,net-LAG(net) OVER (ORDER BY month) AS change FROM months ORDER BY month""",
    "category_frequency": "SELECT category,COUNT(*) AS count FROM lines GROUP BY category ORDER BY count DESC,category",
    "monthly_spending_rank": """, sums AS (SELECT month,category,SUM(amount_minor) AS expense FROM lines
                 WHERE kind='expense' GROUP BY month,category)
                 SELECT month,category,expense,DENSE_RANK() OVER (PARTITION BY month ORDER BY expense DESC)
                 AS rank FROM sums ORDER BY month DESC,rank,category"""
}.items()}
