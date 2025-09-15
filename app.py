from flask import Flask, render_template, request, redirect, session, jsonify
from backend import chatbot, retrive_all_threads, load_con, allowed_file, upload_to_qdrant
from langchain_core.messages import HumanMessage
import uuid
import os

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- Utility ----------------
def generate_thread_id():
    return str(uuid.uuid4())

def add_thread(thread_id):
    if "chat_threads" not in session:
        session["chat_threads"]=[]
    if thread_id not in session["chat_threads"]:
        session["chat_threads"].append(thread_id)

# ---------------- Routes ----------------
@app.route("/", methods=["GET","POST"])
def index():
    if request.method=="POST":
        role = request.form.get("role")
        session["role"]=role
        if role=="student":
            session["messages_history"]=[]
            session["thread_id"]=generate_thread_id()
            add_thread(session["thread_id"])
            return redirect("/student_chat")
        else:
            return redirect("/admin")
    return render_template("index.html")

# ---------------- Admin ----------------
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST":
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            chunks = upload_to_qdrant(filepath)
            return jsonify({"status":"success","message":f"{file.filename} uploaded with {chunks} chunks"})
        else:
            return jsonify({"status":"error","message":"Invalid file type"})
    return render_template("admin.html")

# ---------------- Student Chat ----------------
@app.route("/student_chat", methods=["GET","POST"])
def student_chat():
    if "thread_id" not in session:
        session["thread_id"]=generate_thread_id()
        add_thread(session["thread_id"])
    if "messages_history" not in session:
        session["messages_history"]=[]

    if request.method=="POST":
        user_input = request.form["user_input"]
        session["messages_history"].append({"role":"user","content":user_input})
        config = {"configurable":{"thread_id":session["thread_id"]}}
        response = chatbot.invoke({"messages":[HumanMessage(content=user_input)]}, config=config)
        session["messages_history"].append({"role":"assistant","content":response["messages"][0].content})

    threads = retrive_all_threads()
    return render_template("student_chat.html",
        messages=session["messages_history"],
        threads=threads,
        current_thread=session["thread_id"]
    )

# ---------------- Switch Thread ----------------
@app.route("/switch_thread/<thread_id>")
def switch_thread(thread_id):
    session["thread_id"]=thread_id
    session["messages_history"]=load_con(thread_id)
    add_thread(thread_id)
    return redirect("/student_chat")

# ---------------- Reset Chat ----------------
@app.route("/reset_chat")
def reset_chat():
    session["thread_id"]=generate_thread_id()
    session["messages_history"]=[]
    add_thread(session["thread_id"])
    return redirect("/student_chat")

if __name__=="__main__":
    app.run(debug=True)
