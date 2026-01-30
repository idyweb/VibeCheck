import streamlit as st
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS
import warnings
from datetime import datetime
import zipfile
from collections import Counter
import emoji

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
    
    /* Metric styling */
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
    
    /* Badge styling */
    .badge {
        display: inline-block;
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: 700;
        margin: 5px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.2);
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- PARSING LOGIC ---
MESSAGE_PATTERN = r'.*?\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)$'

@st.cache_data
def load_data(uploaded_file):
    """Parses the uploaded WhatsApp file (TXT or ZIP) into a DataFrame."""
    try:
        # 1. HANDLE ZIP FILES
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file) as z:
                # Find the first .txt file inside the zip (usually _chat.txt)
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if not txt_files:
                    return pd.DataFrame() # No text file found
                
                # Read the file content
                with z.open(txt_files[0]) as f:
                    stringio = f.read().decode("utf-8")
        
        # 2. HANDLE TXT FILES
        else:
            stringio = uploaded_file.getvalue().decode("utf-8")
            
        lines = stringio.splitlines()
    except Exception as e:
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

def extract_emojis(text):
    """Extract all emojis from text. O(n) complexity."""
    return [c for c in str(text) if c in emoji.EMOJI_DATA]

# --- NEW ANALYSIS FUNCTIONS ---

