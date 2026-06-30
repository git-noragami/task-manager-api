import os
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from models import db, User, Task

# Load environment configuration variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///task_manager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-fallback-key')

# Bind extensions to app lifecycle context
db.init_app(app)
jwt = JWTManager(app)

# Initialize database schema arrays tables automatically if missing
with app.app_context():
    db.create_all()

# --- AUTHENTICATION ENDPOINTS ---

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Missing username or password fields"}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists standard choice"}), 400

    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully code sequence"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(username=data.get('username')).first()
    
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({"error": "Invalid client credentials supplied"}), 401
        
    access_token = create_access_token(identity=str(user.id))
    return jsonify({"token": access_token}), 200

# --- SECURE CRUD TASK ENDPOINTS ---

@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user_id = get_jwt_identity()
    query = Task.query.filter_by(user_id=current_user_id)
    
    # Apply optional filter query params parameters if specified by user
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
        
    tasks = query.all()
    return jsonify([task.to_dict() for task in tasks]), 200

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task_by_id(task_id):
    current_user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user_id).first_or_404(description="Task not found or unauthorized access")
    return jsonify(task.to_dict()), 200

@app.route('/api/tasks', methods=['POST'])
@jwt_required()
def create_task():
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    if not data.get('title'):
        return jsonify({"error": "Title field is mandatory required"}), 400
        
    new_task = Task(
        title=data['title'],
        description=data.get('description'),
        category=data.get('category', 'General'),
        status=data.get('status', 'pending'),
        user_id=current_user_id
    )
    
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    current_user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user_id).first_or_404(description="Task not found or unauthorized access")
    data = request.get_json() or {}
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'category' in data:
        task.category = data['category']
    if 'status' in data:
        task.status = data['status']
        
    db.session.commit()
    return jsonify(task.to_dict()), 200

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    current_user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user_id).first_or_404(description="Task not found or unauthorized access")
    
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": f"Task {task_id} deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
