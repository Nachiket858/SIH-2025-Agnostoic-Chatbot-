# College Query Assistant - AI Chatbot

A Flask-based intelligent chatbot application designed to help university students get instant answers to college-related queries using RAG (Retrieval-Augmented Generation) powered by Google's Gemini AI and Qdrant vector database.

## 🎯 Project Overview

This application provides a dual-interface system where:
- **Admins** can upload knowledge base documents (PDF, DOCX, TXT)
- **Students** can chat with an AI assistant that provides accurate answers based on the uploaded documents

The chatbot uses LangGraph for conversation management and maintains persistent chat history for each user.

## ✨ Key Features

### Authentication & Authorization
- **Secure Login System** using Flask-Login
- **Password Hashing** with Werkzeug's scrypt method
- **Role-Based Access Control** (Admin vs Student)
- **Auto-created Default Admin** account on first run
- **User-Isolated Sessions** - each student only sees their own chats

### Admin Features
- Upload knowledge base documents (PDF, DOCX, TXT)
- View list of all uploaded documents
- Logout functionality

### Student Features
- Chat with AI assistant powered by Google Gemini
- **Persistent Chat History** - conversations saved across sessions
- **Thread Management** - create new chats, switch between conversations
- **Real-time Streaming Responses** using Server-Sent Events (SSE)
- User-specific chat isolation (can't see other students' chats)

### AI & Knowledge Base
- **RAG Architecture** - Retrieval-Augmented Generation
- **Vector Search** using Qdrant cloud database
- **Semantic Embeddings** with sentence-transformers (all-MiniLM-L6-v2)
- **Context-Aware Responses** using LangGraph state management
- **Document Processing** - automatic text extraction and chunking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Flask Application                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Auth BP    │  │   Admin BP   │  │  Student BP  │ │
│  │  (Login/     │  │  (Upload     │  │  (Chat       │ │
│  │   Register)  │  │   Docs)      │  │   Interface) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   SQLite     │  │   Qdrant     │  │  LangGraph   │ │
│  │  (Users &    │  │  (Vector     │  │  (Chat       │ │
│  │   Threads)   │  │   Store)     │  │   State)     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    AI Services                           │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────────────────────────┐│
│  │   Gemini AI  │  │  Sentence Transformers (Embedder)││
│  │  (Response   │  │  (all-MiniLM-L6-v2)              ││
│  │  Generation) │  │                                  ││
│  └──────────────┘  └──────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
SIH-2025-Agnostoic-Chatbot/
├── app.py                 # Main Flask application
├── auth.py                # Authentication routes
├── admin.py               # Admin panel routes
├── student.py             # Student chat routes
├── backend.py             # LangGraph chatbot logic
├── db.py                  # Database models and helpers
├── utilities.py           # Qdrant & file processing utilities
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys)
├── templates/             # Jinja2 HTML templates
│   ├── login.html
│   ├── register.html
│   ├── admin.html
│   └── student_chat.html
└── uploads/               # Uploaded documents storage
```

## 🔧 Technical Stack

### Backend
- **Flask** 3.1.2 - Web framework
- **Flask-Login** 0.6.3 - User session management
- **LangChain** 1.1.2 - LLM orchestration
- **LangGraph** 1.0.4 - Conversation state management
- **langchain-google-genai** 3.2.0 - Gemini AI integration

### AI & ML
- **Google Gemini 2.0 Flash** - LLM for response generation
- **sentence-transformers** 5.1.2 - Text embeddings
- **Qdrant** 1.16.1 - Vector database (cloud)

### Document Processing
- **pypdf** 6.4.0 - PDF text extraction
- **python-docx** 1.2.0 - DOCX processing

### Database
- **SQLite** - User authentication & thread management
- **aiosqlite** 0.21.0 - Async SQLite for LangGraph

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd SIH-2025-Agnostoic-Chatbot-
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
FLASK_SECRET_KEY=your-super-secret-key-change-this-in-production
```

**Getting API Keys:**
- **Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Qdrant**: Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)

### Step 5: Run the Application
```bash
python app.py
```

The application will be available at: `http://127.0.0.1:5000`

## 👤 Default Admin Credentials

The system automatically creates a default admin account on first run:

- **Email**: `admin@college.edu`
- **Password**: `admin123`

⚠️ **Important**: Change this password in production!

## 🚀 Usage Guide

### For Admins

1. **Login** with admin credentials
2. **Upload Documents** - Add PDF/DOCX/TXT files containing college information
3. **View Documents** - See list of all uploaded files
4. **Logout** when done

### For Students

1. **Register** a new account (automatically assigned Student role)
2. **Login** with your credentials
3. **Chat** with the AI assistant:
   - Type questions about college (exams, fees, schedules, etc.)
   - Get instant AI-powered answers based on uploaded documents
   - Use quick query buttons for common questions
4. **Manage Chats**:
   - Create new chat threads
   - Switch between previous conversations
   - All chat history is saved and persistent

## 🔒 Security Features

- ✅ Password hashing using scrypt algorithm
- ✅ Session-based authentication
- ✅ Role-based access control
- ✅ User-isolated data (students can't access each other's chats)
- ✅ Environment variable for sensitive credentials
- ✅ CSRF protection (Flask default)

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student'
)
```

### Threads Table
```sql
CREATE TABLE threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    thread_id TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
```

## 📊 How It Works

### Document Upload Flow
1. Admin uploads document (PDF/DOCX/TXT)
2. Text is extracted from the document
3. Text is split into chunks (500 chars with 50 char overlap)
4. Each chunk is embedded using sentence-transformers
5. Embeddings are stored in Qdrant vector database

### Chat Flow
1. Student sends a message
2. Message is embedded using the same model
3. Qdrant performs semantic search to find relevant chunks
4. Relevant chunks are used as context for Gemini AI
5. Gemini generates a response based on the context
6. Response is streamed back to the user
7. Conversation is saved in LangGraph state (SQLite)

## 🛠️ Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError`
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Issue**: Database errors
**Solution**: Delete `users.db` and `chatbot.db` to reset

**Issue**: Qdrant connection errors
**Solution**: Verify your Qdrant URL and API key in `.env`

**Issue**: Gemini API errors
**Solution**: Check your API key and quota at Google AI Studio

## 📝 Development Notes

- The app uses **Flask debug mode** by default (for development)
- Chat state is managed using **LangGraph checkpointers**
- File uploads are stored in the `uploads/` directory
- Streaming responses use **Server-Sent Events** (SSE)

## 🎓 Use Cases

Perfect for:
- University information desks
- Student support systems
- Academic query handling
- Course information distribution
- Campus facility information
- Exam and schedule queries

## 🤝 Contributing

This project was developed for SIH 2025. Contributions are welcome!

## 📄 License

This project is created for educational purposes.

## 🙏 Acknowledgments

- Built with Google Gemini AI
- Powered by LangChain & LangGraph
- Vector search by Qdrant
- Embeddings by Sentence Transformers

---

**Last Updated**: December 2025  
**Version**: 1.0.0
