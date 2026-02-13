import streamlit as st
import json
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USERS_FILE = "users.json"
HISTORY_FILE = "analysis_history.json"

# Supported programming languages
SUPPORTED_LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", 
    "Rust", "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "SQL"
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_json_file(filename):
    """Load JSON file or return empty dict if not exists"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json_file(filename, data):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'language' not in st.session_state:
        st.session_state.language = 'en'

# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def register_user(username, password):
    """Register a new user"""
    users = load_json_file(USERS_FILE)
    
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        "password": hash_password(password),
        "created_at": datetime.now().isoformat()
    }
    
    save_json_file(USERS_FILE, users)
    return True, "Registration successful"

def authenticate_user(username, password):
    """Authenticate user credentials"""
    users = load_json_file(USERS_FILE)
    
    if username not in users:
        return False, "Username not found"
    
    if users[username]["password"] == hash_password(password):
        return True, "Login successful"
    
    return False, "Incorrect password"

def logout():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.page = 'home'
    st.session_state.analysis_result = None

# ============================================================================
# AI ANALYSIS FUNCTIONS
# ============================================================================

def analyze_code_with_ai(code, language):
    """
    Analyze code using Groq API with LLaMA 3.3 70B
    Returns structured analysis with review, optimization, security, and refactored code
    """
    if not GROQ_API_KEY:
        return {"error": "Groq API key not configured. Please set GROQ_API_KEY in .env file"}
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Structured prompt for comprehensive code analysis
        prompt = f"""You are an expert code reviewer and security analyst. Analyze the following {language} code comprehensively.

**IMPORTANT**: Provide your analysis in the following structured format with clear section headers:

## Code Review
- List all bugs and logic errors found
- Identify bad coding practices
- Point out readability issues
- Mention any code smells or anti-patterns

## Optimization Suggestions
- Suggest performance improvements
- Identify memory usage optimization opportunities
- Analyze time complexity and suggest improvements
- Recommend algorithmic optimizations

## Security Issues
- Identify insecure functions or patterns
- Detect potential injection vulnerabilities (SQL, XSS, etc.)
- Flag unsafe dependencies or imports
- Highlight authentication/authorization issues
- Note any data exposure risks

## Refactored Code
Provide a complete, optimized, and secure version of the code that:
- Fixes all identified bugs
- Implements best practices
- Improves performance
- Addresses security vulnerabilities
- Maintains the same functionality
- Is production-ready

**Code to analyze:**
```{language.lower()}
{code}
```

Provide actionable, specific feedback. Do not hallucinate vulnerabilities. Be precise and technical."""

        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert {language} developer and security analyst specializing in code review, optimization, and refactoring."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=4000,
        )
        
        analysis_text = chat_completion.choices[0].message.content
        
        # Parse the structured response
        result = {
            "code_review": "",
            "optimization": "",
            "security": "",
            "refactored_code": "",
            "raw_analysis": analysis_text
        }
        
        # Extract sections from the response
        sections = {
            "## Code Review": "code_review",
            "## Optimization Suggestions": "optimization",
            "## Security Issues": "security",
            "## Refactored Code": "refactored_code"
        }
        
        current_section = None
        lines = analysis_text.split('\n')
        
        for line in lines:
            for header, key in sections.items():
                if header in line:
                    current_section = key
                    break
            
            if current_section:
                result[current_section] += line + '\n'
        
        # Clean up sections
        for key in ["code_review", "optimization", "security", "refactored_code"]:
            result[key] = result[key].strip()
        
        return result
        
    except Exception as e:
        return {"error": f"AI Analysis Error: {str(e)}"}

def save_analysis_to_history(username, code, language, result):
    """Save analysis result to user's history"""
    history = load_json_file(HISTORY_FILE)
    
    if username not in history:
        history[username] = []
    
    history[username].append({
        "timestamp": datetime.now().isoformat(),
        "language": language,
        "code_snippet": code[:200] + "..." if len(code) > 200 else code,
        "has_errors": "error" not in result,
        "analysis_summary": result.get("code_review", "")[:150]
    })
    
    # Keep only last 50 analyses per user
    history[username] = history[username][-50:]
    
    save_json_file(HISTORY_FILE, history)

# ============================================================================
# UI STYLING
# ============================================================================

