## Project Proposal - Group 3
#### Team Name: FinGuru - Personal Finance Assistant API
#### Members: April Yang, Bennett Cohen, Yuwei Quan, Yixuan Tao


### I. Project Idea
Create a personal finance assistant that provides users with personalized financial advice and budgeting tools based on their income, expenses, and investment goals. We used ChatGPT API to get smart financial advice based on analysis of user's financial data and expense history.
The backend infrastructure is built using Python Flask, ensuring a lightweight and scalable framework for seamless API integration. Docker will be employed to containerize the application, allowing for easy deployment and management across various environments. To handle time-consuming tasks efficiently, we will utilize asynchronous task queues with Celery, enabling the processing of multiple user requests concurrently without hindering the application's performance, also enabling users to check the status of the tasks. 


### II. What APIs We Plan to Use
#### - ChatGPT API
Using ChatGPT API, we plan to generate financial advice indluding:
- Budgeting advice: Based on a user's income and expenses, suggest a budget and provide tools for tracking spending.
- Investment advice: Based on a user's risk tolerance and investment goals, suggest specific investments and asset allocations.
- Tax advice: Based on a user's income and expenses, suggest tax-saving strategies and help with tax preparation.
- Debt management advice: Based on a user's debt load, suggest strategies for paying off debt more quickly and efficiently.
- Retirement planning advice: Based on a user's age and retirement goals, suggest specific retirement savings goals and investment strategies.


### USAGE
Install the required dependencies:
`pip install -r requirements.txt`


Start redis:
`redis-server`


Run the celery application:
`cd worker`

`celery -A task worker --loglevel=info`


Run the flask application:
`cd app`

`export FLASK_APP=app.py`

`export FLASK_ENV=development`

`flask run`

