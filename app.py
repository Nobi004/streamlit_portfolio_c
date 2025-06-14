import streamlit as st
import json
import os
from datetime import datetime
import sqlite3
import hashlib
import pandas as pd
from PIL import Image
import base64
import io
import markdown
import re
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="AI Engineer Portfolio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        padding-top: 0rem;
    }
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero section styling */
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        animation: fadeInUp 1s ease-out;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        animation: slideInLeft 1s ease-out;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        font-weight: 300;
        margin-bottom: 2rem;
        animation: slideInRight 1s ease-out;
    }
    
    /* Card styling */
    .project-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
    }
    
    .project-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .blog-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border-left: 4px solid #667eea;
    }
    
    .blog-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Button styling */
    .download-btn {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        text-decoration: none;
        font-weight: 600;
        display: inline-block;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
    }
    
    .download-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Skills section */
    .skill-tag {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        display: inline-block;
        margin: 0.25rem;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Contact form */
    .contact-form {
        background: #f8fafc;
        padding: 2rem;
        border-radius: 15px;
        margin-top: 2rem;
    }
    
    /* Navigation */
    .nav-link {
        padding: 0.5rem 1rem;
        margin: 0 0.25rem;
        border-radius: 8px;
        text-decoration: none;
        color: #4a5568;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .nav-link:hover {
        background: #667eea;
        color: white;
    }
    
    .nav-link.active {
        background: #667eea;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Database initialization
def init_database():
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    
    # Create projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            technologies TEXT NOT NULL,
            image_path TEXT,
            github_link TEXT,
            demo_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create blog posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            featured_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create contact messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user if doesn't exist
    cursor.execute('SELECT COUNT(*) FROM admin_users WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('INSERT INTO admin_users (username, password_hash) VALUES (?, ?)', 
                      ('admin', password_hash))
    
    conn.commit()
    conn.close()

# Authentication functions
def authenticate_admin(username, password):
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute('SELECT id FROM admin_users WHERE username = ? AND password_hash = ?', 
                  (username, password_hash))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def is_admin_logged_in():
    return st.session_state.get('admin_logged_in', False)

# Data access functions
def get_projects():
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
    projects = cursor.fetchall()
    conn.close()
    return projects

def get_blog_posts(search_term=None, tag_filter=None):
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM blog_posts'
    params = []
    
    if search_term or tag_filter:
        query += ' WHERE '
        conditions = []
        
        if search_term:
            conditions.append('(title LIKE ? OR content LIKE ?)')
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        if tag_filter:
            conditions.append('tags LIKE ?')
            params.append(f'%{tag_filter}%')
        
        query += ' AND '.join(conditions)
    
    query += ' ORDER BY created_at DESC'
    
    cursor.execute(query, params)
    posts = cursor.fetchall()
    conn.close()
    return posts

def add_contact_message(name, email, message):
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)',
                  (name, email, message))
    conn.commit()
    conn.close()

# File handling functions
def get_base64_download_link(file_path, filename):
    """Generate a download link for files"""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" class="download-btn">📄 Download CV</a>'
        return href
    else:
        return '<p style="color: red;">CV file not found. Please contact admin.</p>'

