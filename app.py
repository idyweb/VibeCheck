import streamlit as st
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS
import warnings

# --- CONFIGURATION & SETUP ---
warnings.filterwarnings("ignore")
st.set_page_config(
    page_title="WhatsApp Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    h1 { color: #1E88E5; font-family: 'Helvetica Neue', sans-serif; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
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
        return pd.DataFrame() # Return empty on decode error

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
    
    # Robust Date Parsing: Try day-first, fall back to standard
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
    return (cleaned[:10] + "..") if len(cleaned) > 10 else (cleaned or "Unknown")

def get_sentiment(text):
    """Returns a polarity score between -1 (Negative) and 1 (Positive)."""
    return TextBlob(str(text)).sentiment.polarity

# --- VISUALIZATION FUNCTIONS ---
def plot_volume(df):
    st.subheader("📣 Message Volume")
    fig, ax = plt.subplots(figsize=(8, 4))
    top_vol = df['CleanAuthor'].value_counts().head(10)
    sns.barplot(x=top_vol.index, y=top_vol.values, hue=top_vol.index, palette="viridis", ax=ax, legend=False)
    plt.xticks(rotation=45)
    plt.ylabel("Total Messages")
    st.pyplot(fig)

def plot_response_time(df):
    st.subheader("⚡ Avg Response Time (Mins)")
    
    # Calculate response times
    df = df.sort_values('DateTime')
    df['Prev_Author'] = df['Author'].shift(1)
    df['Time_Diff'] = df['DateTime'].diff().dt.total_seconds() / 60
    
    # Filter: Replies within 12 hours, ignoring self-replies
    replies = df[(df['Author'] != df['Prev_Author']) & (df['Time_Diff'] < 720)]
    
    top_authors = df['CleanAuthor'].value_counts().head(10).index
    replies = replies[replies['CleanAuthor'].isin(top_authors)]
    
    if replies.empty:
        st.info("Not enough conversation data for response times.")
        return

    avg_time = replies.groupby('CleanAuthor')['Time_Diff'].mean().sort_values()
    
    fig, ax = plt.subplots(figsize=(8, 4))
    avg_time.plot(kind='bar', color='#2a9d8f', ax=ax)
    plt.xticks(rotation=45)
    plt.ylabel("Minutes")
    st.pyplot(fig)

def plot_wordcloud(df):
    st.subheader("☁️ Word Cloud")
    text = " ".join(msg for msg in df.Message if isinstance(msg, str))
    stopwords = set(STOPWORDS)
    stopwords.update(["media", "omitted", "image", "video", "sticker", "message", "deleted", "null", "https", "www"])
    
    if len(text) < 100:
        st.warning("Not enough text data for a word cloud.")
        return

    wordcloud = WordCloud(width=800, height=400, background_color='white', 
                          stopwords=stopwords, colormap='viridis').generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

def plot_hourly_activity(df):
    st.subheader("🕰️ Hourly Activity")
    df['Hour'] = df['DateTime'].dt.hour
    hour_counts = df['Hour'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(10, 3))
    sns.lineplot(x=hour_counts.index, y=hour_counts.values, linewidth=3, color='#440154', ax=ax)
    ax.fill_between(hour_counts.index, hour_counts.values, color='#440154', alpha=0.1)
    ax.set_xticks(range(0, 24))
    ax.set_xlim(0, 23)
    ax.grid(True, linestyle='--', alpha=0.3)
    st.pyplot(fig)

# --- MAIN APP LAYOUT ---
def main():
    st.title("📊 Chat Analyzer Pro")
    st.markdown("Upload your WhatsApp export (`_chat.txt`) to unlock insights.")
    
    with st.sidebar:
        st.header("Upload & Settings")
        uploaded_file = st.file_uploader("Choose file", type="txt")
        st.markdown("---")
        st.markdown("**Privacy Note:** Data is processed in memory and never stored.")

    if uploaded_file:
        with st.spinner('Parsing chat logs...'):
            df = load_data(uploaded_file)

        if df.empty:
            st.error("⚠️ Error: Could not parse file. Ensure it is an iOS export without media.")
        else:
            # Preprocess names
            df['CleanAuthor'] = df['Author'].apply(clean_name)
            
            # Auto-Detect Mode
            unique_authors = df['Author'].nunique()
            mode = "Group" if unique_authors > 2 else "Couple"
            
            # Dashboard Header
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Type", f"{mode} Chat")
            col2.metric("Total Messages", f"{len(df):,}")
            col3.metric("Participants", unique_authors)
            
            days = (df['DateTime'].max() - df['DateTime'].min()).days or 1
            col4.metric("Duration", f"{days} Days")
            
            st.markdown("---")

            # Main Visuals
            row1_1, row1_2 = st.columns(2)
            with row1_1: plot_volume(df)
            with row1_2: plot_response_time(df)
            
            st.markdown("---")
            plot_hourly_activity(df)
            
            st.markdown("---")
            plot_wordcloud(df)

            # Optional Sentiment Analysis
            if st.checkbox("🔍 Run Advanced Sentiment Analysis (May take a moment)"):
                st.markdown("---")
                st.subheader("❤️ Vibe Check (Sentiment)")
                with st.spinner("Analyzing text sentiment..."):
                    df['Sentiment'] = df.apply(lambda row: get_sentiment(row['Message']) 
                                             if "omitted" not in str(row['Message']) else 0, axis=1)
                    
                    top_authors = df['CleanAuthor'].value_counts().head(10).index
                    sentiment_df = df[df['CleanAuthor'].isin(top_authors)]
                    avg_sentiment = sentiment_df.groupby('CleanAuthor')['Sentiment'].mean()
                    
                    fig, ax = plt.subplots(figsize=(8, 4))
                    colors = sns.color_palette("viridis", len(avg_sentiment))
                    (avg_sentiment * 100).plot(kind='bar', color=colors, ax=ax)
                    ax.axhline(0, color='black', linewidth=0.8)
                    plt.ylabel("Positivity Score (%)")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

    else:
        # Empty State
        st.info("👈 Upload your `_chat.txt` file in the sidebar to begin.")

if __name__ == "__main__":
    main()