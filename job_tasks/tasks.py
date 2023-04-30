from celery_config import app

@app.task
def analyze_spending_income(spending, income):
    # plug in how gpt/bert analyzes spending & income here
    result = "Analyzed spending & income"
    return result