def apply_custom_css():
    """Apply custom CSS for professional, minimal, aesthetic design"""
    st.markdown("""
    <style>
    /* Global Styles */
    .main {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #1f2937;
        color: #ffffff;
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #374151;
        border-color: #4b5563;
    }
    
    /* Text Input */
    .stTextInput>div>div>input {
        background-color: #1f2937;
        color: #ffffff;
        border: 1px solid #374151;
        border-radius: 6px;
    }
    
    /* Text Area */
    .stTextArea>div>div>textarea {
        background-color: #1f2937;
        color: #ffffff;
        border: 1px solid #374151;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
    }
    
    /* Select Box */
    .stSelectbox>div>div>select {
        background-color: #1f2937;
        color: #ffffff;
        border: 1px solid #374151;
        border-radius: 6px;
    }
    
    /* Info/Success/Error boxes */
    .stAlert {
        background-color: #1f2937;
        border-radius: 6px;
        border-left: 4px solid #3b82f6;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background-color: #1f2937;
        border-radius: 6px;
        border: 1px solid #374151;
    }
    
    /* Divider */
    hr {
        border-color: #374151;
    }
    
    /* Custom card styling */
    .analysis-card {
        background-color: #1f2937;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #374151;
        margin: 1rem 0;
    }
    
    .section-header {
        color: #60a5fa;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #374151;
        padding-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGE RENDERING FUNCTIONS
# ============================================================================

def render_home_page():
    """Render the home/landing page"""
    st.markdown("<h1 style='text-align: center;'>🔍 CodeRefine</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #9ca3af;'>Generative AI-Powered Code Review and Optimization Engine</h3>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### What is CodeRefine?
        
        CodeRefine is an intelligent code analysis platform powered by **LLaMA 3.3 70B** that helps developers:
        
        - 🐛 **Identify Bugs** - Detect logic errors and code issues
        - ⚡ **Optimize Performance** - Improve speed and memory usage
        - 🔒 **Enhance Security** - Find vulnerabilities and injection risks
        - ✨ **Refactor Code** - Get cleaner, production-ready code
        
        ### How It Works
        
        1. **Login or Sign Up** - Create your account
        2. **Upload Code** - Paste or upload your source code
        3. **Select Language** - Choose your programming language
        4. **Analyze** - Get comprehensive AI-powered insights
        5. **Improve** - Apply suggestions and download refactored code
        
        ### Supported Languages
        
        Python • JavaScript • TypeScript • Java • C++ • C# • Go • Rust • PHP • Ruby • Swift • Kotlin • Scala • R • SQL
        """)
        
        st.markdown("---")
        
        if not st.session_state.authenticated:
            col_login, col_signup = st.columns(2)
            
            with col_login:
                if st.button("🔑 Login", use_container_width=True):
                    st.session_state.page = 'login'
                    st.rerun()
            
            with col_signup:
                if st.button("📝 Sign Up", use_container_width=True):
                    st.session_state.page = 'signup'
                    st.rerun()
        else:
            if st.button("🚀 Go to Dashboard", use_container_width=True):
                st.session_state.page = 'dashboard'
                st.rerun()

def render_login_page():
    """Render the login page"""
    st.markdown("<h2 style='text-align: center;'>🔑 Login to CodeRefine</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Login", use_container_width=True):
                if username and password:
                    success, message = authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.page = 'dashboard'
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both username and password")
        
        with col_btn2:
            if st.button("Back to Home", use_container_width=True):
                st.session_state.page = 'home'
                st.rerun()
        
        st.markdown("---")
        st.markdown("<p style='text-align: center;'>Don't have an account? <a href='#'>Sign Up</a></p>", unsafe_allow_html=True)
        
        if st.button("Go to Sign Up", use_container_width=True):
            st.session_state.page = 'signup'
            st.rerun()

