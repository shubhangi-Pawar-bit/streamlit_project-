import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from streamlit_lottie import st_lottie
import requests
import altair as alt

def load_lottie_url(url):
    """Load Lottie animation from URL"""
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Custom CSS for better styling
def init_styles():
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        .stProgress .st-bo {
            background-color: #00a651;
        }
        .assignment-card {
            transition: all 0.3s ease;
        }
        .assignment-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def student_dashboard(db):
    """Enhanced Student Dashboard with personalized data and reload button."""
    # init_styles()
    st.subheader("Student Dashboard")
    
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.write(f"Welcome, {st.session_state.role}")
    with col2:
        if st.button("🔄 Reload", key="reload_dashboard"):
            loading_animation = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_innovation.json")
            if loading_animation:
                st_lottie(loading_animation, height=80)
            st.cache_data.clear()
            st.success("Data reloaded!")
            st.rerun()
    
    try:
        questions_collection = db.questions
        questions = list(questions_collection.find())
        java_analysis_db = db.client['JavaFileAnalysis']
        
        name = get_student_name(db, st.session_state.username)
        if name and name in java_analysis_db.list_collection_names():
            student_collection = java_analysis_db[name]
            commits = list(student_collection.find())
            
            total_commits = len(commits)
            total_files = sum(len(commit.get('added_java_files', {})) for commit in commits)
            recent_activity = any(
                datetime.strptime(commit['commit_date'], '%Y-%m-%d').date() == datetime.now().date() 
                for commit in commits
            )
            
            # Enhanced metrics display
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Total Assignments", len(questions),
                         delta="Available",
                         delta_color="normal")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                weekly_commits = len([c for c in commits if 
                    datetime.strptime(c['commit_date'], '%Y-%m-%d').date() > 
                    datetime.now().date() - timedelta(days=7)])
                st.metric("Total Commits", total_commits,
                         delta=f"+{weekly_commits} this week",
                         delta_color="normal")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Java Files", total_files,
                         delta="Created",
                         delta_color="normal")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Today's Activity", 
                         "Active 🟢" if recent_activity else "Inactive ⚪",
                         delta="Last 24h",
                         delta_color="normal")
                st.markdown('</div>', unsafe_allow_html=True)

            # Activity Timeline
            st.subheader("Activity Overview")
            activity_data = []
            for commit in commits:
                date = datetime.strptime(commit['commit_date'], '%Y-%m-%d')
                activity_data.append({
                    'date': date,
                    'files_changed': len(commit.get('added_java_files', {})) + 
                                   len(commit.get('modified_java_files', {}))
                })
            
            if activity_data:
                df = pd.DataFrame(activity_data)
                df = df.set_index('date')
                df = df.resample('D').sum().reset_index()
                
                # Updated chart configuration to remove white background
                chart = alt.Chart(df).mark_area(
                    line={'color':'#00a651'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[
                            alt.GradientStop(color='rgba(0, 166, 81, 0.1)', offset=0),  # Changed from white to transparent green
                            alt.GradientStop(color='#00a651', offset=1)
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0
                    )
                ).encode(
                    x='date:T',
                    y='files_changed:Q',
                    tooltip=['date:T', 'files_changed:Q']
                ).properties(
                    height=200
                ).configure_axis(
                    grid=False
                )
                st.altair_chart(chart, use_container_width=True)
            
            # Enhanced Recent Activity Display
            st.subheader("Recent Activity")
            for commit in commits[:5]:
                with st.expander(f"Commit: {commit['commit_message'][:50]}...", expanded=False):
                    cols = st.columns([1, 1])
                    with cols[0]:
                        st.markdown(f"**Date:** {commit['commit_date']}")
                        st.markdown(f"**Time:** {commit['commit_time']}")
                    with cols[1]:
                        if commit.get('added_java_files'):
                            st.markdown("**📥 Added Files:**")
                            for file in commit['added_java_files'].keys():
                                st.markdown(f"- `{file}`")
                        if commit.get('modified_java_files'):
                            st.markdown("**🔄 Modified Files:**")
                            for file in commit['modified_java_files'].keys():
                                st.markdown(f"- `{file}`")
                    
                    if commit.get('added_java_files') or commit.get('modified_java_files'):
                        tabs = st.tabs(["Added Files", "Modified Files"])
                        with tabs[0]:
                            for filename, content in commit.get('added_java_files', {}).items():
                                st.code(content, language='java')
                        with tabs[1]:
                            for filename, content in commit.get('modified_java_files', {}).items():
                                st.code(content, language='java')
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
def student_assignments(db, username):
    """Enhanced assignments view with reload button."""
    init_styles()
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.subheader("My Assignments")
    with col2:
        if st.button("🔄 Reload", key="reload_assignments"):
            st.cache_data.clear()
            st.success("Data reloaded!")
            st.rerun()
    
    try:
        questions_collection = db.questions
        questions = list(questions_collection.find({}, {"question_name": 1, "class_name": 1, "_id": 0}))
        
        name = get_student_name(db, username)
        if not name:
            raise ValueError(f"User not found: {username}")
        
        java_analysis_db = db.client['JavaFileAnalysis']
        added_java_keys = get_student_files(java_analysis_db, name)
        
        total = len(questions)
        completed = sum(1 for q in questions if q.get('class_name', '').replace('.java', '') in added_java_keys)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # Enhanced progress visualization
        progress_cols = st.columns([2, 1])
        with progress_cols[0]:
            st.progress(completion_rate / 100)
            st.write(f"Overall Progress: {completion_rate:.1f}%")
        with progress_cols[1]:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=completion_rate,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#00a651"},
                    'steps': [
                        {'range': [0, 33], 'color': "lightgray"},
                        {'range': [33, 66], 'color': "gray"},
                        {'range': [66, 100], 'color': "darkgray"}
                    ]
                }))
            fig.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Completed", completed)
        with col2:
            st.metric("Remaining", total - completed)
        
        filter_status = st.selectbox(
            "Filter by Status",
            [f"All ({total})", f"Pending ({total - completed})", f"Completed ({completed})"]
        )
        
        display_assignments(questions, added_java_keys, filter_status)
        
    except Exception as e:
        st.error(f"Error loading assignments: {e}")

