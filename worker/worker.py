import os
from celery import Celery
# from tasks import get_monthly_expenses

broker_url = os.environ.get("CELERY_BROKER_URL"),
res_backend = os.environ.get("CELERY_RESULT_BACKEND")

celery_app = Celery(name='worker',
                    broker=broker_url,
                    result_backend=res_backend)


# tasks.py

import pandas as pd
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
import requests
from flask import render_template, request, redirect, url_for, Flask, jsonify
from app import app
import redis
import os
import openai
from dotenv import load_dotenv
# import parse_df

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


@celery_app.task(bind=True)
def check_parsing_status(self, df):
    return get_monthly_expenses(df)