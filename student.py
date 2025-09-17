# student.py
from flask import Blueprint, render_template, request, session, redirect
from langchain_core.messages import HumanMessage
from backend import chatbot, retrive_all_threads, load_con
from utilities import generate_thread_id, add_thread

student_bp = Blueprint("student", __name__, template_folder="templates")

from flask import Response, stream_with_context

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

                # Streaming response generator
                def generate():
                    config = {"configurable": {"thread_id": session["thread_id"]}}
                    try:
                        for message_chunk, metadata in chatbot.stream(
                            {"messages": [HumanMessage(content=user_input)]},
                            config=config,
                            stream_mode="messages"
                        ):
                            yield f"data: {message_chunk.content}\n\n"
                    except Exception:
                        yield "data: Sorry, an error occurred while generating the response.\n\n"

                return Response(stream_with_context(generate()), mimetype="text/event-stream")
            else:
                return {"error": "No user input provided"}, 400
        else:
            # Handle form submission (fallback, though we'll use AJAX)
            user_input = request.form.get("user_input", "").strip()
            if user_input:
                # Store user message in session for UI rendering
                session["messages_history"].append({"role": "user", "content": user_input})

                config = {"configurable": {"thread_id": session["thread_id"]}}
                response = chatbot.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)

                assistant_text = ""
                try:
                    assistant_text = response["messages"][-1].content
                except Exception:
                    assistant = response if isinstance(response, str) else None
                    if isinstance(assistant, str):
                        assistant_text = assistant
                    else:
                        assistant_text = "Sorry, I couldn't generate a reply."

                session["messages_history"].append({"role": "assistant", "content": assistant_text})

    # Enhanced threads with names and sorting
    raw_threads = retrive_all_threads()
    enhanced_threads = []
    for th in raw_threads:
        messages = load_con(th)
        # Find first user message as thread name
        thread_name = None
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content"):
                thread_name = msg.get("content")
                break
        if not thread_name:
            thread_name = f"Thread {raw_threads.index(th) + 1}"
        enhanced_threads.append({"id": th, "name": thread_name})

    # Sort threads so current thread is on top
    current_thread = session.get("thread_id")
    enhanced_threads.sort(key=lambda x: 0 if x["id"] == current_thread else 1)

    return render_template("student_chat.html",
                           messages=session.get("messages_history", []),
                           threads=enhanced_threads,
                           current_thread=current_thread)

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