# Page functions
def show_home_page():
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">AI Engineer Portfolio</h1>
        <p class="hero-subtitle">Building the Future with Artificial Intelligence</p>
        <p style="font-size: 1.2rem; margin-bottom: 2rem;">Senior AI Engineer | Machine Learning Specialist | Deep Learning Expert</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 👋 Welcome to My Portfolio")
        st.markdown("""
        I am a passionate AI Engineer with extensive experience in developing cutting-edge machine learning solutions 
        and deploying scalable AI systems. My expertise spans across various domains including Natural Language Processing, 
        Computer Vision, and Large Language Models.
        
        **Current Focus Areas:**
        - Large Language Model Development and Fine-tuning
        - Multimodal AI Systems
        - MLOps and AI Infrastructure
        - Responsible AI and Ethics
        """)
        
        st.markdown("### 🛠️ Technical Skills")
        skills = [
            "Python", "TensorFlow", "PyTorch", "Hugging Face", "LangChain",
            "AWS", "GCP", "Docker", "Kubernetes", "MLflow", "Weights & Biases",
            "Transformer Models", "BERT", "GPT", "Computer Vision", "NLP",
            "Deep Learning", "Reinforcement Learning", "MLOps", "Data Engineering"
        ]
        
        skills_html = "".join([f'<span class="skill-tag">{skill}</span>' for skill in skills])
        st.markdown(f'<div style="margin-top: 1rem;">{skills_html}</div>', unsafe_allow_html=True)
        
        st.markdown("### 📈 Professional Experience")
        st.markdown("""
        **Senior AI Engineer** | *Leading Tech Company* | 2022 - Present
        - Led development of large-scale language models serving millions of users
        - Implemented MLOps pipelines reducing model deployment time by 70%
        - Collaborated with cross-functional teams to deliver AI-powered products
        
        **Machine Learning Engineer** | *AI Startup* | 2020 - 2022
        - Built and deployed computer vision models for autonomous systems
        - Optimized model performance achieving 95% accuracy on production data
        - Mentored junior engineers and established ML best practices
        """)
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        st.metric("Years of Experience", "5+")
        st.metric("AI Projects Completed", "50+")
        st.metric("Models Deployed", "25+")
        st.metric("Publications", "12")
        
        st.markdown("### 📄 Download My CV")
        cv_link = get_base64_download_link("static/cv.pdf", "AI_Engineer_CV.pdf")
        st.markdown(cv_link, unsafe_allow_html=True)
        
        st.markdown("### 🏆 Achievements")
        st.markdown("""
        - **Best AI Innovation Award** 2023
        - **Top 1% Kaggle Competitor**
        - **Published Research** in NeurIPS
        - **Patent Holder** - AI System Optimization
        """)

