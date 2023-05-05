import os
from celery import Celery
import redis
import openai
import pandas as pd
import re
from io import StringIO, BytesIO
broker_url = os.environ.get("CELERY_BROKER_URL"),
res_backend = os.environ.get("CELERY_RESULT_BACKEND")
openai.api_key = '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'
celery_app = Celery(name='task',
                    broker=broker_url,
                    result_backend=res_backend)
@celery_app.task
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
    
    prompt = generate_prompt(user_id)
    # Run query on gpt-3.5-turb 
    result = openai.ChatCompletion.create(model = 'gpt-3.5-turbo',
                                          messages = [
                                            {"role": "user", "content": prompt},
                                          ],
                                          temperature = 0)
    
    # Convert the string of lists to list 
    result = result['choices'][0]['message']['content']
    db = redis.Redis(host='localhost', port=6379, db=0)
    db.hset(user_id, "advice_text", result)
    if result:
        return result, 200
    else:
        return 'Unable to complete prompt', 500
    
def generate_prompt(user_id):
    """
    Generates a prompt message for a user based on the user's investment goal and personal financial information stored in a Redis database.

    Parameters:
    - user_id: a string representing the unique identifier of the user in the Redis database.

    Returns:
    - prompt: a string representing the generated prompt message for the user.
    """
    db = redis.Redis(host='localhost', port=6379, db=0)
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
    with open('app/static/prompt_template.txt', 'r') as file:
        template = file.read()
    # Check user's investment goal and compose prompt accordingly
    if investment_goal == 'house':
        house_price = float(db.hget(user_id, 'house_price').decode())
        house_settlement = int(db.hget(user_id, 'house_settlement').decode())
        house_loan_years = int(db.hget(user_id, 'house_loan_years').decode())
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to buy a {house_price} house in {location} with a {house_settlement}% settlement and {house_loan_years} years loan. I am to buy the house in {goal_achieve_time} years. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice"
        
    elif investment_goal == 'car':
        car_price = float(db.hget(user_id, 'car_price').decode())
        car_settlement = int(db.hget(user_id, 'car_settlement').decode())
        car_loan_years = int(db.hget(user_id, 'car_loan_years').decode())
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to buy a {car_price} car in {location} with a {car_settlement}% settlement and {car_loan_years} years loan.  I am to buy the car in {goal_achieve_time} years. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice"
    elif investment_goal == 'retirement':
        retirement_year = db.hget(user_id, 'retirement_year').decode()
        retirement_month_income = db.hget(user_id, 'retirement_monthly_income').decode()
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to save money for retirement at the age of {retirement_year}. My estimated monthly income after retirement needs to be ${retirement_month_income}. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice"
    

    elif investment_goal == 'college':
        saving_for_college = db.hget(user_id, 'total_savings').decode()
        prompt = f"Currently, I am a {age}-year new graduate working as a {occupation} living in {location} earning a {annual_income} annual income. I am spending {Rent} on rent and utilities, {Food} on food & groceries, {Fitness} on fitness and health, {Travel} on travel, {Education} on education, and {Entertainment} on entertainment each month. My saving goal is to save money for attending college. my estimated total saving need to be ${saving_for_college}. I have {goal_achieve_time} years left to achieve my goal. I want to invest {investment_proportion}% of my income, and my risk tolerance is {risk_tolerance}. I have my preferred investment types as {', '.join(investment_types)}. Can you give me personal financial investment advice"
    
    return prompt + "the same format as this: " + template 

@celery_app.task
def get_expense_data(user_id):
    # Extract monthly expenses
    db = redis.Redis(host='localhost', port=6379, db=0)
    df, prompts = load_and_clean_csv(user_id)   
    monthly_expenses = get_monthly_expenses(df)
    
    # Insert to redis DB
    expense_types = ['food', 'fitness', 'travel', 'education', 'entertainment']
    for expense_type in expense_types: 
        val = monthly_expenses.get(expense_type)
        db.hset(user_id, expense_type, val)


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

def load_and_clean_csv(user_id): 
    
    """
    Loads a CSV and tries to remove information not about the vendor
    Params: 
        - path (str): the path to a csv file 
    Returns: 
        - df (pd.DataFrame): the cleaned pandas df
        - prompt (str): the completed prompt template
    """
    db = redis.Redis(host='localhost', port=6379, db=0)
    # Parse the CSV file
    csv_data = db.get(user_id, 'uploaded_csv')
    try:
        csv_string = StringIO(csv_data)
    except:
        csv_string = BytesIO(csv_data)
    df = pd.read_csv(csv_string)[['Date', 'Amount', 'Expense']]

    
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
