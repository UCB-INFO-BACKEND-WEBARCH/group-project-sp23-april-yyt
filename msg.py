from flask import Flask, request, jsonify
import redis
# from pdfminer.high_level import extract_text
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)
engine = create_engine('postgresql://user:password@db:5432/mydatabase')
Session = sessionmaker(bind=engine)
Base = declarative_base()

# class Transaction(Base):
#     __tablename__ = 'transactions'
#     id = Column(Integer, primary_key=True)
#     date = Column(String)
#     amount = Column(Integer)
#     description = Column(String)

#     def __repr__(self):
#         return f"<Transaction(date='{self.date}', amount='{self.amount}', description='{self.description}')>"

class UserInput(Base):
    __tablename__ = 'user_inputs'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    question = Column(String)
    answer = Column(String)

    def __repr__(self):
        return f"<UserInput(user_id='{self.user_id}', question='{self.question}', answer='{self.answer}')>"

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    user_id = str(uuid.uuid4())
    r.hset(user_id, 'data', file.read())
    return jsonify({'user_id': user_id})

# @app.route('/process', methods=['GET'])
# def process():
#     files = r.keys()
#     for file in files:
#         data = r.hget(file, 'data')
#         text = extract_text(data)
#         transactions = parse_text(text)
#         save_to_db(transactions)
#     return 'Processing complete'

@app.route('/questions', methods=['GET', 'POST'])
def questions():
    if request.method == 'POST':
        user_id = request.form['user_id']
        question = request.form['question']
        answer = request.form['answer']
        ui = UserInput(user_id=user_id, question=question, answer=answer)
        session = Session()
        session.add(ui)
        session.commit()
        return 'Question and answer saved successfully'
    else:
        user_id = request.args.get('user_id')
        session = Session()
        questions = session.query(UserInput.question).filter_by(user_id=user_id).distinct().all()
        return jsonify([q[0] for q in questions])

# def parse_text(text):
#     transactions = []
#     # TODO: Parse text to extract transaction data
#     return transactions

# def save_to_db(transactions):
#     session = Session()
#     for transaction in transactions:
#         t = Transaction(date=transaction.date, amount=transaction.amount, description=transaction.description)
#         session.add(t)
#     session.commit()

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True, host='0.0.0.0', port=5000)