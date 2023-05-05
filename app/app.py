from flask import render_template, request, redirect, url_for, Flask, jsonify
import redis
import os
import openai
from dotenv import load_dotenv
import re
import pandas as pd
import numpy as np 
from typing import Union, List, Callable
import json
openai.api_key = os.environ.get('CHATGPT_API_KEY')
from io import StringIO
import requests

# Imports for asynchronous tasks
from worker.task import get_result_from_GPT, get_expense_data
from celery import Celery

app = Flask(__name__)
celery_app = Celery('worker', broker='redis://redis:6379/0', backend='redis://redis:6379/0')


load_dotenv()


@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit_form', methods=['POST'])
def submit():

    """
    Saves user data from submitted form to a Redis database based on the information provided in a POST request.

    Parameters:
    None

    Returns:
    A Flask response object with the 'success.html' template and a user_id parameter.

    Raises:
    None
    """
    db = redis.Redis(host='localhost', port=6379, db=0)
    user_id = request.form['user_id']
    if request.method == 'POST':

        # Grab file upload and user_id
        cc_history =  request.files['cc_upload']
        if cc_history:
            # Save the file to Redis
            db.hset(user_id, 'uploaded_csv', cc_history.read())
        
        db.hset(user_id, 'age', request.form['age'])
        db.hset(user_id, 'occupation', request.form['occupation'])
        db.hset(user_id, 'annual_income', request.form['annual_income'])
        db.hset(user_id, 'rent', request.form['rent'])
        db.hset(user_id, 'location', request.form['location'])
        db.hset(user_id, 'investment_goal', request.form['investment_goal'])
        db.hset(user_id, 'investment_proportion', request.form['allocation_proportion'])
        db.hset(user_id, 'goal_achievement_time', request.form['time'])
        db.hset(user_id, 'risk_tolerance', request.form['risk_tolerance'])
        db.hset(user_id, 'investment_types', request.form['investment_types'])
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

    #                        queue name in task folder.function name
    expense_task = celery_app.send_task('task.get_expense_data', kwargs={'user_id': user_id})
    # app.logger.info(expense_task.backend)
    advice_task = celery_app.send_task('task.get_result_from_GPT', kwargs={'user_id': user_id})
    # app.logger.info(expense_task.backend)    

    # expense_task = get_expense_data.delay(user_id)
    # advice_task = get_result_from_GPT.delay(user_id)
    
    redirect(url_for('success', user_id=user_id))
    return jsonify({'expense_task_id': expense_task.id, 'advice_task_id': advice_task.id}), 202

@app.route('/check_task_status/<expense_task_id>/<advice_task_id>', methods=['GET'])
def check_task_status(expense_task_id, advice_task_id):
    # expense_task = get_expense_data.AsyncResult(expense_task_id)
    # advice_task = get_result_from_GPT.AsyncResult(advice_task_id)

    expense_task = celery_app.AsyncResult(expense_task_id, app=celery_app)
    advice_task = celery_app.AsyncResult(advice_task_id, app=celery_app)

    # if expense_task.ready():
    #     result = expense_task.get()
    #     return render_template('success.html', result=result)
    # elif advice_task.ready():
    #     result = advice_task.get()
    #     return render_template('success.html', result=result)
    # else:
    #     # Print current progress or return the status as JSON
    #     print(f'Task is not yet complete. Current status: {task.state}')
    #     return jsonify({'status': 'in_progress', 'current_state': advice_task.state})
    
    # return jsonify({'status': 'in_progress', 'current_state': advice_task.state})
    if advice_task.ready():
        result = advice_task.result
        # Render the success/viz page or return the data as JSON
        # return render_template('success.html', result=result)
        return jsonify({'status': 'completed', 'result': result})
    else:
        # Print current progress or return the status as JSON
        # print(f'Task is not yet complete. Current status: {task.state}')
        return jsonify({'status': 'in_progress', 'current_state': advice_task.state})


#### parsing the advice text ####

