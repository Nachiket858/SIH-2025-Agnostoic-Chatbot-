# student.py
from flask import Blueprint, render_template, request, session, redirect
from langchain_core.messages import HumanMessage
from backend import chatbot, retrive_all_threads, load_con
from utilities import generate_thread_id, add_thread

student_bp = Blueprint("student", __name__, template_folder="templates")

@student_bp.route("/student_chat", methods=["GET", "POST"])
def student_chat():
    # Ensure thread/session initialization
    if "thread_id" not in session:
        session["thread_id"] = generate_thread_id()
        add_thread(session["thread_id"])

    if "messages_history" not in session:
        session["messages_history"] = []

    if request.method == "POST":
        if request.is_json:
            # Handle AJAX request
            data = request.get_json()
            user_input = data.get("user_input", "").strip()
            if user_input:
                # Store user message in session for UI rendering
                session["messages_history"].append({"role": "user", "content": user_input})

                # Invoke the LangGraph chatbot, passing thread_id so conversation history is preserved
                config = {"configurable": {"thread_id": session["thread_id"]}}
                # We pass the message as a HumanMessage (same pattern as your original working code)
                response = chatbot.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)

                # LangGraph compiled chatbot returns a dict with "messages": [<BaseMessage>...]
                # Guard: extract assistant text safely
                assistant_text = ""
                try:
                    # expected form: response["messages"][-1].content
                    assistant_text = response["messages"][-1].content
                except Exception:
                    # Fallback if response shape differs
                    assistant = response if isinstance(response, str) else None
                    if isinstance(assistant, str):
                        assistant_text = assistant
                    else:
                        assistant_text = "Sorry, I couldn't generate a reply."

                session["messages_history"].append({"role": "assistant", "content": assistant_text})

                return {"assistant": assistant_text}
            else:
                return {"error": "No user input provided"}, 400
        else:
            # Handle form submission (fallback, though we'll use AJAX)
            user_input = request.form.get("user_input", "").strip()
            if user_input:
                # Store user message in session for UI rendering
                session["messages_history"].append({"role": "user", "content": user_input})

                # Invoke the LangGraph chatbot, passing thread_id so conversation history is preserved
                config = {"configurable": {"thread_id": session["thread_id"]}}
                # We pass the message as a HumanMessage (same pattern as your original working code)
                response = chatbot.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)

                # LangGraph compiled chatbot returns a dict with "messages": [<BaseMessage>...]
                # Guard: extract assistant text safely
                assistant_text = ""
                try:
                    # expected form: response["messages"][-1].content
                    assistant_text = response["messages"][-1].content
                except Exception:
                    # Fallback if response shape differs
                    assistant = response if isinstance(response, str) else None
                    if isinstance(assistant, str):
                        assistant_text = assistant
                    else:
                        assistant_text = "Sorry, I couldn't generate a reply."

                session["messages_history"].append({"role": "assistant", "content": assistant_text})

    threads = retrive_all_threads()
    return render_template("student_chat.html",
                           messages=session.get("messages_history", []),
                           threads=threads,
                           current_thread=session.get("thread_id"))

@student_bp.route("/switch_thread/<thread_id>")
def switch_thread(thread_id):
    # Load messages from the persistent store for the given thread
    session["thread_id"] = thread_id
    session["messages_history"] = load_con(thread_id)
    add_thread(thread_id)
    return redirect("/student_chat")

@student_bp.route("/reset_chat")
def reset_chat():
    session["thread_id"] = generate_thread_id()
    session["messages_history"] = []
    add_thread(session["thread_id"])
    return redirect("/student_chat")
