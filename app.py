import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import warnings
import zipfile

# Import from our modular library
from src.parser import parse_chat_content
from src.analyzers import ChatAnalyzer
from src.utils import clean_name

# --- CONFIGURATION & SETUP ---
warnings.filterwarnings("ignore")
st.set_page_config(
    page_title="WhatsApp Vibe Checker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional, READABLE look
CUSTOM_CSS = """
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
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- DATA LOADING ---
@st.cache_data
def load_data(uploaded_file):
    """Load and parse WhatsApp chat file using the modular parser."""
    try:
        # Handle ZIP files
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file) as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if not txt_files:
                    return None
                with z.open(txt_files[0]) as f:
                    content = f.read().decode("utf-8")
        else:
            content = uploaded_file.getvalue().decode("utf-8")
        
        df = parse_chat_content(content)
        
        if df.empty:
            return None
        
        # Add clean author names
        df['CleanAuthor'] = df['Author'].apply(clean_name)
        return df
        
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None


# --- VISUALIZATION FUNCTIONS ---
def plot_bar_chart(data: list, x_key: str, y_key: str, title: str, 
                   xlabel: str, ylabel: str, palette: str = "viridis"):
    """Generic bar chart plotter."""
    df = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df, x=x_key, y=y_key, hue=x_key, palette=palette, ax=ax, legend=False)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(xlabel, fontsize=12, fontweight='bold')
    plt.ylabel(ylabel, fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)


def plot_volume(analyzer: ChatAnalyzer):
    """Plot message volume chart."""
    st.markdown("### 📣 Message Volume - Who's the Chatterbox?")
    data = analyzer.analyze_volume(limit=10)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    names = [d['name'] for d in data['data']]
    values = [d['messages'] for d in data['data']]
    
    sns.barplot(x=names, y=values, hue=names, palette="viridis", ax=ax, legend=False)
    plt.ylabel("Total Messages", fontsize=12, fontweight='bold')
    plt.xlabel("Participant", fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("📊 What does this mean?"):
        if data['top_contributor']:
            top = data['data'][0]
            pct = (top['messages'] / data['total_messages']) * 100
            st.write(f"**{top['name']}** is the most active with **{top['messages']:,}** messages! That's {pct:.1f}% of all messages.")


def plot_sentiment(analyzer: ChatAnalyzer):
    """Plot sentiment analysis chart."""
    st.markdown("### ❤️ Vibe Check - Positivity Score")
    
    with st.spinner("Analyzing text sentiment..."):
        data = analyzer.analyze_sentiment(limit=10)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    names = [d['name'] for d in data['data']]
    values = [d['sentiment'] for d in data['data']]
    colors = ['#2ecc71' if v > 0 else '#e74c3c' for v in values]
    
    df_plot = pd.DataFrame({'name': names, 'sentiment': values})
    df_plot.set_index('name')['sentiment'].plot(kind='bar', color=colors, ax=ax)
    ax.axhline(0, color='black', linewidth=1.5, linestyle='--', alpha=0.5)
    plt.ylabel("Positivity Score (%)", fontsize=12, fontweight='bold')
    plt.xlabel("Participant", fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("😊 What does this mean?"):
        if data['most_positive']:
            st.write(f"**{data['most_positive']}** brings the most positive energy! 🌟")
            st.write("Positive scores mean upbeat messages, negative means more critical/sarcastic tones.")


def plot_response_time(analyzer: ChatAnalyzer):
    """Plot response time chart."""
    st.markdown("### ⚡ Response Speed - Who Replies Fastest?")
    data = analyzer.analyze_response_time(limit=10)
    
    if not data['data']:
        st.info("⏳ Not enough conversation data to calculate response times.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 5))
    names = [d['name'] for d in data['data']]
    values = [d['response_time'] for d in data['data']]
    
    df_plot = pd.DataFrame({'name': names, 'time': values})
    df_plot.set_index('name')['time'].plot(kind='bar', color='#3498db', ax=ax)
    plt.ylabel("Average Minutes", fontsize=12, fontweight='bold')
    plt.xlabel("Participant", fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("⚡ What does this mean?"):
        if data['fastest_responder']:
            st.write(f"**{data['fastest_responder']}** is the speed demon! 🏃‍♂️💨")


def plot_hourly_activity(analyzer: ChatAnalyzer):
    """Plot hourly activity chart."""
    st.markdown("### 🕰️ Hourly Activity - Night Owls vs Early Birds")
    data = analyzer.analyze_hourly_activity()
    
    hours = [d['hour'] for d in data['data']]
    values = [d['messages'] for d in data['data']]
    
    fig, ax = plt.subplots(figsize=(12, 4))
    sns.lineplot(x=hours, y=values, linewidth=3, color='#9b59b6', ax=ax, marker='o')
    ax.fill_between(hours, values, color='#9b59b6', alpha=0.2)
    ax.set_xticks(range(0, 24))
    ax.set_xlim(0, 23)
    ax.set_xlabel("Hour of Day (0 = Midnight, 23 = 11PM)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Message Count", fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("🦉 What does this mean?"):
        st.write(f"Peak activity is at **{data['peak_hour_label']}**! That's when this chat is most alive. 🔥")


def plot_weekly_activity(analyzer: ChatAnalyzer):
    """Plot weekly activity chart."""
    st.markdown("### 📅 Weekly Pattern - Busiest Days")
    data = analyzer.analyze_weekly_activity()
    
    days = [d['day'] for d in data['data']]
    values = [d['messages'] for d in data['data']]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=days, y=values, hue=days, palette="viridis", ax=ax, legend=False)
    plt.ylabel("Message Count", fontsize=12, fontweight='bold')
    plt.xlabel("Day of Week", fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("📅 What does this mean?"):
        st.write(f"**{data['busiest_day']}** is the busiest day! The chat goes wild on this day. 🎉")


def plot_wordcloud(df):
    """Plot word cloud."""
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


def show_emojis(analyzer: ChatAnalyzer):
    """Show emoji analysis."""
    st.markdown("### 😂 Emoji Analysis - Who's the Emoji King/Queen?")
    data = analyzer.analyze_emojis(limit=10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👑 Top Emoji Users")
        if data['top_users']:
            fig, ax = plt.subplots(figsize=(8, 5))
            names = [d['name'] for d in data['top_users']]
            values = [d['emoji_count'] for d in data['top_users']]
            sns.barplot(x=values, y=names, hue=names, palette="viridis", ax=ax, legend=False)
            plt.xlabel("Total Emojis Used", fontsize=12, fontweight='bold')
            plt.ylabel("Participant", fontsize=12, fontweight='bold')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
    
    with col2:
        st.markdown("#### 🌟 Most Popular Emojis")
        if data['top_emojis']:
            emoji_html = "<div style='background: white; padding: 20px; border-radius: 10px; text-align: center;'>"
            for item in data['top_emojis'][:10]:
                emoji_html += f"<div style='display: inline-block; margin: 10px; text-align: center;'>"
                emoji_html += f"<div style='font-size: 3rem;'>{item['emoji']}</div>"
                emoji_html += f"<div style='color: #333; font-weight: bold;'>{item['count']:,}</div>"
                emoji_html += "</div>"
            emoji_html += "</div>"
            st.markdown(emoji_html, unsafe_allow_html=True)

    # Signature emojis
    st.markdown("#### ✨ Signature Emojis (Each Person's Favorite)")
    if data['author_summaries']:
        sig_html = "<div style='background: white; padding: 20px; border-radius: 10px;'>"
        for author in data['author_summaries']:
            sig_html += f"<div style='padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 8px; color: #333;'>"
            sig_html += f"<strong>{author['name']}</strong>: <span style='font-size: 2rem;'>{author['primary_emoji']}</span>"
            sig_html += "</div>"
        sig_html += "</div>"
        st.markdown(sig_html, unsafe_allow_html=True)


def show_monologues(analyzer: ChatAnalyzer):
    """Show monologue detection analysis."""
    st.markdown("### 🗣️ Monologue Detector - The Serial Texters")
    data = analyzer.detect_monologues()
    
    if not data['data']:
        st.info("No monologues detected! Everyone's pretty balanced.")
        return

    df_plot = pd.DataFrame(data['data'])
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_plot, x='consecutive_messages', y='name', hue='name', palette="Reds_r", ax=ax, legend=False)
    plt.xlabel("Total Consecutive Messages", fontsize=12, fontweight='bold')
    plt.ylabel("Participant", fontsize=12, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("🗣️ What does this mean?"):
        st.write(data['insight'])


def show_roles(analyzer: ChatAnalyzer):
    """Show conversation starters and enders."""
    st.markdown("### 🎬 Conversation Starters vs Enders")
    data = analyzer.analyze_conversation_roles()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚀 Conversation Starters")
        if data['starters']:
            df_s = pd.DataFrame(data['starters'])
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=df_s, x='count', y='name', hue='name', palette="Greens_r", ax=ax, legend=False)
            plt.xlabel("Times Started Conversation", fontsize=12, fontweight='bold')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
    
    with col2:
        st.markdown("#### 🛑 Conversation Enders")
        if data['enders']:
            df_e = pd.DataFrame(data['enders'])
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=df_e, x='count', y='name', hue='name', palette="Oranges_r", ax=ax, legend=False)
            plt.xlabel("Times Ended Conversation", fontsize=12, fontweight='bold')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
    
    with st.expander("🎬 What does this mean?"):
        st.write(data['insight'])


def show_links(analyzer: ChatAnalyzer):
    """Show link sharing analysis."""
    st.markdown("### 🔗 Link Sharer - The Internet Scout")
    data = analyzer.analyze_links()
    
    if not data['data']:
        st.info("No links shared in this chat!")
        return

    df_plot = pd.DataFrame(data['data'])
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_plot, x='links', y='name', hue='name', palette="Blues_r", ax=ax, legend=False)
    plt.xlabel("Links Shared", fontsize=12, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("🔗 What does this mean?"):
        st.write(data['insight'])


def show_message_lengths(analyzer: ChatAnalyzer):
    """Show message length analysis."""
    st.markdown("### 📏 Message Length - Novels vs One-Liners")
    data = analyzer.analyze_message_length()
    
    if not data['data']:
        return

    df_plot = pd.DataFrame(data['data'])
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_plot, x='avg_length', y='name', hue='name', palette="Purples_r", ax=ax, legend=False)
    plt.xlabel("Average Message Length (characters)", fontsize=12, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    with st.expander("📏 What does this mean?"):
        st.write(data['insight'])
        lm = data['longest_message']
        st.write(f"\n**Longest message** ({lm['length']:,} chars) by **{lm['author']}**:")
        st.code(lm['preview'])


def show_comparison(analyzer: ChatAnalyzer):
    """Show personal comparison report card."""
    st.markdown("### 🤺 You vs The Group - Personal Report Card")
    
    user_name = st.text_input("Enter your name exactly as it appears in the chat:", key="user_comparison")
    
    if user_name:
        data = analyzer.compare_user_to_group(user_name)
        if not data:
            st.warning(f"❌ Couldn't find '{user_name}' in the chat.")
            return

        st.markdown(f"#### 📊 {data['user_name']}'s Performance")
        
        # Mapping for display
        metrics = {
            "Messages": data['messages'],
            "Avg Msg Length": data['avg_message_length'],
            "Response Time": data['response_time'],
            "Positivity": data['positivity'],
            "Total Emojis": data['emojis']
        }
        
        cols = st.columns(len(metrics))
        for i, (name, val) in enumerate(metrics.items()):
            with cols[i]:
                user_val = val['user']
                group_avg = val['group_avg']
                
                if name == "Response Time":
                    delta = group_avg - user_val # Lower is better
                    delta_str = f"{abs(delta):.1f} min {'faster' if delta > 0 else 'slower'}"
                else:
                    delta = user_val - group_avg
                    delta_str = f"{abs(delta):.1f} {'above' if delta > 0 else 'below'} avg"
                
                st.metric(label=name, value=f"{user_val:.1f}", delta=delta_str)
        
        st.success(f"✨ {data['user_name']}, you're {'above' if data['messages']['user'] > data['messages']['group_avg'] else 'below'} average in activity!")


def show_achievements(analyzer: ChatAnalyzer):
    """Show achievement badges."""
    st.markdown("### 🏆 Achievement Badges - Hall of Fame")
    data = analyzer.calculate_achievements()
    
    if data['achievements']:
        for item in data['achievements']:
            badge_html = f"<div style='background: white; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 5px solid #FFD700;'>"
            badge_html += f"<div style='color: #1a1a1a; margin: 0 0 10px 0; font-size: 1.3rem; font-weight: 700;'>{item['name']}</div>"
            for badge in item['badges']:
                badge_html += f"<span class='badge'>{badge}</span>"
            badge_html += "</div>"
            st.markdown(badge_html, unsafe_allow_html=True)


def show_leaderboard(analyzer: ChatAnalyzer):
    """Show top contributors leaderboard."""
    st.markdown("## 🏆 Hall of Fame - Top 5 Contributors")
    data = analyzer.get_leaderboard(limit=5)
    medals = ['🥇', '🥈', '🥉', '🏅', '🎖️']
    
    for i, item in enumerate(data['data']):
        html_card = f"""
        <div style="background: #ffffff; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 5px solid #667eea; box-shadow: 0 3px 8px rgba(0,0,0,0.1); display: flex; align-items: center;">
            <div style="font-size: 2.5rem; margin-right: 20px; min-width: 60px; text-align: center;">{medals[i]}</div>
            <div style="flex-grow: 1;">
                <div style="color: #1a1a1a; margin: 0; font-size: 1.4rem; font-weight: 700; margin-bottom: 5px;">{item['name']}</div>
                <p style="color: #333333; margin: 0; font-size: 1rem;">
                    <strong style="color: #1a1a1a;">{item['messages']:,}</strong> messages • <span style="color: #555555;">{item['percentage']:.1f}%</span>
                </p>
            </div>
            <div style="font-size: 2rem; font-weight: bold; color: #667eea; min-width: 60px; text-align: center;">#{item['rank']}</div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)


def show_summary(analyzer: ChatAnalyzer):
    """Show executive summary."""
    st.markdown("## 📊 Executive Summary")
    data = analyzer.get_summary()
    
    from datetime import datetime
    start_date = datetime.fromisoformat(data['start_date']).strftime('%B %d, %Y')
    end_date = datetime.fromisoformat(data['end_date']).strftime('%B %d, %Y')
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.2);">
        <h2 style="margin-top: 0; color: white;">📈 Chat Statistics</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h4 style="color: #667eea; margin-bottom: 10px;">📅 Timeframe</h4>
            <p style="font-size: 1rem; margin: 5px 0; color: #333;"><strong>{start_date}</strong></p>
            <p style="color: #777;">to</p>
            <p style="font-size: 1rem; margin: 5px 0; color: #333;"><strong>{end_date}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h4 style="color: #667eea; margin-bottom: 10px;">💬 Messages</h4>
            <p style="font-size: 2rem; margin: 10px 0; color: #333; font-weight: bold;">{data['total_messages']:,}</p>
            <p style="color: #777;">{data['messages_per_day']:.0f} per day</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h4 style="color: #667eea; margin-bottom: 10px;">👥 Participants</h4>
            <p style="font-size: 2rem; margin: 10px 0; color: #333; font-weight: bold;">{data['unique_participants']}</p>
            <p style="color: #777;">unique people</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h4 style="color: #667eea; margin-bottom: 10px;">🏆 Top Contributor</h4>
            <p style="font-size: 1.5rem; margin: 10px 0; color: #333; font-weight: bold;">{data['top_contributor']['name']}</p>
            <p style="color: #777;">{data['top_contributor']['percentage']:.1f}% of messages</p>
        </div>
        """, unsafe_allow_html=True)

    # Key Insights Section
    if data['key_insights']:
        insight_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 12px; margin-top: 20px; color: white;">
            <h3 style="margin-top: 0; color: white;">🎯 Key Insights</h3>
            <ul style="font-size: 1.1rem; line-height: 2;">
        """
        for insight in data['key_insights']:
            insight_html += f"<li>{insight}</li>"
        insight_html += "</ul></div>"
        st.markdown(insight_html, unsafe_allow_html=True)


