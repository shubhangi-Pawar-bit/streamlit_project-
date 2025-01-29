import streamlit as st
from bson.objectid import ObjectId
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import re
from collections import Counter
import numpy as np
from textwrap import dedent

# Move set_page_config to the top level
st.set_page_config(layout="wide", page_title="Advanced Code Analysis Dashboard")

# Custom CSS for better styling
st.markdown("""
    <style>
    .stMetric .label { font-size: 1.2rem !important; }
    .stMetric .value { font-size: 2rem !important; }
    .student-card { 
        padding: 1rem; 
        border-radius: 0.5rem; 
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def admin_dashboard(db):
    st.title("Admin Overview")
    st.write("Welcome to the Admin Dashboard")
    
    total_questions = db.questions.count_documents({})
    questions = db.questions.find()
    
    class_question_dict = {}
    for question in questions:
        if 'class_name' in question and 'question_name' in question:
            class_question_dict[question['class_name']] = question['question_name']

    username = "abhishelke297127"
    password = "Abhi%402971"
    connection_string = f"mongodb+srv://{username}:{password}@cluster0.uu8yq.mongodb.net/?retryWrites=true&w=majority"
    
    client = MongoClient(connection_string)
    db = client["JavaFileAnalysis"]
    
    total_students = len(db.list_collection_names())
    
    # Enhanced metrics with better visualization
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Students", total_students)
    with col2:
        st.metric("📝 Total Questions", total_questions)
    with col3:
        avg_submissions = total_questions/max(total_students, 1)
        st.metric("📊 Average Questions/Student", f"{avg_submissions:.2f}")
    with col4:
        active_students = sum(1 for c in db.list_collection_names() if db[c].count_documents({}) > 0)
        st.metric("🎯 Active Students", active_students)
def manage_questions(db):
    st.header("Manage Questions")
    
    questions_collection = db.questions
    
    # Create tabs for better organization
    tab1, tab2 = st.tabs(["➕ Add Questions", "📋 View Questions"])
    
    with tab1:
        with st.form(key="send_question_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                question_name = st.text_input("Question Name 📝")
            with col2:
                class_name = st.text_input("Class Name 📚")
            
            st.markdown("---")
            submit_button = st.form_submit_button("Send Question ✉️", use_container_width=True)

            if submit_button:
                if question_name and class_name:
                    existing_question = questions_collection.find_one({
                        "class_name": class_name
                    })

                    if existing_question:
                        st.error(f"⚠️ The class '{class_name}' already has a question assigned.")
                    else:
                        try:
                            new_question = {
                                "question_name": question_name, 
                                "class_name": class_name,
                                "created_at": datetime.now()
                            }
                            questions_collection.insert_one(new_question)
                            st.success("✅ Question sent successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                else:
                    st.warning("⚠️ Please fill in both fields.")
    
    with tab2:
        questions = list(questions_collection.find())
        
        if questions:
            for question in questions:
                with st.container():
                    st.markdown("""
                        <div style='
                            padding: 1rem;
                            border-radius: 0.5rem;
                            border: 1px solid #e0e0e0;
                            margin: 0.5rem 0;
                            background-color: #f8f9fa;
                        '>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col1:
                        st.markdown(f"""
                            **Question:** {question['question_name']}  
                            **Class:** {question['class_name']}  
                            **Created:** {question.get('created_at', 'Unknown date')}
                        """)
                    with col2:
                        if st.button("✏️", key=f"edit_{question['_id']}"):
                            st.session_state[f"editing_{question['_id']}"] = True
                    with col3:
                        if st.button("🗑️", key=f"delete_{question['_id']}"):
                            try:
                                questions_collection.delete_one({"_id": ObjectId(question["_id"])})
                                st.success("✅ Question deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")

                    if st.session_state.get(f"editing_{question['_id']}", False):
                        edit_question(db, question)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("📝 No questions available.")


def analyze_code_complexity(code):
    """Analyze code complexity metrics."""
    # Count nested loops and conditionals
    nested_depth = 0
    max_nested_depth = 0
    loops = len(re.findall(r'\b(for|while)\b', code))
    conditionals = len(re.findall(r'\b(if|else|switch)\b', code))
    
    # Count method definitions
    methods = len(re.findall(r'\b(public|private|protected)?\s+\w+\s+\w+\s*\([^)]*\)\s*\{', code))
    
    # Basic cyclomatic complexity (very simplified)
    complexity = loops + conditionals + 1
    
    return {
        'loops': loops,
        'conditionals': conditionals,
        'methods': methods,
        'complexity': complexity
    }

def generate_code_summary(code):
    """Generate a summary of the code structure."""
    # Identify class names
    class_matches = re.findall(r'class\s+(\w+)', code)
    # Identify method names
    method_matches = re.findall(r'(?:public|private|protected)?\s+\w+\s+(\w+)\s*\([^)]*\)', code)
    # Identify imports
    import_matches = re.findall(r'import\s+([^;]+);', code)
    
    return {
        'classes': class_matches,
        'methods': method_matches,
        'imports': import_matches
    }

def analyze_code_complexity(code):
    """Analyze code complexity metrics."""
    # Count nested loops and conditionals
    nested_depth = 0
    max_nested_depth = 0
    loops = len(re.findall(r'\b(for|while)\b', code))
    conditionals = len(re.findall(r'\b(if|else|switch)\b', code))
    
    # Count method definitions
    methods = len(re.findall(r'\b(public|private|protected)?\s+\w+\s+\w+\s*\([^)]*\)\s*\{', code))
    
    # Basic cyclomatic complexity (very simplified)
    complexity = loops + conditionals + 1
    
    return {
        'loops': loops,
        'conditionals': conditionals,
        'methods': methods,
        'complexity': complexity
    }

def generate_code_summary(code):
    """Generate a summary of the code structure."""
    # Identify class names
    class_matches = re.findall(r'class\s+(\w+)', code)
    # Identify method names
    method_matches = re.findall(r'(?:public|private|protected)?\s+\w+\s+(\w+)\s*\([^)]*\)', code)
    # Identify imports
    import_matches = re.findall(r'import\s+([^;]+);', code)
    
    return {
        'classes': class_matches,
        'methods': method_matches,
        'imports': import_matches
    }

def manage_students(db):
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🎓 Advanced Student Code Analysis Dashboard")
    
    # MongoDB connection
    try:
        username = "abhishelke297127"
        password = "Abhi%402971"
        connection_string = f"mongodb+srv://{username}:{password}@cluster0.uu8yq.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(connection_string)
        db = client["JavaFileAnalysis"]
        
        # Create main tabs
        overview_tab, code_tab, analytics_tab, trends_tab = st.tabs([
            "📊 Overview", 
            "💻 Code Explorer", 
            "📈 Analytics",
            "📋 Trends"
        ])
        
        collections = db.list_collection_names()
        
        with overview_tab:
            st.header("Student Overview")
            
            # Key metrics in a row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Students", len(collections))
            
            # Student selector with search
            selected_student = st.selectbox(
                "Select Student Repository",
                collections,
                help="Choose a student's repository to analyze"
            )
            
            if selected_student:
                documents = list(db[selected_student].find())
                
                # Update metrics
                with col2:
                    st.metric("Total Commits", len(documents))
                with col3:
                    java_files = set()
                    for doc in documents:
                        if 'added_java_files' in doc and isinstance(doc['added_java_files'], dict):
                            java_files.update(doc['added_java_files'].keys())
                    st.metric("Java Files", len(java_files))
                with col4:
                    # Fixed last activity calculation
                    commit_timestamps = [
                        doc.get('timestamp') 
                        for doc in documents 
                        if isinstance(doc.get('timestamp'), datetime)
                    ]
                    if commit_timestamps:
                        last_commit = max(commit_timestamps)
                        days_since = (datetime.now() - last_commit).days
                        activity_text = (
                            "Today" if days_since == 0 
                            else "Yesterday" if days_since == 1 
                            else f"{days_since} days ago"
                        )
                        st.metric("Last Activity", activity_text)
                    else:
                        st.metric("Last Activity", "No activity")
        
        with code_tab:
            if selected_student:
                st.header("Code Explorer")
                
                # File selection with metrics
                java_files_list = sorted(java_files)
                selected_file = st.selectbox(
                    "Select Java File",
                    java_files_list,
                    help="Choose a Java file to analyze"
                )
                
                if selected_file:
                    # Get file versions
                    versions = []
                    for doc in documents:
                        if ('added_java_files' in doc and 
                            isinstance(doc['added_java_files'], dict) and 
                            selected_file in doc['added_java_files']):
                            versions.append({
                                'timestamp': doc.get('timestamp', 'Unknown'),
                                'content': doc['added_java_files'][selected_file]
                            })
                    
                    # Version comparison
                    st.subheader("Version Comparison")
                    col1, col2 = st.columns(2)
                    with col1:
                        v1 = st.selectbox("Select Base Version", 
                                        range(len(versions)), 
                                        format_func=lambda x: f"Version {x+1}")
                    with col2:
                        v2 = st.selectbox("Select Compare Version", 
                                        range(len(versions)), 
                                        format_func=lambda x: f"Version {x+1}")
                    
                    # Show diff
                    if v1 != v2:
                        st.subheader("Code Changes")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.code(versions[v1]['content'], language='java')
                        with col2:
                            st.code(versions[v2]['content'], language='java')
        
        with analytics_tab:
            if selected_student and selected_file and versions:
                st.header("Code Analytics")
                
                # Get latest version for analysis
                latest_code = versions[-1]['content']
                
                # Code metrics
                metrics = analyze_code_complexity(latest_code)
                summary = generate_code_summary(latest_code)
                
                # Display metrics in an organized way
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Cyclomatic Complexity", metrics['complexity'])
                with col2:
                    st.metric("Methods", metrics['methods'])
                with col3:
                    st.metric("Loops", metrics['loops'])
                with col4:
                    st.metric("Conditionals", metrics['conditionals'])
                
                # Code structure visualization
                st.subheader("Code Structure")
                code_structure = {
                    'Classes': len(summary['classes']),
                    'Methods': len(summary['methods']),
                    'Imports': len(summary['imports'])
                }
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(code_structure.keys()),
                        y=list(code_structure.values()),
                        text=list(code_structure.values()),
                        textposition='auto',
                    )
                ])
                fig.update_layout(title="Code Components")
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed breakdown
                with st.expander("View Detailed Code Analysis"):
                    st.markdown("### Classes")
                    for cls in summary['classes']:
                        st.write(f"- {cls}")
                    
                    st.markdown("### Methods")
                    for method in summary['methods']:
                        st.write(f"- {method}")
                    
                    st.markdown("### Imports")
                    for imp in summary['imports']:
                        st.write(f"- {imp}")
        
        with trends_tab:
            if selected_student and versions:
                st.header("Code Evolution Trends")
                
                # Track metrics over time
                trend_data = []
                for idx, version in enumerate(versions):
                    metrics = analyze_code_complexity(version['content'])
                    trend_data.append({
                        'version': idx + 1,
                        'timestamp': version['timestamp'],
                        **metrics
                    })
                
                trend_df = pd.DataFrame(trend_data)
                
                # Plot metrics trends
                fig = go.Figure()
                metrics_to_plot = ['complexity', 'methods', 'loops', 'conditionals']
                
                for metric in metrics_to_plot:
                    fig.add_trace(go.Scatter(
                        x=trend_df['version'],
                        y=trend_df[metric],
                        name=metric.capitalize(),
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    title="Code Metrics Evolution",
                    xaxis_title="Version",
                    yaxis_title="Count",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Code size evolution
                sizes = [len(version['content'].split('\n')) for version in versions]
                fig = px.line(
                    x=range(1, len(sizes) + 1),
                    y=sizes,
                    title="Code Size Evolution",
                    labels={'x': 'Version', 'y': 'Lines of Code'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.error("Please check your database connection and try again.")
    
    finally:
        if 'client' in locals():
            client.close()
def edit_question(db, question):
    with st.form(key=f"edit_form_{question['_id']}"):
        new_question_name = st.text_input("Question Name", value=question['question_name'])
        new_class_name = st.text_input("Class Name", value=question['class_name'])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save", use_container_width=True):
                try:
                    db.questions.update_one(
                        {"_id": ObjectId(question["_id"])},
                        {"$set": {
                            "question_name": new_question_name,
                            "class_name": new_class_name,
                            "updated_at": datetime.now()
                        }}
                    )
                    st.success("✅ Changes saved!")
                    st.session_state[f"editing_{question['_id']}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state[f"editing_{question['_id']}"] = False
                st.rerun()