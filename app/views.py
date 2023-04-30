from flask import render_template, request, redirect, url_for, Flask
from app import app
import redis
import os
import openai
from dotenv import load_dotenv
# import parse_df
import requests

# Imports for parse df
import re
import pandas as pd
import numpy as np 
# from transformers import pipeline
from typing import Union, List, Callable
import json
import os
import openai
openai.api_key = os.environ.get('CHATGPT_API_KEY')
from io import StringIO

openai.api_key = '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'

load_dotenv()
db = redis.Redis(host='localhost', port=6379, db=0)

def clean_text(text: str): 
    
    """
    Removes the non-essential information about an expense text
    """
    
    # Remove random words
    text = text.replace('PURCHASE', '')
    text = text.replace('AUTHORIZED', '')
    text = text.replace('RECURRING', '')
    text = text.replace("PAYMENT", '')
    text = text.replace("CARD", '')
    text = text.replace("ON", '')
    
    # Remove dates 
    date_pattern = r"\d{2}/\d{2}"
    text = re.sub(date_pattern, "", text)
    
    # Remove cities 
    cities = ['SAN FRANCISCO', 'NEW YORK', 'LOS ANGELES']

    # Define a regular expression pattern to match any of the city names in the list
    city_pattern = '|'.join(cities)

    # Replace all instances of the city pattern with an empty string
    text = re.sub(city_pattern, "", text)
    
    # Remove long valeus 
    pattern = r'\s[PS]\d+\s'
    text = re.sub(pattern, '', text)

    # Strip 
    text = text.strip()

    return text

def load_and_clean_csv(path: str = None, df: str = None): 
    
    """
    Loads a CSV and tries to remove information not about the vendor
    Params: 
        - path (str): the path to a csv file 
    Returns: 
        - df (pd.DataFrame): the cleaned pandas df
        - prompt (str): the completed prompt template
    """

    # Parse the CSV file
    csv_data = db.get('uploaded_csv').decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))[['Date', 'Amount', 'Expense']]

    # csv_data = csv_data.decode('utf-8')
    # csv_rows = csv_data.split('\n')
    # for row in csv_rows:
    #     csv_fields = row.split(',')
    #     # Process each field as necessary
    
    # Load CSV if need to 
    # if (path):
    #     df = pd.read_csv(path)[['Date', 'Amount', 'Expense']]
    
    # Clean text
    df['Expense'] = df['Expense'].apply(clean_text)
    
    # Make columns lowercase
    df.columns = df.columns.str.lower()

    # Add column for month
    df['month'] = pd.to_datetime(df['date']).dt.month


    
    prompt = """
    I'm going to give you a list of bank statement expenses with some text removed (to shorten the token size). 

    Your task is to classify each of these into one of the following categories:

    ['food', 'fitness', 'travel', 'education', 'entertainment']

    If the expense does not fall into one of those categories, return 'other'.

    Please return JSON format like this: {1: 'rent', 2: 'food', 3: 'other'}

    PLEASE MAKE SURE YOU ASSIGN EXACTLY ONE LABEL TO EACH EXPENSE.

    Here are the expenses:
    """

    for idx, row in df.iterrows(): 
        prompt += f'\n {idx+1}: {row["expense"]}'

    
    return df, prompt

def get_monthly_expenses(df): 
    
    """
    Gets the monthly expenses for a given df
    Params: 
        - df (pd.DataFrame): the expenses df
    Returns: 
        - monthly_expenses (dict): dictionary of monthly expenses by category
    """

    # Load in the data and generate prompt
    df, prompt = load_and_clean_csv(df = df)

    # Run query on gpt-3.5-turb 
    labels = openai.ChatCompletion.create(model = 'gpt-3.5-turbo',
                                          messages = [
                                            {"role": "user", "content": prompt},
                                          ])
    
    # Convert the string of lists to list 
    labels = eval(labels['choices'][0]['message']['content'])

    # Add predictions to df
    df['label'] = list(labels.values())

    # Double groupby to get monthly expenses 
    monthly_expenses = df.groupby(['category', 'month'])['amount'].sum().groupby('category').mean().to_dict()

    return monthly_expenses


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
    if request.method == 'POST':

        # Grab file upload and user_id
        cc_history =  request.files['cc_upload']
        if cc_history:
            # Save the file to Redis
            db.set('uploaded_csv', cc_history.read())
            
        
        user_id = request.form['user_id']

        # Extract monthly expenses 
        # monthly_expenses = get_monthly_expenses(cc_history)
        
        # # Insert to redis DB
        # expense_types = ['food', 'fitness', 'travel', 'education', 'entertainment']
        # for expense_type in expense_types: 
        #     val = monthly_expenses.get(expense_type)
        #     db.hset(user_id, expense_type, val)


        # Save user data to Redis database
        user_id = request.form['user_id']
        db.hset(user_id, 'age', request.form['age'])
        db.hset(user_id, 'occupation', request.form['occupation'])
        db.hset(user_id, 'annual_income', request.form['annual_income'])
        db.hset(user_id, 'rent', request.form['rent'])
        db.hset(user_id, 'location', request.form['location'])
        db.hset(user_id, 'investment_goal', request.form['investment_goal'])
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

    return redirect(url_for('success', user_id=user_id))


