Project is a Flask-based chatbot application for college-related queries.
Admin interface allows uploading documents (pdf, docx, txt) which are processed and stored in a Qdrant vector database.
Student interface provides a chat UI with multi-thread support, interacting with a chatbot powered by Google Gemini API and LangGraph.
The chatbot retrieves relevant context from uploaded documents to answer queries.
Technologies used: Flask, LangChain, LangGraph, Google Gemini, Qdrant, Sentence Transformers, SQLite.
The project architecture includes separate blueprints for admin and student, a backend managing chat state and model interaction, and utilities for file processing and vector database interaction.




The project is a Flask-based AI chatbot application designed for college-related queries, developed for the SIH hackathon. It features two main user roles: Admin and Student.

Project Overview:
The Admin interface allows uploading documents (PDF, DOCX, TXT) which are processed and stored in a Qdrant vector database for semantic search.
The Student interface provides a chat UI where students can interact with the chatbot, which uses Google Gemini API and LangGraph to generate responses.
The chatbot retrieves relevant context from the uploaded documents to answer college-related questions accurately.
The system supports multiple chat threads per student session.
Architecture:
Flask web app with blueprints for admin and student routes.
Backend manages chat state, message history, and interaction with the generative AI model.
Utilities handle file processing, text extraction, chunking, embedding, and Qdrant vector database operations.
SQLite is used for chat state persistence.
Technologies Used:
Python, Flask, LangChain, LangGraph, Google Gemini API, Qdrant, Sentence Transformers, SQLite, Tailwind CSS for frontend styling.
User Interface:
Role selection page for Admin or Student.
Admin page for uploading documents.
Student chat page with multi-thread support and streaming AI responses.