def render_signup_page():
    """Render the signup page"""
    st.markdown("<h2 style='text-align: center;'>📝 Create Your Account</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        username = st.text_input("Choose Username", key="signup_username")
        password = st.text_input("Choose Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Sign Up", use_container_width=True):
                if username and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = register_user(username, password)
                        if success:
                            st.success(message)
                            st.info("Please login with your credentials")
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Please fill in all fields")
        
        with col_btn2:
            if st.button("Back to Home", use_container_width=True):
                st.session_state.page = 'home'
                st.rerun()

def render_dashboard():
    """Render the main dashboard for code analysis"""
    st.markdown(f"<h2>👨‍💻 Welcome, {st.session_state.username}!</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Code Analysis Dashboard")
    
    with col2:
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
    
    st.markdown("---")
    
    # Code input section
    st.markdown("### 📝 Input Your Code")
    
    # File upload option
    uploaded_file = st.file_uploader("Upload Code File (optional)", type=['py', 'js', 'ts', 'java', 'cpp', 'cs', 'go', 'rs', 'php', 'rb', 'swift', 'kt', 'scala', 'r', 'sql'])
    
    # Code editor
    code_input = st.text_area(
        "Paste Your Code Here",
        height=300,
        placeholder="Enter your code here or upload a file above...",
        key="code_input"
    )
    
    # If file uploaded, use its content
    if uploaded_file is not None:
        code_input = uploaded_file.read().decode('utf-8')
        st.info(f"Loaded code from: {uploaded_file.name}")
    
    # Language selection
    col_lang, col_analyze = st.columns([2, 1])
    
    with col_lang:
        selected_language = st.selectbox(
            "Select Programming Language",
            SUPPORTED_LANGUAGES,
            key="language_select"
        )
    
    with col_analyze:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze Code", use_container_width=True, type="primary")
    
    # Analysis execution
    if analyze_button:
        if not code_input or code_input.strip() == "":
            st.error("Please enter or upload code to analyze")
        else:
            with st.spinner("🤖 Analyzing your code with AI... This may take a moment."):
                result = analyze_code_with_ai(code_input, selected_language)
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.analysis_result = result
                    save_analysis_to_history(st.session_state.username, code_input, selected_language, result)
                    st.session_state.page = 'results'
                    st.rerun()

def render_results_page():
    """Render the analysis results page"""
    st.markdown("<h2>📊 Analysis Results</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("← Back to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    result = st.session_state.analysis_result
    
    if result:
        # Code Review Section
        st.markdown("<div class='section-header'>🐛 Code Review</div>", unsafe_allow_html=True)
        if result.get("code_review"):
            st.markdown(result["code_review"])
        else:
            st.info("No specific code review issues found")
        
        st.markdown("---")
        
        # Optimization Suggestions
        st.markdown("<div class='section-header'>⚡ Optimization Suggestions</div>", unsafe_allow_html=True)
        if result.get("optimization"):
            st.markdown(result["optimization"])
        else:
            st.info("No optimization suggestions")
        
        st.markdown("---")
        
        # Security Issues
        st.markdown("<div class='section-header'>🔒 Security Issues</div>", unsafe_allow_html=True)
        if result.get("security"):
            st.markdown(result["security"])
        else:
            st.success("No security vulnerabilities detected")
        
        st.markdown("---")
        
        # Refactored Code
        st.markdown("<div class='section-header'>✨ Refactored Code</div>", unsafe_allow_html=True)
        if result.get("refactored_code"):
            # Extract code from markdown code blocks if present
            refactored = result["refactored_code"]
            st.code(refactored, language="python")
            
            # Copy button functionality
            st.download_button(
                label="📥 Download Refactored Code",
                data=refactored,
                file_name="refactored_code.txt",
                mime="text/plain"
            )
        else:
            st.info("No refactored code available")
        
        st.markdown("---")
        
        # Full analysis (collapsible)
        with st.expander("📄 View Full Analysis"):
            st.markdown(result.get("raw_analysis", "No analysis available"))
    
    else:
        st.warning("No analysis results available")
        if st.button("Go to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    # Page configuration
    st.set_page_config(
        page_title="CodeRefine - AI Code Review",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Page routing
    if st.session_state.page == 'home':
        render_home_page()
    elif st.session_state.page == 'login':
        render_login_page()
    elif st.session_state.page == 'signup':
        render_signup_page()
    elif st.session_state.page == 'dashboard':
        if st.session_state.authenticated:
            render_dashboard()
        else:
            st.warning("Please login to access the dashboard")
            st.session_state.page = 'login'
            st.rerun()
    elif st.session_state.page == 'results':
        if st.session_state.authenticated:
            render_results_page()
        else:
            st.warning("Please login to view results")
            st.session_state.page = 'login'
            st.rerun()

# Run the application
if __name__ == "__main__":
    main()