def generate_prompt(user_id):
    """
    Generates a prompt message for a user based on the user's investment goal and personal financial information stored in a Redis database.

    Parameters:
    - user_id: a string representing the unique identifier of the user in the Redis database.

    Returns:
    - prompt: a string representing the generated prompt message for the user.
    """
    age = db.hget(user_id, 'age').decode()
    occupation = db.hget(user_id, 'occupation').decode()
    location = db.hget(user_id, 'location').decode()
    annual_income = int(db.hget(user_id, 'annual_income').decode())
    investment_goal = (db.hget(user_id, 'investment_goal').decode())
    goal_achieve_time = (db.hget(user_id, 'goal_achievement_time').decode())

    # Rent = (db.hget(user_id, 'rent').decode())
    # Food = (db.hget(user_id, 'food').decode())
    # Fitness = (db.hget(user_id, 'fitness').decode())
    # Travel = (db.hget(user_id, 'travel').decode())
    # Education = (db.hget(user_id, 'education').decode())
    # Entertainment = (db.hget(user_id, 'entertainment').decode())

    Rent = 3003
    Food = 1000
    Fitness = 567
    Travel = 80
    Education = 300
    Entertainment = 400



    investment_proportion = int(db.hget(user_id, 'investment_proportion').decode())
    risk_tolerance = db.hget(user_id, 'risk_tolerance').decode()
    investment_types = db.hget(user_id, 'investment_type').decode()

    # Check user's investment goal and compose prompt accordingly
    if investment_goal == 'house':
        house_price = float(db.hget(user_id, 'house_price').decode())
        house_settlement = int(db.hget(user_id, 'house_settlement').decode())
        house_loan_years = int(db.hget(user_id, 'house_loan_years').decode())
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to buy a {house_price} house in {location} with a {house_settlement}% settlement and {house_loan_years} years loan. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice?"
    elif investment_goal == 'car':
        car_price = float(db.hget(user_id, 'car_price').decode())
        car_settlement = int(db.hget(user_id, 'car_settlement').decode())
        car_loan_years = int(db.hget(user_id, 'car_loan_years').decode())
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to buy a {car_price} house in {location} with a {car_settlement}% settlement and {car_loan_years} years loan. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice?"
    elif investment_goal == 'retirement':
        retirement_year = db.hget(user_id, 'retirement_year').decode()
        retirement_month_income = db.hget(user_id, 'retirement_monthly_income').decode()
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to save money for retirement at the age of {retirement_year}. My estimated monthly income after retirement needs to be ${retirement_month_income}. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice?"
    

    elif investment_goal == 'college':
        saving_for_college = db.hget(user_id, 'total_savings').decode()
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to save money for attending college. my estimated total saving need to be ${saving_for_college}. I have {goal_achieve_time} years left to achieve my goal. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice?"
    
    return prompt

def get_result_from_GPT(user_id):
    """
    Generates text using the OpenAI Codex API given a user ID and our-defined prompt.

    Args:
        user_id (str): A string representing the user ID to generate text for.

    Returns:
        Tuple containing the generated text and a status code.

        - generated_text (str): A string representing the generated text.
        - status_code (int): An integer representing the status code.

    Raises:
        HTTPError: If the request to the OpenAI API fails.
    """
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

    # # using asynctasks to check the status of the tasks

    # # Call the task asynchronously
    # task = analyze_spending_income.delay(spending_data, income_data)

    # # Get the task ID to check its status later
    # task_id = task.id

    # # Retrieve the task status using the task ID
    # task_status = AsyncResult(task_id, app=app)

    # # Check if the task has been completed
    # if task_status.ready():
    #     # Get the result of the task
    #     result = task_status.result
    #     print("Task completed. Result:", result)
    # else:
    #     print("Task is still running or pending.")

    completions = result.get('choices', [])
    if completions:
        generated_text = completions[0]['text']
        return generated_text, 200
    else:
        return 'Unable to complete prompt', 500


@app.route('/success/<user_id>')
def success(user_id):
    # user_id = db.get('user_id')
    # if user_id:
    #     user_id = user_id.decode('utf-8')

    result = chat_gpt_result(user_id)

    return render_template('success.html', user_id=user_id, result = result)


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
