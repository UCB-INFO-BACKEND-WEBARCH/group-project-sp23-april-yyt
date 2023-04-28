from flask import Flask, request, render_template
import redis
import os
import openai
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
db = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/submit_form', methods=['POST'])
def save_answers():
    if request.method == 'POST':
        # Save user data to Redis database
        user_id = request.form['user_id']
        db.hset(user_id, 'age', request.form['age'])
        db.hset(user_id, 'occupation', request.form['occupation'])
        db.hset(user_id, 'annual_income', request.form['annual_income'])
        db.hset(user_id, 'location', request.form['location'])
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
            db.hset(user_id, 'retirement_monthly_income', request.form['retirement_income'])
        elif request.form['investment_goal'] == 'college':
            db.hset(user_id, 'total_savings', request.form['total_savings'])
    return render_template('success.html', user_id=user_id)
    #return render_template('form.html')
def generate_prompt(user_id):
    age = db.hget(user_id, 'age').decode()
    occupation = db.hget(user_id, 'occupation').decode()
    location = db.hget(user_id, 'location').decode()
    annual_income = int(db.hget(user_id, 'annual_income').decode())
    investment_goal = (db.hget(user_id, 'investment_goal').decode())
    goal_achieve_time = (db.hget(user_id, 'goal_achievement_time').decode())

    #### BN need to store this in redis as well ### 
    rent = 3000
    food = 1000
    fitness = 300
    travel = 500
    education = 600
    entertainment = 400
    ##### 

    investment_proportion = int(db.hget(user_id, 'investment_proportion').decode())
    risk_tolerance = db.hget(user_id, 'risk_tolerance').decode()
    investment_type = db.hget(user_id, 'investment_type').decode()

    # Check user's investment goal and compose prompt accordingly
    if investment_goal == 'house':
        house_price = float(db.hget(user_id, 'house_price').decode())
        house_settlement = int(db.hget(user_id, 'house_settlement').decode())
        house_loan_years = int(db.hget(user_id, 'house_loan_years').decode())
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. 
        I am spending {rent} on rent and utilities, {food} on food & groceries, {fitness} on fitness and health, {travel} on travel, {education} on education, 
        and {entertainment} on entertainment each month. My saving goal is to buy a {house_price} house in {location} with a {house_settlement}% 
        settlement and {house_loan_years} years loan. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. 
        I have my preferred investment types as {', '.join(preferred_investment_types)}. Can you give me personal financial investment advice?"
    elif investment_goal == 'car':
        car_price = float(db.hget(user_id, 'car_price').decode())
        car_settlement = int(db.hget(user_id, 'car_settlement').decode())
        car_load_years = int(db.hget(user_id, 'car_loan_years').decode())
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. 
        I am spending {rent} on rent and utilities, {food} on food & groceries, {fitness} on fitness and health, {travel} on travel, {education} on education, 
        and {entertainment} on entertainment each month. My saving goal is to buy a {car_price} house in {location} with a {car_settlement}% 
        settlement and {car_loan_years} years loan. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. 
        I have my preferred investment types as {', '.join(preferred_investment_types)}. Can you give me personal financial investment advice?"
    elif investment_goal == 'retirement':
        retirement_year = db.hget(user_id, 'retirement_year').decode()
        retirement_month_income = db.hget(user_id, 'retirement_monthly_income').decode()
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. 
        I am spending {rent} on rent and utilities, {food} on food & groceries, {fitness} on fitness and health, {travel} on travel, {education} on education, 
        and {entertainment} on entertainment each month. My saving goal is to save money for retirement. My estimated monthly income after retirement needs to be ${retirement_month_income}. 
        I have {goal_achieve_time} years left to achieve my goal. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. 
        I have my preferred investment types as {', '.join(preferred_investment_types)}. Can you give me personal financial investment advice?"
    

    elif investment_goal == 'college':
        saving_for_college = db.hget(user_id, 'total_savings').decode()
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. 
        I am spending {rent} on rent and utilities, {food} on food & groceries, {fitness} on fitness and health, {travel} on travel, {education} on education, 
        and {entertainment} on entertainment each month. My saving goal is to save money for attending college. my estimated total saving need to be ${saving_for_college}. 
        I have {goal_achieve_time} years left to achieve my goal. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. 
        I have my preferred investment types as {', '.join(preferred_investment_types)}. Can you give me personal financial investment advice?"
    
    return prompt

def get_result_from_GPT(user_id):
    CHATGPT_API_ENDPOINT = 'https://api.openai.com/v1/engines/davinci-codex/completions'
    api_key = os.environ.get('CHATGPT_API_KEY')
    prompt = generate_prompt(user_id)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'prompt': prompt,
        'max_tokens': 1024,
        'temperature': 0.7,
        'n': 1,
        'stop': '\n'
    }

    response = requests.post(CHATGPT_API_ENDPOINT, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    completions = result.get('choices', [])
    if completions:
        generated_text = completions[0]['text']
        return generated_text, 200
    else:
        return 'Unable to complete prompt', 500

@app.route('/get_response', methods=['GET'])
def chat_gpt_result(user_id):
    text, status_code = get_result_from_GPT(user_id)
    if status_code = 500:
        return 'Unable to complete prompt', 500
    elif status_code = 200:
        return text












if __name__ == '__main__':
    app.run(debug=True)
