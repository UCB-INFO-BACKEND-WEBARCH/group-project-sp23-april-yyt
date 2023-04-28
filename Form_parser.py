from flask import Flask, request, render_template
import redis

app = Flask(__name__)
db = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/submit_form', methods=['POST'])
def index():
    if request.method == 'POST':
        # Save user data to Redis database
        user_id = request.form['user_id']
        db.hset(user_id, 'age', request.form['age'])
        db.hset(user_id, 'occupation', request.form['occupation'])
        db.hset(user_id, 'annual_income', request.form['annual_income'])
        #db.hset(user_id, 'credit_card_statement', request.form['credit_card_statement'])
        db.hset(user_id, 'investment_goal', request.form['goal'])
        db.hset(user_id, 'investment_proportion', request.form['allocation_proportion'])
        db.hset(user_id, 'goal_achievement_time', request.form['time'])
        db.hset(user_id, 'risk_tolerance', request.form['risk_tolerance'])
        db.hset(user_id, 'investment_type', request.form['investment_types'])
        if request.form['investment_goal'] == 'house':
            db.hset(user_id, 'house_price', request.form['house_amount'])
            db.hset(user_id, 'house_settlement', request.form['house_settlement'])
            db.hset(user_id, 'house_loan_years', request.form['house_loan_years'])
        elif request.form['investment_goal'] == 'car':
            db.hset(user_id, 'car_price', request.form['car_price'])
            db.hset(user_id, 'car_settlement', request.form['car_settlement'])
            db.hset(user_id, 'car_loan_years', request.form['car_loan_years'])
        elif request.form['investment_goal'] == 'retirement':
            db.hset(user_id, 'retirement_year', request.form['retirement_year'])
            db.hset(user_id, 'current_age', request.form['current_age'])
            db.hset(user_id, 'retirement_monthly_income', request.form['retirement_income'])
        elif request.form['investment_goal'] == 'college':
            db.hset(user_id, 'years_until_college', request.form['years_until'])
            db.hset(user_id, 'total_savings', request.form['total_savings'])
    return render_template('success.html', user_id=user_id)
    #return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