# --- MAIN APP ---
def main():
    st.title("📊 WhatsApp Vibe Checker")
    st.markdown("### *Uncover the secrets hidden in your group chat* 🕵️‍♂️")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📤 Upload Your Chat")
        st.markdown("---")
        uploaded_file = st.file_uploader(
            "Choose your _chat.txt or .zip file", 
            type=["txt", "zip"], 
            help="Export your WhatsApp chat without media"
        )
        
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
        st.info("Your data is processed in memory and never stored.")
        
        st.markdown("---")
        st.markdown("### 🚀 API Mode")
        st.info("Run `uvicorn api.main:app --reload` for the React/Recharts API!")
        
        st.markdown("---")
        st.markdown("Made with ❤️ by Idy")

    if uploaded_file:
        with st.spinner('🔍 Parsing your chat history...'):
            df = load_data(uploaded_file)

        if df is None:
            st.error("⚠️ **Oops!** Couldn't parse the file.")
            st.info("💡 Tip: Make sure it's a WhatsApp export file.")
        else:
            # Create analyzer
            analyzer = ChatAnalyzer(df)
            summary = analyzer.get_summary()
            
            # Mode detection
            mode = "Group" if summary['unique_participants'] > 2 else "Couple"
            mode_emoji = "👥" if mode == "Group" else "💑"
            
            st.success(f"✅ Successfully loaded **{len(df):,}** messages! Let's dive in... 🏊‍♂️")
            
            # Dashboard Header
            st.markdown("---")
            st.markdown(f"## {mode_emoji} {mode} Chat Dashboard")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Chat Type", f"{mode_emoji} {mode}")
            col2.metric("Total Messages", f"{summary['total_messages']:,}")
            col3.metric("Participants", f"{summary['unique_participants']} 👤")
            col4.metric("Daily Average", f"{summary['messages_per_day']:.0f} 💬")
            
            st.markdown("---")
            
            # Analytics
            st.markdown("## 📈 Deep Dive Analytics")
            
            col1, col2 = st.columns(2)
            with col1:
                plot_volume(analyzer)
            with col2:
                plot_response_time(analyzer)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                plot_sentiment(analyzer)
            with col2:
                plot_weekly_activity(analyzer)
            
            st.markdown("---")
            plot_hourly_activity(analyzer)
            
            st.markdown("---")
            plot_wordcloud(df)
            
            st.markdown("---")
            st.markdown("## 🎮 Advanced Analytics")
            
            show_emojis(analyzer)
            st.markdown("---")
            show_monologues(analyzer)
            st.markdown("---")
            show_roles(analyzer)
            st.markdown("---")
            show_links(analyzer)
            st.markdown("---")
            show_message_lengths(analyzer)
            st.markdown("---")
            show_achievements(analyzer)
            st.markdown("---")
            show_comparison(analyzer)
            st.markdown("---")
            show_summary(analyzer)
            st.markdown("---")
            show_leaderboard(analyzer)
            
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; padding: 20px; color: white; font-size: 0.9rem;">
                <p>🎉 <strong>Analysis Complete!</strong> Share your findings with the group... or keep them secret 🤫</p>
                <p style="opacity: 0.7;">Built with Streamlit • Powered by Python • Fueled by curiosity ☕</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Empty state
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
            - Emoji analysis
            - Conversation dynamics
            """)
        
        with col3:
            st.markdown("""
            ### 🏆 Fun Statistics
            - Top contributors
            - Night owls vs early birds
            - Achievement badges
            - Comprehensive summary
            """)


if __name__ == "__main__":
    main()