def analyze_emojis(df):
    """Emoji analysis with top users and most popular emojis. O(n*m) where m is avg message length."""
    st.markdown("### 😂 Emoji Analysis - Who's the Emoji King/Queen?")
    
    with st.spinner("Counting emojis..."):
        # Extract emojis efficiently
        df['emojis'] = df['Message'].apply(extract_emojis)
        df['emoji_count'] = df['emojis'].apply(len)
        
        # Top emoji users
        top_authors = df['CleanAuthor'].value_counts().head(10).index
        emoji_users = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['emoji_count'].sum().sort_values(ascending=False)
        
        # Most popular emojis
        all_emojis = [e for emojis in df['emojis'] for e in emojis]
        emoji_counter = Counter(all_emojis)
        top_emojis = emoji_counter.most_common(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👑 Top Emoji Users")
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(x=emoji_users.values, y=emoji_users.index, hue=emoji_users.index, palette="viridis", ax=ax, legend=False)
            plt.xlabel("Total Emojis Used", fontsize=12, fontweight='bold')
            plt.ylabel("Participant", fontsize=12, fontweight='bold')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.markdown("#### 🌟 Most Popular Emojis")
            if top_emojis:
                emoji_html = "<div style='background: white; padding: 20px; border-radius: 10px; text-align: center;'>"
                for emoji_char, count in top_emojis[:10]:
                    emoji_html += f"<div style='display: inline-block; margin: 10px; text-align: center;'>"
                    emoji_html += f"<div style='font-size: 3rem;'>{emoji_char}</div>"
                    emoji_html += f"<div style='color: #333; font-weight: bold;'>{count:,}</div>"
                    emoji_html += "</div>"
                emoji_html += "</div>"
                st.markdown(emoji_html, unsafe_allow_html=True)
            else:
                st.info("No emojis found in this chat!")
        
        # Signature emojis
        st.markdown("#### ✨ Signature Emojis (Each Person's Favorite)")
        signature_emojis = {}
        for author in top_authors:
            author_emojis = [e for emojis in df[df['CleanAuthor'] == author]['emojis'] for e in emojis]
            if author_emojis:
                signature_emojis[author] = Counter(author_emojis).most_common(1)[0][0]
        
        if signature_emojis:
            sig_html = "<div style='background: white; padding: 20px; border-radius: 10px;'>"
            for author, emoji_char in signature_emojis.items():
                sig_html += f"<div style='padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 8px; color: #333;'>"
                sig_html += f"<strong>{author}</strong>: <span style='font-size: 2rem;'>{emoji_char}</span>"
                sig_html += "</div>"
            sig_html += "</div>"
            st.markdown(sig_html, unsafe_allow_html=True)
    
    return df

def detect_monologues(df):
    """Find who sends multiple messages in a row. O(n) complexity."""
    st.markdown("### 🗣️ Monologue Detector - The Serial Texters")
    
    # Efficient monologue detection using vectorized operations
    df = df.sort_values('DateTime').reset_index(drop=True)
    df['prev_author'] = df['Author'].shift(1)
    df['next_author'] = df['Author'].shift(-1)
    df['is_monologue'] = (df['Author'] == df['prev_author']) | (df['Author'] == df['next_author'])
    
    # Count consecutive messages
    monologue_data = []
    current_author = None
    current_count = 0
    
    for idx, row in df.iterrows():
        if row['Author'] == current_author:
            current_count += 1
        else:
            if current_count >= 3:  # 3+ consecutive messages
                monologue_data.append({'Author': current_author, 'Count': current_count})
            current_author = row['Author']
            current_count = 1
    
    if current_count >= 3:
        monologue_data.append({'Author': current_author, 'Count': current_count})
    
    if not monologue_data:
        st.info("No monologues detected! Everyone's pretty balanced.")
        return df
    
    monologue_df = pd.DataFrame(monologue_data)
    monologue_df['CleanAuthor'] = monologue_df['Author'].apply(clean_name)
    top_monologuers = monologue_df.groupby('CleanAuthor')['Count'].sum().sort_values(ascending=False).head(10)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=top_monologuers.values, y=top_monologuers.index, hue=top_monologuers.index, palette="Reds_r", ax=ax, legend=False)
    plt.xlabel("Total Consecutive Messages", fontsize=12, fontweight='bold')
    plt.ylabel("Participant", fontsize=12, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("🗣️ What does this mean?"):
        top_monologuer = top_monologuers.index[0]
        count = top_monologuers.values[0]
        st.write(f"**{top_monologuer}** loves to send multiple messages in a row! Total: **{count:,}** consecutive messages. 📱💨")
    
    return df

def analyze_conversation_roles(df):
    """Identify conversation starters and enders. O(n) complexity."""
    st.markdown("### 🎬 Conversation Starters vs Enders")
    
    df = df.sort_values('DateTime').reset_index(drop=True)
    df['time_since_last'] = df['DateTime'].diff().dt.total_seconds() / 3600  # hours
    
    # Starters: messages after 3+ hours of silence
    starters = df[df['time_since_last'] > 3].copy()
    starter_counts = starters['CleanAuthor'].value_counts().head(10)
    
    # Enders: messages before 3+ hours of silence
    df['time_to_next'] = df['DateTime'].shift(-1) - df['DateTime']
    df['time_to_next_hours'] = df['time_to_next'].dt.total_seconds() / 3600
    enders = df[df['time_to_next_hours'] > 3].copy()
    ender_counts = enders['CleanAuthor'].value_counts().head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚀 Conversation Starters")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x=starter_counts.values, y=starter_counts.index, hue=starter_counts.index, palette="Greens_r", ax=ax, legend=False)
        plt.xlabel("Times Started Conversation", fontsize=12, fontweight='bold')
        plt.ylabel("Participant", fontsize=12, fontweight='bold')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        st.markdown("#### 🛑 Conversation Enders")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x=ender_counts.values, y=ender_counts.index, hue=ender_counts.index, palette="Oranges_r", ax=ax, legend=False)
        plt.xlabel("Times Ended Conversation", fontsize=12, fontweight='bold')
        plt.ylabel("Participant", fontsize=12, fontweight='bold')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    
    with st.expander("🎬 What does this mean?"):
        if not starter_counts.empty:
            st.write(f"**{starter_counts.index[0]}** is the conversation igniter, breaking {starter_counts.values[0]} silences! 🔥")
        if not ender_counts.empty:
            st.write(f"**{ender_counts.index[0]}** has the last word {ender_counts.values[0]} times... conversation killer or mic drop master? 🎤⬇️")
    
    return df