def extract_advice(text):
    advice = {}
    
    # Extract monthly expense
    monthly_expense_1 = re.search(r'Your monthly expenses add up to approximately \$([\d,]+)', text)
    monthly_expense_2 = re.search(r'Based on your monthly expenses of \$([\d,]+)', text)
    if monthly_expense_1:
        advice['monthly_expense'] = float(monthly_expense_1.group(1).replace(',', ''))
    elif monthly_expense_2:
        advice['monthly_expense'] = float(monthly_expense_2.group(1).replace(',', ''))

    # Extract emergency fund lower and upper bounds
    emergency_fund = re.search(r'an emergency fund of \$([\d,]+) to \$([\d,]+)', text)
    if emergency_fund:
        advice['emergency_fund_lower_bound'] = float(emergency_fund.group(1).replace(',', ''))
        advice['emergency_fund_upper_bound'] = float(emergency_fund.group(2).replace(',', ''))

    # Extract down payment amount
    down_payment = re.search(r'home is \$([\d,]+)', text)
    if down_payment:
        advice['down_payment_amount'] = float(down_payment.group(1).replace(',', ''))

    # Extract downpayment time
    downpayment_time = re.search(r'aim to buy the house in (\d+) years', text)
    if downpayment_time:
        advice['downpayment_time'] = int(downpayment_time.group(1))

    # Extract downpayment saving goal
    saving_goal = re.search(r'you\'ll need to save or invest \$([\d,]+) annually', text)
    if saving_goal:
        advice['downpayment_saving_goal'] = float(saving_goal.group(1).replace(',', ''))

    # Extract investment ratios
    bonds_ratio = re.search(r'(-?\d+)-(-?\d+)% in bonds', text)
    stocks_ratio = re.search(r'(-?\d+)-(-?\d+)% in stocks', text)
    mutual_funds_ratio = re.search(r'(-?\d+)-(-?\d+)% in mutual funds', text)
    derivatives_ratio = re.search(r'(-?\d+)-(-?\d+)% in derivatives', text)


    if bonds_ratio:
        advice['bonds_investment_ratio'] = (float(bonds_ratio.group(1)) + float(bonds_ratio.group(2))) / 2
    else:
        advice['bonds_investment_ratio'] = 0

    if stocks_ratio:
        advice['stocks_investment_ratio'] = (float(stocks_ratio.group(1)) + float(stocks_ratio.group(2))) / 2
    else:
        advice['stocks_investment_ratio'] = 0

    if mutual_funds_ratio:
        advice['mutual_funds_investment_ratio'] = (float(mutual_funds_ratio.group(1)) + float(mutual_funds_ratio.group(2))) / 2
    else:
        advice['mutual_funds_investment_ratio'] = 0

    if derivatives_ratio:
        advice['derivatives_investment_ratio'] = (float(derivatives_ratio.group(1)) + float(derivatives_ratio.group(2))) / 2
    else:
        advice['derivatives_investment_ratio'] = 0

    
    advice['derivatives_investment_ratio'] = 100 - advice['bonds_investment_ratio'] - advice['stocks_investment_ratio'] - advice['mutual_funds_investment_ratio'] - advice['derivatives_investment_ratio']

    return advice


def parse_advice(result_text):
    # db = redis.Redis(host='localhost', port=6379, db=0)
    # advice_text = db.hget(user_id, 'advice_text')
    paragraph = result_text
    # if advice_text:
    #     paragraph = advice_text
    #     # .decode('utf-8')
    # else:
    #     paragraph = None
    advice_dict = extract_advice(paragraph)
    print(advice_dict)
    return advice_dict



@app.route('/success/<user_id>')
def success(user_id, result):
    result = chat_gpt_result(user_id)
    result_dict = parse_advice(result)

    ## adding other data entries to the dictionary
    db = redis.Redis(host='localhost', port=6379, db=0)

    result_dict['user_id'] = user_id
    # result_dict['monthly_expenses'] = db.hget(user_id, 'monthly_expenses')
    result_dict['age'] = db.hget(user_id, 'age')
    result_dict['occupation'] = db.hget(user_id, 'occupation')
    result_dict['annual_income'] = db.hget(user_id, 'annual_income')
    result_dict['rent'] = db.hget(user_id, 'rent')
    result_dict['location'] = db.hget(user_id, 'location')
    result_dict['investment_goal'] = db.hget(user_id, 'investment_goal')
    result_dict['investment_proportion'] = db.hget(user_id, 'investment_proportion')
    result_dict['goal_achievement_time'] = db.hget(user_id, 'goal_achievement_time')
    result_dict['risk_tolerance'] = db.hget(user_id, 'risk_tolerance')
    result_dict['investment_type'] = db.hget(user_id, 'investment_type')
    result_dict['result'] = result

    result_dict['food'] = db.hget(user_id, 'food')
    result_dict['fitness'] = db.hget(user_id, 'fitness')
    result_dict['travel'] = db.hget(user_id, 'travel')
    result_dict['education'] = db.hget(user_id, 'education')
    result_dict['entertainment'] = db.hget(user_id, 'entertainment')

    if not result_dict['monthly_expense']:
        # result_dict['monthly_expenses'] = 3750
        result_dict['food'] + result_dict['fitness'] + result_dict['travel'] + result_dict['education'] + result_dict['entertainment']+ result_dict['rent']

# #     # return render_template('success.html', user_id=user_id, task_id=task_id, result = result)
    return render_template('success.html', **result_dict)


@app.route('/get_response', methods=['GET'])
def chat_gpt_result(user_id):
    """
    Retrieves a response generated by the OpenAI GPT model based on the given user ID.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        If the response was successfully generated, returns the generated text and a status code of 200.
        If the response generation failed, returns an error message and a status code of 500.
    """
    text, status_code = get_result_from_GPT(user_id)
    if status_code == 500:
        return 'Unable to complete prompt', 500
    elif status_code == 200:
        return text
