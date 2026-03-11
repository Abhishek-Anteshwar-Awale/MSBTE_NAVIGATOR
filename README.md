# MSBTE Navigator – AI-Based Question Answering System

## 📌 Project Description

MSBTE Navigator is an AI-powered question-answering system designed to help students quickly find information from MSBTE academic documents. The system allows users to ask questions in natural language and retrieves accurate answers from uploaded PDF documents.

The project uses Natural Language Processing (NLP), vector search, and machine learning techniques to process educational documents and provide meaningful responses.

---

## 🚀 Features

* Ask questions related to MSBTE documents
* AI-based answer generation
* PDF document processing
* Semantic search using vector embeddings
* Fast information retrieval from academic content
* Simple web interface for interaction

---

## 🛠️ Technologies Used

* Python
* Flask
* MySQL
* FAISS (Vector Database)
* FLAN-T5 (Hugging Face Transformer Model)
* HTML
* CSS
* JavaScript

---

## 📂 Project Structure

```
MSBTE-Navigator
│
├── app.py                # Main Flask application
├── templates             # HTML pages
├── static                # CSS and JavaScript files
├── database              # MySQL database scripts
├── pdfs                  # Uploaded MSBTE documents
├── vector_store          # FAISS embeddings
└── README.md
```

---

## ⚙️ How It Works

1. MSBTE PDF documents are uploaded into the system.
2. The text is extracted and converted into vector embeddings.
3. FAISS is used to store and search embeddings efficiently.
4. When a user asks a question, the system retrieves relevant content.
5. The FLAN-T5 model generates an accurate answer based on the retrieved data.

---

## 💻 Installation & Setup

1. Clone the repository

```
git clone https://github.com/Abhishek-Anteshwar-Awale/MSBTE_NAVIGATOR.git
```

2. Navigate to the project folder

```
cd MSBTE_NAVIGATOR
```

3. Install required libraries

```
pip install -r requirements.txt
```

4. Run the Flask application

```
python app.py
```

5. Open the browser and go to

```
http://127.0.0.1:5000/
```

---

## 📊 Use Case

This system helps students quickly access academic information without manually searching through large PDF documents. It improves learning efficiency by providing instant answers.

---

## 👨‍💻 Author

Abhishek Awale

Computer Engineering Student
Interested in AI, Data Analysis, and Software Development