def show_projects_page():
    st.markdown("# 🚀 AI Projects Portfolio")
    st.markdown("Explore my collection of AI and machine learning projects that demonstrate expertise across various domains.")
    
    projects = get_projects()
    
    if not projects:
        st.info("No projects available yet. Please check back later or contact the admin to add projects.")
        return
    
    for project in projects:
        project_id, title, description, technologies, image_path, github_link, demo_link, created_at = project
        
        st.markdown(f"""
        <div class="project-card">
            <h3 style="color: #2d3748; margin-bottom: 1rem;">{title}</h3>
            <p style="color: #4a5568; line-height: 1.6; margin-bottom: 1rem;">{description}</p>
            <div style="margin-bottom: 1rem;">
                <strong>Technologies:</strong> {technologies}
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        if github_link:
            with col1:
                st.markdown(f'<a href="{github_link}" target="_blank" style="text-decoration: none; background: #24292e; color: white; padding: 0.5rem 1rem; border-radius: 8px; display: inline-block;">🔗 GitHub</a>', unsafe_allow_html=True)
        
        if demo_link:
            with col2:
                st.markdown(f'<a href="{demo_link}" target="_blank" style="text-decoration: none; background: #667eea; color: white; padding: 0.5rem 1rem; border-radius: 8px; display: inline-block;">🚀 Demo</a>', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_blog_page():
    st.markdown("# 📝 AI Engineering Blog")
    st.markdown("Insights, tutorials, and thoughts on artificial intelligence and machine learning.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search blog posts", placeholder="Enter keywords...")
    
    with col2:
        tag_filter = st.selectbox("🏷️ Filter by tag", ["All", "AI", "ML", "Deep Learning", "NLP", "Computer Vision", "MLOps"])
        if tag_filter == "All":
            tag_filter = None
    
    posts = get_blog_posts(search_term if search_term else None, tag_filter)
    
    if not posts:
        st.info("No blog posts found. Try adjusting your search criteria or check back later.")
        return
    
    for post in posts:
        post_id, title, content, tags, featured_image, created_at, updated_at = post
        
        # Convert markdown content to HTML
        html_content = markdown.markdown(content[:300] + "..." if len(content) > 300 else content)
        
        st.markdown(f"""
        <div class="blog-card">
            <h3 style="color: #2d3748; margin-bottom: 0.5rem;">{title}</h3>
            <p style="color: #718096; font-size: 0.9rem; margin-bottom: 1rem;">📅 {created_at}</p>
            <div style="color: #4a5568; line-height: 1.6; margin-bottom: 1rem;">
                {html_content}
            </div>
        """, unsafe_allow_html=True)
        
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]
            tags_html = "".join([f'<span style="background: #e2e8f0; color: #2d3748; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem; margin-right: 0.5rem;">#{tag}</span>' for tag in tags_list])
            st.markdown(f'<div style="margin-bottom: 1rem;">{tags_html}</div>', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_contact_page():
    st.markdown("# 📞 Get In Touch")
    st.markdown("Let's discuss AI opportunities, collaborations, or any questions you might have.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="contact-form">', unsafe_allow_html=True)
        
        with st.form("contact_form"):
            name = st.text_input("Full Name", placeholder="Your name")
            email = st.text_input("Email Address", placeholder="your.email@example.com")
            message = st.text_area("Message", placeholder="Tell me about your project or question...", height=150)
            
            submitted = st.form_submit_button("Send Message", use_container_width=True)
            
            if submitted:
                if name and email and message:
                    add_contact_message(name, email, message)
                    st.success("Thank you for your message! I'll get back to you soon.")
                else:
                    st.error("Please fill in all fields.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🌐 Connect With Me")
        st.markdown("""
        **Email:** ai.engineer@example.com
        
        **LinkedIn:** [linkedin.com/in/ai-engineer](https://linkedin.com/in/ai-engineer)
        
        **GitHub:** [github.com/ai-engineer](https://github.com/ai-engineer)
        
        **Twitter:** [@ai_engineer](https://twitter.com/ai_engineer)
        """)
        
        st.markdown("### 💼 Professional Services")
        st.markdown("""
        - AI Consulting & Strategy
        - Machine Learning Model Development
        - MLOps Implementation
        - AI Team Training & Mentoring
        - Research & Development
        """)
        
        st.markdown("### 🌍 Location")
        st.markdown("Available for remote work worldwide and on-site in major tech hubs.")

def show_admin_login():
    st.markdown("# 🔐 Admin Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
        
        if login_btn:
            if authenticate_admin(username, password):
                st.session_state.admin_logged_in = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

def show_admin_dashboard():
    st.markdown("# 🛠️ Admin Dashboard")
    
    if st.button("Logout", type="secondary"):
        st.session_state.admin_logged_in = False
        st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🚀 Projects", "📝 Blog", "📨 Messages"])
    
    with tab1:
        st.markdown("### Portfolio Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM projects')
        project_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM blog_posts')
        blog_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM contact_messages')
        message_count = cursor.fetchone()[0]
        
        conn.close()
        
        with col1:
            st.metric("Total Projects", project_count)
        with col2:
            st.metric("Blog Posts", blog_count)
        with col3:
            st.metric("Contact Messages", message_count)
        with col4:
            st.metric("Admin Users", 1)
    
    with tab2:
        st.markdown("### Manage Projects")
        
        # Add new project
        with st.expander("Add New Project"):
            with st.form("add_project"):
                title = st.text_input("Project Title")
                description = st.text_area("Description")
                technologies = st.text_input("Technologies (comma-separated)")
                github_link = st.text_input("GitHub Link (optional)")
                demo_link = st.text_input("Demo Link (optional)")
                
                if st.form_submit_button("Add Project"):
                    if title and description and technologies:
                        conn = sqlite3.connect('portfolio.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO projects (title, description, technologies, github_link, demo_link)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (title, description, technologies, github_link, demo_link))
                        conn.commit()
                        conn.close()
                        st.success("Project added successfully!")
                        st.rerun()
        
        # List existing projects
        projects = get_projects()
        if projects:
            st.markdown("### Existing Projects")
            for project in projects:
                project_id, title, description, technologies, image_path, github_link, demo_link, created_at = project
                
                with st.expander(f"{title}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Description:** {description}")
                        st.write(f"**Technologies:** {technologies}")
                        if github_link:
                            st.write(f"**GitHub:** {github_link}")
                        if demo_link:
                            st.write(f"**Demo:** {demo_link}")
                    
                    with col2:
                        if st.button(f"Delete", key=f"del_proj_{project_id}"):
                            conn = sqlite3.connect('portfolio.db')
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
                            conn.commit()
                            conn.close()
                            st.success("Project deleted!")
                            st.rerun()
    
    with tab3:
        st.markdown("### Manage Blog Posts")
        
        # Add new blog post
        with st.expander("Add New Blog Post"):
            with st.form("add_blog"):
                title = st.text_input("Post Title")
                content = st.text_area("Content (Markdown supported)", height=200)
                tags = st.text_input("Tags (comma-separated)")
                
                if st.form_submit_button("Add Blog Post"):
                    if title and content:
                        conn = sqlite3.connect('portfolio.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO blog_posts (title, content, tags)
                            VALUES (?, ?, ?)
                        ''', (title, content, tags))
                        conn.commit()
                        conn.close()
                        st.success("Blog post added successfully!")
                        st.rerun()
        
        # List existing blog posts
        posts = get_blog_posts()
        if posts:
            st.markdown("### Existing Blog Posts")
            for post in posts:
                post_id, title, content, tags, featured_image, created_at, updated_at = post
                
                with st.expander(f"{title}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Created:** {created_at}")
                        st.write(f"**Tags:** {tags}")
                        st.write(f"**Content Preview:** {content[:200]}...")
                    
                    with col2:
                        if st.button(f"Delete", key=f"del_post_{post_id}"):
                            conn = sqlite3.connect('portfolio.db')
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM blog_posts WHERE id = ?', (post_id,))
                            conn.commit()
                            conn.close()
                            st.success("Blog post deleted!")
                            st.rerun()
    
    with tab4:
        st.markdown("### Contact Messages")
        
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contact_messages ORDER BY created_at DESC')
        messages = cursor.fetchall()
        conn.close()
        
        if messages:
            for message in messages:
                msg_id, name, email, msg_content, created_at = message
                
                with st.expander(f"From: {name} ({email}) - {created_at}"):
                    st.write(msg_content)
                    
                    if st.button(f"Delete Message", key=f"del_msg_{msg_id}"):
                        conn = sqlite3.connect('portfolio.db')
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM contact_messages WHERE id = ?', (msg_id,))
                        conn.commit()
                        conn.close()
                        st.success("Message deleted!")
                        st.rerun()
        else:
            st.info("No messages yet.")

# Main navigation
def main():
    load_css()
    init_database()
    
    # Create static directory if it doesn't exist
    Path("static").mkdir(exist_ok=True)
    
    # Navigation
    st.markdown("### 🤖 AI Engineer Portfolio")
    
    # Main navigation
    pages = ["🏠 Home", "🚀 Projects", "📝 Blog", "📞 Contact"]
    if is_admin_logged_in():
        pages.append("🛠️ Admin Dashboard")
    else:
        pages.append("🔐 Admin Login")
    
    selected_page = st.selectbox("Navigate", pages, label_visibility="collapsed")
    
    st.markdown("---")
    
    # Page routing
    if selected_page == "🏠 Home":
        show_home_page()
    elif selected_page == "🚀 Projects":
        show_projects_page()
    elif selected_page == "📝 Blog":
        show_blog_page()
    elif selected_page == "📞 Contact":
        show_contact_page()
    elif selected_page == "🔐 Admin Login":
        if not is_admin_logged_in():
            show_admin_login()
        else:
            show_admin_dashboard()
    elif selected_page == "🛠️ Admin Dashboard":
        if is_admin_logged_in():
            show_admin_dashboard()
        else:
            show_admin_login()

if __name__ == "__main__":
    main()