def student_data(db, username):
    """Enhanced student data view with reload button."""
    # init_styles()
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.subheader("My Profile and Data")
    with col2:
        if st.button("🔄 Reload", key="reload_data"):
            st.cache_data.clear()
            st.success("Data reloaded!")
            st.rerun()
    
    try:
        name = get_student_name(db, username)
        if not name:
            raise ValueError(f"User not found: {username}")
        
        # Enhanced profile display
        st.markdown("""
            <div class="metric-card">
                <h3 style="margin:0">Profile Information</h3>
                <hr style="margin:10px 0">
        """, unsafe_allow_html=True)
        st.write(f"**Name:** {name}")
        st.write(f"**Username:** {username}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        java_analysis_db = db.client['JavaFileAnalysis']
        if name in java_analysis_db.list_collection_names():
            student_collection = java_analysis_db[name]
            student_data_list = list(student_collection.find())
            
            if student_data_list:
                st.subheader("Activity Timeline")
                
                # Create timeline visualization with both start and end times
                timeline_data = []
                for data in student_data_list:
                    date_str = f"{data['commit_date']} {data['commit_time']}"
                    start_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    # Set end time to 30 minutes after start time
                    end_time = start_time + timedelta(minutes=30)
                    
                    timeline_data.append({
                        'Task': f"Commit: {data['commit_message'][:30]}...",
                        'Start': start_time,
                        'End': end_time,
                        'Description': data['commit_message']
                    })
                
                if timeline_data:
                    df = pd.DataFrame(timeline_data)
                    
                    # Create a Gantt chart using Plotly
                    fig = px.timeline(
                        df,
                        x_start='Start',
                        x_end='End',
                        y='Task',
                        hover_data=['Description']
                    )
                    
                    # Customize the layout
                    fig.update_layout(
                        height=400,
                        title='Commit Activity Timeline',
                        xaxis_title='Date & Time',
                        yaxis_title='Commits',
                        showlegend=False,
                        # Make it more visually appealing
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        xaxis=dict(
                            gridcolor='black',
                            showgrid=True
                        ),
                        yaxis=dict(
                            gridcolor='black',
                            showgrid=True
                        )
                    )
                    
                    # Update traces
                    fig.update_traces(
                        marker_color='#00a651',  # Match the green theme
                        marker_line_color='darkgreen',
                        marker_line_width=1.5,
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display detailed commit information
                st.subheader("Detailed Activity")
                for data in student_data_list:
                    with st.expander(f"Commit: {data['commit_date']} - {data['commit_time']}", 
                                   expanded=False):
                        st.markdown(f"**Message:** {data['commit_message']}")
                        display_file_changes(data)
            else:
                st.info("No activity data available yet.")
    except Exception as e:
        st.error(f"Error loading student data: {e}")
# Keep original helper functions unchanged
def get_student_name(db, username):
    """Get student's name from login database."""
    login_db = db.client['LoginData']
    for collection_name in login_db.list_collection_names():
        user = login_db[collection_name].find_one({"username": username})
        if user:
            return user['name']
    return None

def get_student_files(db, name):
    """Get student's submitted files."""
    added_java_keys = []
    if name in db.list_collection_names():
        student_collection = db[name]
        documents = list(student_collection.find({}, {"added_java_files": 1, "_id": 0}))
        for doc in documents:
            added_files = doc.get("added_java_files", {})
            if isinstance(added_files, dict):
                added_java_keys.extend(added_files.keys())
    return list(set(added_java_keys))

def display_assignments(questions, added_java_keys, filter_status):
    """Display filtered assignments with enhanced status indicators and better text contrast."""
    for question in questions:
        class_name = question.get('class_name', '').replace('.java', '')
        is_completed = class_name in added_java_keys
        
        if ("Pending" in filter_status and is_completed) or \
           ("Completed" in filter_status and not is_completed):
            continue
        
        status_color = "#00a651" if is_completed else "#dc3545"
        status_icon = "✅" if is_completed else "⏳"
        
        # Using white background for both states
        bg_color = 'white'
        text_color = '#000000'  # Dark text for good visibility
        subtext_color = '#444444'  # Darker gray for better visibility
        
        st.markdown(
            f"""
            <div class='assignment-card' style='
                padding: 15px;
                border-radius: 10px;
                border: 2px solid {status_color};
                margin: 5px 0;
                background-color: {bg_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            '>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='flex-grow: 1;'>
                        <span style='
                            font-size: 1.1em; 
                            font-weight: 600;
                            color: {text_color};
                            display: block;
                            margin-bottom: 4px;
                            letter-spacing: 0.2px;
                        '>
                            {question.get('question_name', 'Unnamed Question')}
                        </span>
                        <span style='
                            color: {subtext_color};
                            font-size: 0.9em;
                            display: block;
                            font-weight: 500;
                        '>
                            {class_name}
                        </span>
                    </div>
                    <div style='margin-left: 15px;'>
                        <span style='
                            background-color: {status_color};
                            color: white;
                            padding: 5px 12px;
                            border-radius: 15px;
                            font-size: 0.9em;
                            display: inline-block;
                            min-width: 90px;
                            text-align: center;
                            font-weight: 500;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        '>
                            {status_icon} {'Completed' if is_completed else 'Pending'}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
def display_file_changes(commit_data):
    """Display file changes in a structured format with enhanced visualization."""
    if commit_data.get('added_java_files'):
        st.markdown("""
            <div style='
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            '>
                <h4 style='margin: 0; color: #28a745;'>📝 Added Files</h4>
            </div>
        """, unsafe_allow_html=True)
        
        tabs = st.tabs(list(commit_data['added_java_files'].keys()))
        for tab, (filename, content) in zip(tabs, commit_data['added_java_files'].items()):
            with tab:
                st.code(content, language='java')
    
    if commit_data.get('modified_java_files'):
        st.markdown("""
            <div style='
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            '>
                <h4 style='margin: 0; color: #007bff;'>🔄 Modified Files</h4>
            </div>
        """, unsafe_allow_html=True)
        
        tabs = st.tabs(list(commit_data['modified_java_files'].keys()))
        for tab, (filename, content) in zip(tabs, commit_data['modified_java_files'].items()):
            with tab:
                st.code(content, language='java')