def analyze_links(df):
    """Find who shares the most links. O(n*m) where m is avg message length."""
    st.markdown("### 🔗 Link Sharer - The Internet Scout")
    
    # Detect links efficiently
    df['has_link'] = df['Message'].str.contains(r'http|www\.', case=False, na=False, regex=True)
    df['link_count'] = df['Message'].str.count(r'http|www\.', flags=re.IGNORECASE)
    
    top_authors = df['CleanAuthor'].value_counts().head(10).index
    link_sharers = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['has_link'].sum().sort_values(ascending=False)
    
    if link_sharers.sum() == 0:
        st.info("No links shared in this chat!")
        return df
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=link_sharers.values, y=link_sharers.index, hue=link_sharers.index, palette="Blues_r", ax=ax, legend=False)
    plt.xlabel("Links Shared", fontsize=12, fontweight='bold')
    plt.ylabel("Participant", fontsize=12, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("🔗 What does this mean?"):
        top_linker = link_sharers.index[0]
        count = link_sharers.values[0]
        st.write(f"**{top_linker}** is the group's news source with **{count:,}** links shared! 📰")
    
    return df

def analyze_message_length(df):
    """Find who sends the longest messages. O(n) complexity."""
    st.markdown("### 📏 Message Length - Novels vs One-Liners")
    
    df['msg_length'] = df['Message'].str.len()
    
    top_authors = df['CleanAuthor'].value_counts().head(10).index
    avg_lengths = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['msg_length'].mean().sort_values(ascending=False)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=avg_lengths.values, y=avg_lengths.index, hue=avg_lengths.index, palette="Purples_r", ax=ax, legend=False)
    plt.xlabel("Average Message Length (characters)", fontsize=12, fontweight='bold')
    plt.ylabel("Participant", fontsize=12, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    # Find longest single message
    longest_msg = df.loc[df['msg_length'].idxmax()]
    longest_preview = longest_msg['Message'][:200] + "..." if len(longest_msg['Message']) > 200 else longest_msg['Message']
    
    with st.expander("📏 What does this mean?"):
        top_writer = avg_lengths.index[0]
        avg_len = avg_lengths.values[0]
        st.write(f"**{top_writer}** writes essays with an average of **{avg_len:.0f}** characters per message! 📚")
        st.write(f"\n**Longest message** ({longest_msg['msg_length']:,} chars) by **{clean_name(longest_msg['Author'])}**:")
        st.code(longest_preview)
    
    return df

def calculate_achievements(df):
    """Award achievement badges based on behavior. O(n) complexity."""
    st.markdown("### 🏆 Achievement Badges - Hall of Fame")
    
    achievements = {}
    
    # Night Owl - most messages after midnight
    df['hour'] = df['DateTime'].dt.hour
    night_msgs = df[df['hour'].between(0, 5)]
    if not night_msgs.empty:
        night_owl = night_msgs['CleanAuthor'].value_counts().index[0]
        achievements[night_owl] = achievements.get(night_owl, []) + ['🦉 Night Owl']
    
    # Early Bird - most messages before 7am
    early_msgs = df[df['hour'].between(5, 7)]
    if not early_msgs.empty:
        early_bird = early_msgs['CleanAuthor'].value_counts().index[0]
        achievements[early_bird] = achievements.get(early_bird, []) + ['🐦 Early Bird']
    
    # Comedian - highest emoji ratio
    if 'emoji_count' in df.columns:
        df['emoji_ratio'] = df['emoji_count'] / (df['Message'].str.len() + 1)
        top_authors = df['CleanAuthor'].value_counts().head(10).index
        emoji_ratio = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['emoji_ratio'].mean()
        if not emoji_ratio.empty:
            comedian = emoji_ratio.idxmax()
            achievements[comedian] = achievements.get(comedian, []) + ['😂 Comedian']
    
    # Professor - longest average message
    if 'msg_length' in df.columns:
        top_authors = df['CleanAuthor'].value_counts().head(10).index
        avg_length = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['msg_length'].mean()
        if not avg_length.empty:
            professor = avg_length.idxmax()
            achievements[professor] = achievements.get(professor, []) + ['👨‍🏫 Professor']
    
    # Lightning - fastest average response (if we have response time data)
    df_sorted = df.sort_values('DateTime')
    df_sorted['Prev_Author'] = df_sorted['Author'].shift(1)
    df_sorted['Time_Diff'] = df_sorted['DateTime'].diff().dt.total_seconds() / 60
    replies = df_sorted[(df_sorted['Author'] != df_sorted['Prev_Author']) & 
                        (df_sorted['Time_Diff'] < 720) & (df_sorted['Time_Diff'] > 0)]
    if not replies.empty:
        top_authors = df['CleanAuthor'].value_counts().head(10).index
        avg_response = replies[replies['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['Time_Diff'].mean()
        if not avg_response.empty:
            lightning = avg_response.idxmin()
            achievements[lightning] = achievements.get(lightning, []) + ['⚡ Lightning']
    
    # Chatterbox - most messages
    chatterbox = df['CleanAuthor'].value_counts().index[0]
    achievements[chatterbox] = achievements.get(chatterbox, []) + ['💬 Chatterbox']
    
    # Display achievements
    if achievements:
        for person, badges in achievements.items():
            badge_html = f"<div style='background: white; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 5px solid #FFD700;'>"
            badge_html += f"<div style='color: #1a1a1a; margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;'>{person}</div>"
            for badge in badges:
                badge_html += f"<span class='badge'>{badge}</span>"
            badge_html += "</div>"
            st.markdown(badge_html, unsafe_allow_html=True)
    
    return df

def you_vs_group_comparison(df):
    """Compare a specific user to group averages. O(n) complexity."""
    st.markdown("### 🤺 You vs The Group - Personal Report Card")
    
    user_name = st.text_input("Enter your name exactly as it appears in the chat:", key="user_comparison")
    
    if user_name:
        # Find closest match
        user_clean = clean_name(user_name)
        if user_clean not in df['CleanAuthor'].values:
            st.warning(f"❌ Couldn't find '{user_name}' in the chat. Try these: {', '.join(df['CleanAuthor'].unique()[:5])}")
            return df
        
        user_df = df[df['CleanAuthor'] == user_clean]
        
        # Calculate metrics
        metrics = {}
        
        # Message count
        user_msgs = len(user_df)
        group_avg_msgs = len(df) / df['Author'].nunique()
        metrics['Messages'] = {'You': user_msgs, 'Group Avg': group_avg_msgs, 'Unit': 'messages'}
        
        # Response time
        df_sorted = df.sort_values('DateTime')
        df_sorted['Prev_Author'] = df_sorted['Author'].shift(1)
        df_sorted['Time_Diff'] = df_sorted['DateTime'].diff().dt.total_seconds() / 60
        replies = df_sorted[(df_sorted['Author'] != df_sorted['Prev_Author']) & 
                           (df_sorted['Time_Diff'] < 720) & (df_sorted['Time_Diff'] > 0)]
        
        if not replies.empty:
            user_response = replies[replies['CleanAuthor'] == user_clean]['Time_Diff'].mean()
            group_response = replies['Time_Diff'].mean()
            metrics['Response Time'] = {'You': user_response, 'Group Avg': group_response, 'Unit': 'minutes'}
        
        # Sentiment
        if 'Sentiment' in df.columns:
            user_sentiment = user_df['Sentiment'].mean() * 100
            group_sentiment = df['Sentiment'].mean() * 100
            metrics['Positivity'] = {'You': user_sentiment, 'Group Avg': group_sentiment, 'Unit': '%'}
        
        # Message length
        if 'msg_length' in df.columns:
            user_length = user_df['msg_length'].mean()
            group_length = df['msg_length'].mean()
            metrics['Avg Message Length'] = {'You': user_length, 'Group Avg': group_length, 'Unit': 'chars'}
        
        # Emoji usage
        if 'emoji_count' in df.columns:
            user_emojis = user_df['emoji_count'].sum()
            group_emojis = df['emoji_count'].sum() / df['Author'].nunique()
            metrics['Total Emojis'] = {'You': user_emojis, 'Group Avg': group_emojis, 'Unit': 'emojis'}
        
        # Display comparison
        st.markdown(f"#### 📊 {user_clean}'s Performance")
        
        cols = st.columns(len(metrics))
        for i, (metric_name, values) in enumerate(metrics.items()):
            with cols[i]:
                your_val = values['You']
                group_val = values['Group Avg']
                
                if metric_name == 'Response Time':
                    delta = group_val - your_val  # Faster is better
                    delta_str = f"{abs(delta):.1f} min {'faster' if delta > 0 else 'slower'}"
                else:
                    delta = your_val - group_val
                    delta_str = f"{abs(delta):.1f} {'above' if delta > 0 else 'below'} avg"
                
                st.metric(
                    label=metric_name,
                    value=f"{your_val:.1f} {values['Unit']}",
                    delta=delta_str
                )
        
        # Radar chart would go here if we had plotly
        st.success(f"✨ {user_clean}, you're {'above' if user_msgs > group_avg_msgs else 'below'} average in activity!")
    
    return df

# --- EXISTING VISUALIZATION FUNCTIONS ---
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
    
    for i, (author, count) in enumerate(top5.items()):
        percentage = (count / len(df)) * 100
        clean_author = clean_name(author)
        
        html_card = f"""
        <div style="background: #ffffff; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 5px solid #667eea; box-shadow: 0 3px 8px rgba(0,0,0,0.1); display: flex; align-items: center;">
            <div style="font-size: 2.5rem; margin-right: 20px; min-width: 60px; text-align: center;">{medals[i]}</div>
            <div style="flex-grow: 1;">
                <div style="color: #1a1a1a; margin: 0; font-size: 1.4rem; font-weight: 700; margin-bottom: 5px;">{clean_author}</div>
                <p style="color: #333333; margin: 0; font-size: 1rem;">
                    <strong style="color: #1a1a1a;">{count:,}</strong> messages • <span style="color: #555555;">{percentage:.1f}%</span>
                </p>
            </div>
            <div style="font-size: 2rem; font-weight: bold; color: #667eea; min-width: 60px; text-align: center;">#{i+1}</div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)

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
        uploaded_file = st.file_uploader("Choose your _chat.txt or .zip file", type=["txt", "zip"], help="Export your WhatsApp chat without media")
        
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
            st.info("💡 Tip: The file should look like `WhatsApp Chat with XYZ.txt` or a `.zip` containing it.")
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
            
            # NEW FEATURES SECTION
            st.markdown("## 🎮 Advanced Analytics")
            
            # Emoji Analysis
            df = analyze_emojis(df)
            
            st.markdown("---")
            
            # Monologue Detector
            df = detect_monologues(df)
            
            st.markdown("---")
            
            # Conversation Roles
            df = analyze_conversation_roles(df)
            
            st.markdown("---")
            
            # Message Length
            df = analyze_message_length(df)
            
            st.markdown("---")
            
            # Link Sharer
            df = analyze_links(df)
            
            st.markdown("---")
            
            # Achievement Badges
            df = calculate_achievements(df)
            
            st.markdown("---")
            
            # You vs Group
            df = you_vs_group_comparison(df)
            
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
        
        st.markdown("---")
        
        # NEW FEATURES PREVIEW
        st.markdown("## 🎮 NEW: Advanced Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 😂 Emoji Analysis
            - Top emoji users
            - Most popular emojis
            - Signature emojis
            - Emoji-to-text ratios
            """)
        
        with col2:
            st.markdown("""
            ### 🎬 Behavior Insights
            - Monologue detector
            - Conversation starters/enders
            - Link sharers
            - Message length analysis
            """)
        
        with col3:
            st.markdown("""
            ### 🏆 Gamification
            - Achievement badges
            - You vs Group comparison
            - Personal report card
            """)

if __name__ == "__main__":
    main()