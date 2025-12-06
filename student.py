from flask import Blueprint, render_template, request, session, redirect, abort, Response, stream_with_context
from flask_login import login_required, current_user
from langchain_core.messages import HumanMessage
from backend import chatbot, load_con
from utilities import generate_thread_id
from db import create_thread_entry, get_user_threads, get_thread_owner, update_thread_name

student_bp = Blueprint("student", __name__, template_folder="templates")

@student_bp.route("/student_chat", methods=["GET", "POST"])
@login_required
def student_chat():
    # Ensure thread initialization
    if "thread_id" not in session:
        new_thread_id = generate_thread_id()
        session["thread_id"] = new_thread_id
        create_thread_entry(current_user.id, new_thread_id, "New Chat")
    
    # Verify thread ownership (security check)
    current_thread_id = session["thread_id"]
    owner_id = get_thread_owner(current_thread_id)
    
    # If thread doesn't exist in DB (maybe from old session) or belongs to another user
    if not owner_id or owner_id != current_user.id:
        # Create a new one
        new_thread_id = generate_thread_id()
        session["thread_id"] = new_thread_id
        create_thread_entry(current_user.id, new_thread_id, "New Chat")
        current_thread_id = new_thread_id

    # Always load history from backend to ensure persistence across logins
    session["messages_history"] = load_con(current_thread_id)

    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            user_input = data.get("user_input", "").strip()
            if user_input:
                # Update thread name if it's the first message (or generic name)
                # We can check if history is empty
                if not session.get("messages_history"):
                     update_thread_name(current_thread_id, user_input[:30] + "..." if len(user_input) > 30 else user_input)

                # Streaming response generator
                def generate():
                    config = {"configurable": {"thread_id": current_thread_id}}
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

    # Load user threads from DB
    db_threads = get_user_threads(current_user.id)
    enhanced_threads = []
    for th in db_threads:
        enhanced_threads.append({
            "id": th["thread_id"],
            "name": th["name"] or "New Chat"
        })

    return render_template("student_chat.html",
                           messages=session.get("messages_history", []),
                           threads=enhanced_threads,
                           current_thread=current_thread_id)

@student_bp.route("/switch_thread/<thread_id>")
@login_required
def switch_thread(thread_id):
    # Verify ownership
    owner_id = get_thread_owner(thread_id)
    if not owner_id or owner_id != current_user.id:
        return abort(403)

    session["thread_id"] = thread_id
    # History will be loaded in student_chat
    return redirect("/student_chat")

@student_bp.route("/reset_chat")
@login_required
def reset_chat():
    new_thread_id = generate_thread_id()
    session["thread_id"] = new_thread_id
    create_thread_entry(current_user.id, new_thread_id, "New Chat")
    return redirect("/student_chat")
