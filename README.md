## Project Proposal - Group 3
#### Team Name: FinGuru - Personal Finance Assistant API
#### Members: Bennett Colin, Yuwei Quan, Yixuan Tao, Yutong Yang


### I. Project Idea
Create a personal finance assistant API that provides users with personalized financial advice and budgeting tools based on their income, expenses, and investment goals. The API will integrate with popular shopping apps like Amazon to allow users to track their spending and set budget limits. 
The backend infrastructure will be built using Python Flask, ensuring a lightweight and scalable framework for seamless API integration. Docker will be employed to containerize the application, allowing for easy deployment and management across various environments. To handle time-consuming tasks efficiently, we will utilize asynchronous task queues with Celery, enabling the processing of multiple user requests concurrently without hindering the application's performance. 


### II. What APIs We Plan to Use
#### - ChatGPT API
Using ChatGPT API, we plan to generate financial advice indluding:
- Budgeting advice: Based on a user's income and expenses, suggest a budget and provide tools for tracking spending.
- Investment advice: Based on a user's risk tolerance and investment goals, suggest specific investments and asset allocations.
- Tax advice: Based on a user's income and expenses, suggest tax-saving strategies and help with tax preparation.
- Debt management advice: Based on a user's debt load, suggest strategies for paying off debt more quickly and efficiently.
- Retirement planning advice: Based on a user's age and retirement goals, suggest specific retirement savings goals and investment strategies.

#### - Amazon API
We plan to make a budgeting function for users. By integrating with Amazon's API, we allow users to track their spending on Amazon and set budget limits for their purchases.


### USAGE
Install the required dependencies:
`pip install -r requirements.txt`


Start redis:
`redis-server`


To run the celery application:
`cd worker`

`celery -A task worker --loglevel=info`


To run the flask application:
`cd app`

`export FLASK_APP=app.py`

`export FLASK_ENV=development`

`flask run`

