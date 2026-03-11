from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import timedelta
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
import mysql.connector as mycon
import os
import requests  # For Ollama API calls

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.permanent_session_lifetime = timedelta(days=7)

# Database Connection
mydb = mycon.connect(host="localhost", user="root", password="Admin@123", database="signup")
db_cur = mydb.cursor()

# Ollama API URL
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Load PDFs and setup QA system
try:
    pdf_directory = "C:\\Users\\Abhishek Awale\\Desktop\\kapil\\data"

    loader = PyPDFDirectoryLoader(pdf_directory)
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1024, chunk_overlap=20)
    texts = text_splitter.split_documents(documents)

    # Summarization
    summarizer_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    summarizer_model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
    summarizer_pipe = pipeline("summarization", model=summarizer_model, tokenizer=summarizer_tokenizer)

    summarized_texts = [
        summarizer_pipe(text.page_content, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
        if len(text.page_content) > 100 else text.page_content for text in texts
    ]

    # Create embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    db = FAISS.from_texts(summarized_texts, embeddings)

    # Load FLAN-T5 model
    tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
    model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        torch_dtype=torch.float32,
        device=0 if device == "cuda" else -1
    )
    llm = HuggingFacePipeline(pipeline=pipe)

    # Set up QA chain
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=db.as_retriever())
except Exception as e:
    print(f"Model loading failed: {str(e)}")
    raise

@app.route('/')
def home():
    clear = request.args.get('clear', 'false') == 'true'
    return render_template('login.html', clear_local_storage=clear)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    db_cur.execute("SELECT * FROM usersdata WHERE username=%s AND password=%s", (username, password))
    result = db_cur.fetchone()
    
    if result:
        session['username'] = username
        flash("Login Successful!", "success")
        return redirect(url_for('index'))
    else:
        flash("Invalid Username or Password!", "danger")
        return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))
        
        try:
            # Check if username already exists
            db_cur.execute("SELECT * FROM usersdata WHERE username=%s", (username,))
            if db_cur.fetchone():
                flash("Username already exists!", "danger")
                return redirect(url_for('signup'))
            
            # Insert new user
            db_cur.execute(
                "INSERT INTO usersdata (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            mydb.commit()
            flash("Signup successful! You can now log in.", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Database Error: {e}", "danger")
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('index.html', username=session['username'])

@app.route('/ask', methods=['POST'])
def ask():
    if 'username' not in session:
        return jsonify({"answer": "Please log in to use the chatbot.", "status": "error"})
    
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Please enter a valid question.", "status": "error"})
    
    try:
        # First try to get answer from PDF knowledge base
        pdf_answer = qa.run(question)
        
        # If the answer is too short or seems incomplete, augment with Mistral
        if len(pdf_answer.split()) < 15 or "I don't know" in pdf_answer.lower():
            # Get broader context from Mistral
            mistral_response = requests.post(
                OLLAMA_URL,
                json={
                    "model": "mistral",
                    "prompt": f"Based on this information: '{pdf_answer}'. Can you provide more context about: {question}",
                    "stream": False
                }
            )
            
            if mistral_response.status_code == 200:
                mistral_data = mistral_response.json()
                augmented_answer = f"{pdf_answer}\n\nAdditional context:\n{mistral_data.get('response', '')}"
                return jsonify({
                    "answer": augmented_answer, 
                    "status": "success"
                })
        
        return jsonify({
            "answer": pdf_answer, 
            "status": "success"
        })
    except Exception as e:
        # If PDF processing fails, fall back to Mistral
        try:
            mistral_response = requests.post(
                OLLAMA_URL,
                json={
                    "model": "mistral",
                    "prompt": question,
                    "stream": False
                }
            )
            
            if mistral_response.status_code == 200:
                mistral_data = mistral_response.json()
                return jsonify({
                    "answer": mistral_data.get('response', 'I couldn\'t process your request.'), 
                    "status": "success"
                })
            return jsonify({
                "answer": f"Sorry, an error occurred: {str(e)}", 
                "status": "error"
            })
        except Exception as mistral_error:
            return jsonify({
                "answer": f"Sorry, both systems failed to process your request: {str(mistral_error)}", 
                "status": "error"
            })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home', clear='true'))

if __name__ == '__main__':
    app.run(debug=True)