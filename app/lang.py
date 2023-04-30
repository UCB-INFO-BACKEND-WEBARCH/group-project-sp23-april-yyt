"""
Utilities to interact with a CSV via Lagnchain API
"""

# Imports 
import os 
import pandas as pd
from langchain.llms import OpenAI
from langchain.agents import create_pandas_dataframe_agent

# Setup the OpenAI Key <- this is my personal account soo  ya
os.environ["OPENAI_API_KEY"] = "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"

def create_agent(path: str): 

    """
    Loads in a CSV and creates a Langchain Agent to interact via Pandas 
    Args: 
        - path (str): file path to CSV
    Returns: 
        - agent: the Langchain pandas agent
    """

    # Load data 
    df = pd.read_csv(path)

    # Connect to OpenAI
    model = OpenAI( temperature = 0 )

    # Create agent
    agent = create_pandas_dataframe_agent(llm = model, df = df)

    return agent

# # Create agent
# agent = create_agent(path = "app/static/checking_data.csv")

# # Ask sample question
# question = """
# What is the sum of food expenses in the table?
# """
# answer = agent.run(question)
# print(answer)

from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain

loader = PyPDFLoader("app/static/bank_statement.pdf")
documents = loader.load()

chain = load_qa_chain(llm = OpenAI(), chain_type="map_reduce")
query = "What was the total rent expense from the statement?"
answer = chain.run(input_documents = documents, question = query)

print('\n\n\nQuestion: ', query)
print('\n\nAnswer:', answer)
