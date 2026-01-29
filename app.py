import streamlit as st
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS
import warnings
from datetime import datetime

# --- CONFIGURATION & SETUP ---
warnings.filterwarnings("ignore")
st.set_page_config(
    page_title="WhatsApp Vibe Checker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional, READABLE look
st.markdown("""
    <style>
    /* Main background */
    .main { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Headers */
    h1 { 
        color: #ffffff !important; 
        font-family: 'Helvetica Neue', sans-serif; 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-weight: 700;
    }
    h2, h3 { 
        color: #ffffff !important; 
        font-weight: 600;
    }
    
    /* Metric styling - FIXED WHITE ON WHITE ISSUE */
    [data-testid="stMetricValue"] {
        color: #1E88E5 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #333333 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        border: 2px solid #e0e0e0 !important;
    }
    
    /* Cards */
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        margin: 10px 0;
    }
    
    /* Info boxes */
    .stInfo, .stWarning, .stSuccess {
        background-color: rgba(255,255,255,0.9) !important;
        color: #333333 !important;
        border-radius: 8px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 15px;
    }
    
    /* Summary section */
    .summary-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin: 20px 0;
    }
    
    /* Leaderboard */
    .leaderboard {
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .leader-item {
        display: flex;
        align-items: center;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 8px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .medal {
        font-size: 2rem;
        margin-right: 15px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- PARSING LOGIC ---
MESSAGE_PATTERN = r'.*?\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)$'

@st.cache_data
def load_data(uploaded_file):
    """Parses the uploaded WhatsApp text file into a DataFrame."""
    try:
        stringio = uploaded_file.getvalue().decode("utf-8")
        lines = stringio.splitlines()
    except Exception:
        return pd.DataFrame()

    data = []
    message_buffer = [] 
    date, time, author = None, None, None
    
    for line in lines:
        line = line.strip()
        match = re.match(MESSAGE_PATTERN, line)
        if match:
            if author:
                data.append([date, time, author, ' '.join(message_buffer)])
            date, time, author, message = match.groups()
            message_buffer = [message]
        else:
            if author:
                message_buffer.append(line)
    if author:
        data.append([date, time, author, ' '.join(message_buffer)])

    df = pd.DataFrame(data, columns=['Date', 'Time', 'Author', 'Message'])
    
    try:
        df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=True, errors='coerce')
    except Exception:
        df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
        
    df = df.dropna(subset=['DateTime'])
    return df

def clean_name(name):
    """Truncates and cleans names for charts."""
    if not isinstance(name, str): return str(name)
    cleaned = re.sub(r'[^\w\s\-]', '', name).strip()
    return (cleaned[:15] + "..") if len(cleaned) > 15 else (cleaned or "Unknown")

def get_sentiment(text):
    """Returns a polarity score between -1 (Negative) and 1 (Positive)."""
    return TextBlob(str(text)).sentiment.polarity

# --- VISUALIZATION FUNCTIONS ---
def plot_volume(df):
    st.markdown("### 📣 Message Volume - Who's the Chatterbox?")
    fig, ax = plt.subplots(figsize=(10, 5))
    top_vol = df['CleanAuthor'].value_counts().head(10)
    sns.barplot(x=top_vol.index, y=top_vol.values, hue=top_vol.index, palette="viridis", ax=ax, legend=False)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Total Messages", fontsize=12, fontweight='bold')
    plt.xlabel("Participant", fontsize=12, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("📊 What does this mean?"):
        st.write(f"**{top_vol.index[0]}** is the most active with **{top_vol.values[0]:,}** messages! That's {(top_vol.values[0]/len(df)*100):.1f}% of all messages.")

def plot_sentiment(df):
    st.markdown("### ❤️ Vibe Check - Positivity Score")
    with st.spinner("Analyzing text sentiment... (this might take a moment)"):
        df['Sentiment'] = df.apply(lambda row: get_sentiment(row['Message']) 
                                 if "omitted" not in str(row['Message']).lower() else 0, axis=1)
        
        top_authors = df['CleanAuthor'].value_counts().head(10).index
        sentiment_df = df[df['CleanAuthor'].isin(top_authors)]
        avg_sentiment = sentiment_df.groupby('CleanAuthor')['Sentiment'].mean().sort_values(ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in avg_sentiment.values]
        (avg_sentiment * 100).plot(kind='bar', color=colors, ax=ax)
        ax.axhline(0, color='black', linewidth=1.5, linestyle='--', alpha=0.5)
        plt.ylabel("Positivity Score (%)", fontsize=12, fontweight='bold')
        plt.xlabel("Participant", fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        
        with st.expander("😊 What does this mean?"):
            most_positive = avg_sentiment.index[0]
            score = avg_sentiment.values[0] * 100
            st.write(f"**{most_positive}** brings the most positive energy with a **{score:.1f}%** vibe score! 🌟")
            st.write("Positive scores mean upbeat messages, negative means more critical/sarcastic tones.")
    
    return df

def plot_response_time(df):
    st.markdown("### ⚡ Response Speed - Who Replies Fastest?")
    
    df = df.sort_values('DateTime')
    df['Prev_Author'] = df['Author'].shift(1)
    df['Time_Diff'] = df['DateTime'].diff().dt.total_seconds() / 60
    
    replies = df[(df['Author'] != df['Prev_Author']) & (df['Time_Diff'] < 720) & (df['Time_Diff'] > 0)]
    
    top_authors = df['CleanAuthor'].value_counts().head(10).index
    replies = replies[replies['CleanAuthor'].isin(top_authors)]
    
    if replies.empty:
        st.info("⏳ Not enough conversation data to calculate response times.")
        return

    avg_time = replies.groupby('CleanAuthor')['Time_Diff'].mean().sort_values()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    avg_time.plot(kind='bar', color='#3498db', ax=ax)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Average Minutes", fontsize=12, fontweight='bold')
    plt.xlabel("Participant", fontsize=12, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("⚡ What does this mean?"):
        fastest = avg_time.index[0]
        time_val = avg_time.values[0]
        st.write(f"**{fastest}** is the speed demon, replying in an average of **{time_val:.1f} minutes**! 🏃‍♂️💨")

def plot_wordcloud(df):
    st.markdown("### ☁️ Word Cloud - What's Everyone Talking About?")
    text = " ".join(msg for msg in df.Message if isinstance(msg, str))
    stopwords = set(STOPWORDS)
    stopwords.update(["media", "omitted", "image", "video", "sticker", "message", "deleted", "null", "https", "www", "com"])
    
    if len(text) < 100:
        st.warning("⚠️ Not enough text data for a word cloud.")
        return

    wordcloud = WordCloud(width=1000, height=500, background_color='white', 
                          stopwords=stopwords, colormap='viridis', 
                          max_words=100, relative_scaling=0.5).generate(text)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("☁️ What does this mean?"):
        st.write("Bigger words = mentioned more often. This shows the most common topics in your chat!")

def plot_hourly_activity(df):
    st.markdown("### 🕰️ Hourly Activity - Night Owls vs Early Birds")
    df['Hour'] = df['DateTime'].dt.hour
    hour_counts = df['Hour'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(12, 4))
    sns.lineplot(x=hour_counts.index, y=hour_counts.values, linewidth=3, color='#9b59b6', ax=ax, marker='o')
    ax.fill_between(hour_counts.index, hour_counts.values, color='#9b59b6', alpha=0.2)
    ax.set_xticks(range(0, 24))
    ax.set_xlim(0, 23)
    ax.set_xlabel("Hour of Day (0 = Midnight, 23 = 11PM)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Message Count", fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("🦉 What does this mean?"):
        peak_hour = hour_counts.idxmax()
        peak_time = f"{peak_hour:02d}:00"
        st.write(f"Peak activity is at **{peak_time}**! That's when this chat is most alive. 🔥")

def plot_weekly_activity(df):
    st.markdown("### 📅 Weekly Pattern - Busiest Days")
    df['Day'] = df['DateTime'].dt.day_name()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df['Day'].value_counts().reindex(days_order)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=day_counts.index, y=day_counts.values, hue=day_counts.index, palette="viridis", ax=ax, legend=False)
    plt.ylabel("Message Count", fontsize=12, fontweight='bold')
    plt.xlabel("Day of Week", fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("📅 What does this mean?"):
        busiest_day = day_counts.idxmax()
        count = day_counts.max()
        st.write(f"**{busiest_day}** is the busiest day with **{count:,}** messages! The chat goes wild on this day. 🎉")

def show_leaderboard(df):
    st.markdown("## 🏆 Hall of Fame - Top 5 Contributors")
    
    top5 = df['Author'].value_counts().head(5)
    medals = ['🥇', '🥈', '🥉', '🏅', '🎖️']
    
    # Use Streamlit columns for better rendering
    for i, (author, count) in enumerate(top5.items()):
        percentage = (count / len(df)) * 100
        clean_author = clean_name(author)
        
        # Create a card for each person
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%); 
                    padding: 20px; margin: 15px 0; border-radius: 10px; 
                    border-left: 5px solid #667eea; box-shadow: 0 3px 8px rgba(0,0,0,0.1);
                    display: flex; align-items: center;">
            <div style="font-size: 2.5rem; margin-right: 20px; min-width: 60px; text-align: center;">
                {medals[i]}
            </div>
            <div style="flex-grow: 1;">
                <h3 style="margin: 0; color: #333; font-size: 1.4rem;">{clean_author}</h3>
                <p style="margin: 8px 0 0 0; color: #666; font-size: 1rem;">
                    <strong>{count:,}</strong> messages • <strong>{percentage:.1f}%</strong> of total
                </p>
            </div>
            <div style="font-size: 2rem; font-weight: bold; color: #667eea; min-width: 60px; text-align: center;">
                #{i+1}
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_summary(df):
    st.markdown("## 📊 Executive Summary")
    
    start_date = df['DateTime'].min().strftime('%B %d, %Y')
    end_date = df['DateTime'].max().strftime('%B %d, %Y')
    total_msg = len(df)
    days = (df['DateTime'].max() - df['DateTime'].min()).days or 1
    avg_per_day = int(total_msg / days)
    unique_authors = df['Author'].nunique()
    
    # Calculate some fun stats
    most_active = df['Author'].value_counts().index[0]
    most_active_count = df['Author'].value_counts().values[0]
    
    df['Hour'] = df['DateTime'].dt.hour
    peak_hour = df['Hour'].value_counts().idxmax()
    
    df['Day'] = df['DateTime'].dt.day_name()
    busiest_day = df['Day'].value_counts().idxmax()
    
    # Use container with custom styling
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 30px; border-radius: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.2);">
            <h2 style="margin-top: 0; color: white;">📈 Chat Statistics</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats grid using Streamlit columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #667eea; margin-bottom: 10px;">📅 Timeframe</h4>
                <p style="font-size: 1rem; margin: 5px 0; color: #333;"><strong>{start_date}</strong></p>
                <p style="font-size: 0.8rem; color: #666;">to</p>
                <p style="font-size: 1rem; margin: 5px 0; color: #333;"><strong>{end_date}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #667eea; margin-bottom: 10px;">💬 Activity</h4>
                <p style="font-size: 2rem; font-weight: bold; margin: 10px 0; color: #1E88E5;">{total_msg:,}</p>
                <p style="font-size: 0.9rem; color: #666;">Total Messages</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #667eea; margin-bottom: 10px;">📊 Average</h4>
                <p style="font-size: 2rem; font-weight: bold; margin: 10px 0; color: #1E88E5;">{avg_per_day}</p>
                <p style="font-size: 0.9rem; color: #666;">Messages per day</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="color: #667eea; margin-bottom: 10px;">👥 Participants</h4>
                <p style="font-size: 2rem; font-weight: bold; margin: 10px 0; color: #1E88E5;">{unique_authors}</p>
                <p style="font-size: 0.9rem; color: #666;">Active members</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Key Insights box
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 12px; margin-top: 20px; color: white;">
            <h3 style="margin-top: 0; color: white;">🎯 Key Insights</h3>
            <ul style="font-size: 1rem; line-height: 2; list-style: none; padding-left: 0;">
                <li>🏆 <strong>{clean_name(most_active)}</strong> dominated the chat with <strong>{most_active_count:,}</strong> messages ({(most_active_count/total_msg*100):.1f}%)</li>
                <li>⏰ Peak activity happens around <strong>{peak_hour:02d}:00</strong> - prime chatting time!</li>
                <li>📅 <strong>{busiest_day}</strong> is when things get wild with the most messages 🎉</li>
                <li>📆 This chat lasted <strong>{days} days</strong> - that's <strong>{days/365:.1f} years</strong> of memories!</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN APP LAYOUT ---
def main():
    st.title("📊 WhatsApp Vibe Checker")
    st.markdown("### *Uncover the secrets hidden in your group chat* 🕵️‍♂️")
    
    with st.sidebar:
        st.markdown("## 📤 Upload Your Chat")
        st.markdown("---")
        uploaded_file = st.file_uploader("Choose your _chat.txt file", type="txt", help="Export your WhatsApp chat without media")
        
        st.markdown("---")
        st.markdown("### 📱 How to Export")
        st.markdown("""
        **iOS:**
        1. Open chat → tap name
        2. Export Chat
        3. Without Media
        
        **Android:**
        1. Open chat → ⋮ menu
        2. More → Export chat
        3. Without media
        """)
        
        st.markdown("---")
        st.markdown("### 🔒 Privacy First")
        st.info("Your data is processed in memory and never stored. Once you close this tab, it's gone forever.")
        
        st.markdown("---")
        st.markdown("Made with ❤️ by Idy")

    if uploaded_file:
        with st.spinner('🔍 Parsing your chat history... This might take a moment!'):
            df = load_data(uploaded_file)

        if df.empty:
            st.error("⚠️ **Oops!** Couldn't parse the file. Make sure it's an iOS WhatsApp export without media.")
            st.info("💡 Tip: The file should look like `WhatsApp Chat with XYZ.txt`")
        else:
            # Preprocess names
            df['CleanAuthor'] = df['Author'].apply(clean_name)
            
            # Auto-Detect Mode
            unique_authors = df['Author'].nunique()
            mode = "Group" if unique_authors > 2 else "Couple"
            mode_emoji = "👥" if mode == "Group" else "💑"
            
            # Success message
            st.success(f"✅ Successfully loaded **{len(df):,}** messages! Let's dive in... 🏊‍♂️")
            
            # Dashboard Header with Metrics
            st.markdown("---")
            st.markdown(f"## {mode_emoji} {mode} Chat Dashboard")
            
            col1, col2, col3, col4 = st.columns(4)
            
            days = (df['DateTime'].max() - df['DateTime'].min()).days or 1
            avg_per_day = int(len(df) / days)
            
            col1.metric("Chat Type", f"{mode_emoji} {mode}")
            col2.metric("Total Messages", f"{len(df):,}")
            col3.metric("Participants", f"{unique_authors} 👤")
            col4.metric("Daily Average", f"{avg_per_day} 💬")
            
            st.markdown("---")

            # Main Visuals Grid
            st.markdown("## 📈 Deep Dive Analytics")
            
            # Row 1: Volume + Response Time
            col1, col2 = st.columns(2)
            with col1:
                plot_volume(df)
            with col2:
                plot_response_time(df)
            
            st.markdown("---")
            
            # Row 2: Sentiment + Weekly
            col1, col2 = st.columns(2)
            with col1:
                df = plot_sentiment(df)
            with col2:
                plot_weekly_activity(df)
            
            st.markdown("---")
            
            # Row 3: Hourly Activity (full width)
            plot_hourly_activity(df)
            
            st.markdown("---")
            
            # Row 4: Word Cloud (full width)
            plot_wordcloud(df)
            
            st.markdown("---")
            st.markdown("---")
            
            # Summary Section
            show_summary(df)
            
            st.markdown("---")
            
            # Leaderboard
            show_leaderboard(df)
            
            st.markdown("---")
            
            # Footer
            st.markdown("""
            <div style="text-align: center; padding: 20px; color: white; font-size: 0.9rem;">
                <p>🎉 <strong>Analysis Complete!</strong> Share your findings with the group... or keep them secret 🤫</p>
                <p style="opacity: 0.7;">Built with Streamlit • Powered by Python • Fueled by curiosity ☕</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Empty State with visual guidance
        st.markdown("""
        <div style="text-align: center; padding: 50px; background: rgba(255,255,255,0.9); border-radius: 15px; margin-top: 50px;">
            <h2 style="color: #667eea;">👋 Welcome!</h2>
            <p style="font-size: 1.2rem; color: #555; margin: 20px 0;">
                Upload your WhatsApp chat export to unlock powerful insights
            </p>
            <p style="color: #777;">
                👈 Click "Browse files" in the sidebar to get started
            </p>
            <div style="margin-top: 30px; font-size: 3rem;">
                📊 📱 💬 📈
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Feature showcase
        st.markdown("## ✨ What You'll Discover")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 📊 Activity Patterns
            - Message volume rankings
            - Hourly activity heatmap
            - Weekly patterns
            - Response speed analysis
            """)
        
        with col2:
            st.markdown("""
            ### 💬 Communication Insights
            - Sentiment analysis
            - Word clouds
            - Topic trends
            - Conversation dynamics
            """)
        
        with col3:
            st.markdown("""
            ### 🏆 Fun Statistics
            - Top contributors
            - Night owls vs early birds
            - Most positive vibes
            - Comprehensive summary
            """)

if __name__ == "__main__":
    main()