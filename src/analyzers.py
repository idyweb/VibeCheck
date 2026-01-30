"""
WhatsApp Chat Analyzers Module

Pure analysis functions that return data dictionaries (no UI code).
Designed to work with both Streamlit and FastAPI.

All methods follow the pattern:
- Input: DataFrame from parser
- Output: Dictionary with 'data' key for charts + metadata
"""

from collections import Counter
from typing import Any
import pandas as pd

from src.utils import clean_name, get_sentiment, extract_emojis, has_link, is_media_message


class ChatAnalyzer:
    """
    Analyzes WhatsApp chat data and returns structured results.
    
    All analysis methods return dictionaries compatible with Recharts.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with parsed chat DataFrame.
        
        Args:
            df: DataFrame from parse_chat_file() with DateTime column
        """
        self.df = df.copy()
        self.df['CleanAuthor'] = self.df['Author'].apply(clean_name)
        self._precompute()
    
    def _precompute(self) -> None:
        """Pre-compute common columns for efficiency."""
        self.df['Hour'] = self.df['DateTime'].dt.hour
        self.df['Day'] = self.df['DateTime'].dt.day_name()
        self.df['msg_length'] = self.df['Message'].str.len()
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get executive summary of the chat.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Returns:
            Dictionary with chat statistics
        """
        df = self.df
        start_date = df['DateTime'].min()
        end_date = df['DateTime'].max()
        days = (end_date - start_date).days or 1
        
        top_author = df['Author'].value_counts().index[0]
        top_author_count = df['Author'].value_counts().values[0]
        peak_hour = df['Hour'].value_counts().idxmax()
        busiest_day = df['Day'].value_counts().idxmax()
        
        # Key Insights (Narrative text)
        insights = [
            f"🏆 {clean_name(top_author)} dominated the chat with {top_author_count:,} messages ({round(top_author_count/len(df)*100, 1)}%)",
            f"⏰ Peak activity happens around {peak_hour:02d}:00 - prime chatting time!",
            f"📅 {busiest_day} is when things get wild with the most messages 🎉",
            f"📆 This chat lasted {days} days - that's {round(days/365, 1)} years of memories!"
        ]
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_messages": len(df),
            "total_days": days,
            "messages_per_day": round(len(df) / days, 1),
            "unique_participants": df['Author'].nunique(),
            "top_contributor": {
                "name": clean_name(top_author),
                "messages": int(top_author_count),
                "percentage": round((top_author_count / len(df)) * 100, 1)
            },
            "peak_hour": int(peak_hour),
            "busiest_day": busiest_day,
            "key_insights": insights
        }
    
    def analyze_volume(self, limit: int = 10) -> dict[str, Any]:
        """
        Analyze message volume per author.
        
        Time Complexity: O(n)
        Space Complexity: O(k) where k is unique authors
        
        Args:
            limit: Max authors to return (default 10)
            
        Returns:
            Recharts-compatible data
        """
        volume = self.df['CleanAuthor'].value_counts().head(limit)
        total = len(self.df)
        
        # Generate insight text
        insight = None
        if not volume.empty:
            top_name = volume.index[0]
            top_count = int(volume.values[0])
            pct = round((top_count / total) * 100, 1)
            insight = f"{top_name} is the most active with {top_count:,} messages! That's {pct}% of all messages."
        
        return {
            "data": [
                {"name": name, "messages": int(count)}
                for name, count in volume.items()
            ],
            "total_messages": total,
            "top_contributor": volume.index[0] if not volume.empty else None,
            "insight": insight
        }
    
    def analyze_sentiment(self, limit: int = 10) -> dict[str, Any]:
        """
        Analyze sentiment/positivity per author.
        
        Time Complexity: O(n*m) where m is avg message length
        Space Complexity: O(n)
        
        Args:
            limit: Max authors to return
            
        Returns:
            Recharts-compatible sentiment data
        """
        df = self.df.copy()
        
        # Calculate sentiment, skip media messages
        df['Sentiment'] = df.apply(
            lambda row: get_sentiment(row['Message']) 
            if not is_media_message(row['Message']) else 0,
            axis=1
        )
        
        top_authors = df['CleanAuthor'].value_counts().head(limit).index
        sentiment_df = df[df['CleanAuthor'].isin(top_authors)]
        avg_sentiment = sentiment_df.groupby('CleanAuthor')['Sentiment'].mean()
        avg_sentiment = avg_sentiment.sort_values(ascending=False)
        
        # Generate insight text
        insight = None
        if not avg_sentiment.empty:
            most_positive = avg_sentiment.index[0]
            score = round(avg_sentiment.values[0] * 100, 1)
            insight = f"{most_positive} brings the most positive energy with a {score}% vibe score! 🌟 Positive scores mean upbeat messages, negative means more critical/sarcastic tones."
        
        return {
            "data": [
                {
                    "name": name, 
                    "sentiment": round(score * 100, 1),
                    "category": "positive" if score > 0 else "negative"
                }
                for name, score in avg_sentiment.items()
            ],
            "most_positive": avg_sentiment.index[0] if not avg_sentiment.empty else None,
            "average_sentiment": round(df['Sentiment'].mean() * 100, 1),
            "insight": insight
        }
    
    def analyze_response_time(self, limit: int = 10) -> dict[str, Any]:
        """
        Analyze average response time per author.
        
        Time Complexity: O(n log n) for sorting
        Space Complexity: O(n)
        
        Args:
            limit: Max authors to return
            
        Returns:
            Recharts-compatible response time data
        """
        df = self.df.sort_values('DateTime').copy()
        df['Prev_Author'] = df['Author'].shift(1)
        df['Time_Diff'] = df['DateTime'].diff().dt.total_seconds() / 60  # minutes
        
        # Only consider replies (different author, within 12 hours, > 0)
        replies = df[
            (df['Author'] != df['Prev_Author']) & 
            (df['Time_Diff'] < 720) & 
            (df['Time_Diff'] > 0)
        ]
        
        if replies.empty:
            return {"data": [], "fastest_responder": None, "average_response_time": None, "insight": "Not enough conversation data to calculate response times."}
        
        top_authors = self.df['CleanAuthor'].value_counts().head(limit).index
        replies = replies[replies['CleanAuthor'].isin(top_authors)]
        
        avg_time = replies.groupby('CleanAuthor')['Time_Diff'].mean().sort_values()
        
        # Generate insight text
        insight = None
        if not avg_time.empty:
            fastest = avg_time.index[0]
            time_val = round(avg_time.values[0], 1)
            insight = f"{fastest} is the speed demon, replying in an average of {time_val} minutes! 🏃‍♂️💨"
        
        return {
            "data": [
                {"name": name, "response_time": round(time, 1)}
                for name, time in avg_time.items()
            ],
            "fastest_responder": avg_time.index[0] if not avg_time.empty else None,
            "average_response_time": round(replies['Time_Diff'].mean(), 1),
            "insight": insight
        }
    
    def analyze_hourly_activity(self) -> dict[str, Any]:
        """
        Analyze message activity by hour of day.
        
        Time Complexity: O(n)
        Space Complexity: O(24)
        
        Returns:
            Recharts-compatible hourly data
        """
        hour_counts = self.df['Hour'].value_counts().sort_index()
        
        # Fill missing hours with 0
        all_hours = pd.Series(0, index=range(24))
        hour_counts = hour_counts.reindex(all_hours.index, fill_value=0)
        
        peak_hour = hour_counts.idxmax()
        
        # Generate insight text
        insight = f"Peak activity is at {peak_hour:02d}:00! That's when this chat is most alive. 🔥"
        
        return {
            "data": [
                {"hour": int(hour), "messages": int(count)}
                for hour, count in hour_counts.items()
            ],
            "peak_hour": int(peak_hour),
            "peak_hour_label": f"{peak_hour:02d}:00",
            "insight": insight
        }
    
    def analyze_weekly_activity(self) -> dict[str, Any]:
        """
        Analyze message activity by day of week.
        
        Time Complexity: O(n)
        Space Complexity: O(7)
        
        Returns:
            Recharts-compatible weekly data
        """
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = self.df['Day'].value_counts().reindex(days_order, fill_value=0)
        
        busiest_day = day_counts.idxmax()
        
        busiest_count = int(day_counts.max())
        
        # Generate insight text
        insight = f"{busiest_day} is the busiest day with {busiest_count:,} messages! The chat goes wild on this day. 🎉"
        
        return {
            "data": [
                {"day": day, "messages": int(count)}
                for day, count in day_counts.items()
            ],
            "busiest_day": busiest_day,
            "weekend_vs_weekday": {
                "weekend": int(day_counts[['Saturday', 'Sunday']].sum()),
                "weekday": int(day_counts[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']].sum())
            },
            "insight": insight
        }
    
    def analyze_emojis(self, limit: int = 10) -> dict[str, Any]:
        """
        Analyze emoji usage patterns.
        
        Time Complexity: O(n*m) where m is avg message length
        Space Complexity: O(n)
        
        Args:
            limit: Max items to return per category
            
        Returns:
            Emoji analysis data
        """
        df = self.df.copy()
        df['emojis'] = df['Message'].apply(extract_emojis)
        df['emoji_count'] = df['emojis'].apply(len)
        
        # Top emoji users
        top_authors = df['CleanAuthor'].value_counts().head(limit).index
        emoji_users = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['emoji_count'].sum()
        emoji_users = emoji_users.sort_values(ascending=False)
        
        # Most popular emojis
        all_emojis = [e for emojis in df['emojis'] for e in emojis]
        emoji_counter = Counter(all_emojis)
        top_emojis = emoji_counter.most_common(limit)
        
        # Signature emoji per person (Top 5 for detail)
        author_summaries = []
        for author in top_authors:
            author_emojis = [e for emojis in df[df['CleanAuthor'] == author]['emojis'] for e in emojis]
            if author_emojis:
                counts = Counter(author_emojis)
                top_for_author = [
                    {"emoji": e, "count": c} 
                    for e, c in counts.most_common(5)
                ]
                author_summaries.append({
                    "name": author,
                    "top_emojis": top_for_author,
                    "primary_emoji": top_for_author[0]["emoji"]
                })
        
        # Generate insight text
        insight = None
        if not emoji_users.empty:
            top_user = emoji_users.index[0]
            emoji_count = int(emoji_users.values[0])
            insight = f"{top_user} is the emoji champion with {emoji_count:,} emojis used! 👑"
        
        return {
            "top_users": [
                {"name": name, "emoji_count": int(count)}
                for name, count in emoji_users.items()
            ],
            "top_emojis": [
                {"emoji": emoji, "count": count}
                for emoji, count in top_emojis
            ],
            "author_summaries": author_summaries,
            "total_emojis": len(all_emojis),
            "insight": insight
        }
    
    def analyze_message_length(self, limit: int = 10) -> dict[str, Any]:
        """
        Analyze average message length per author.
        
        Time Complexity: O(n)
        Space Complexity: O(k)
        
        Args:
            limit: Max authors to return
            
        Returns:
            Message length data
        """
        top_authors = self.df['CleanAuthor'].value_counts().head(limit).index
        avg_lengths = self.df[self.df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['msg_length'].mean()
        avg_lengths = avg_lengths.sort_values(ascending=False)
        
        # Find longest single message
        longest_idx = self.df['msg_length'].idxmax()
        longest_msg = self.df.loc[longest_idx]
        
        # Generate insight text
        insight = None
        if not avg_lengths.empty:
            top_writer = avg_lengths.index[0]
            avg_len = round(avg_lengths.values[0], 0)
            insight = f"{top_writer} writes essays with an average of {avg_len:.0f} characters per message! 📚"
        
        return {
            "data": [
                {"name": name, "avg_length": round(length, 1)}
                for name, length in avg_lengths.items()
            ],
            "longest_message": {
                "author": clean_name(longest_msg['Author']),
                "length": int(longest_msg['msg_length']),
                "preview": longest_msg['Message'][:200] + "..." if len(longest_msg['Message']) > 200 else longest_msg['Message']
            },
            "insight": insight
        }
    
    def analyze_links(self, limit: int = 10) -> dict[str, Any]:
        """
        Analyze link sharing per author.
        
        Time Complexity: O(n*m)
        Space Complexity: O(n)
        
        Args:
            limit: Max authors to return
            
        Returns:
            Link sharing data
        """
        df = self.df.copy()
        df['has_link'] = df['Message'].apply(has_link)
        
        top_authors = df['CleanAuthor'].value_counts().head(limit).index
        link_sharers = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['has_link'].sum()
        link_sharers = link_sharers.sort_values(ascending=False)
        
        # Generate insight text
        insight = None
        if not link_sharers.empty and link_sharers.values[0] > 0:
            top_linker = link_sharers.index[0]
            count = int(link_sharers.values[0])
            insight = f"{top_linker} is the group's news source with {count:,} links shared! 📰"
        else:
            insight = "No links shared in this chat!"
        
        return {
            "data": [
                {"name": name, "links": int(count)}
                for name, count in link_sharers.items()
            ],
            "total_links": int(df['has_link'].sum()),
            "top_sharer": link_sharers.index[0] if not link_sharers.empty and link_sharers.values[0] > 0 else None,
            "insight": insight
        }
    
    def get_leaderboard(self, limit: int = 5) -> dict[str, Any]:
        """
        Get top contributors leaderboard.
        
        Time Complexity: O(n)
        Space Complexity: O(k)
        
        Args:
            limit: Number of top contributors
            
        Returns:
            Leaderboard data
        """
        top = self.df['Author'].value_counts().head(limit)
        total = len(self.df)
        
        return {
            "data": [
                {
                    "rank": i + 1,
                    "name": clean_name(author),
                    "messages": int(count),
                    "percentage": round((count / total) * 100, 1)
                }
                for i, (author, count) in enumerate(top.items())
            ]
        }
    
    def analyze_conversation_roles(self) -> dict[str, Any]:
        """
        Identify conversation starters and enders.
        
        Time Complexity: O(n log n)
        Space Complexity: O(n)
        
        Returns:
            Conversation role data
        """
        df = self.df.sort_values('DateTime').copy()
        df['time_since_last'] = df['DateTime'].diff().dt.total_seconds() / 3600  # hours
        
        # Starters: messages after 3+ hours of silence
        starters = df[df['time_since_last'] > 3]
        starter_counts = starters['CleanAuthor'].value_counts().head(10)
        
        # Enders: messages before 3+ hours of silence
        df['time_to_next'] = df['DateTime'].shift(-1) - df['DateTime']
        df['time_to_next_hours'] = df['time_to_next'].dt.total_seconds() / 3600
        enders = df[df['time_to_next_hours'] > 3]
        ender_counts = enders['CleanAuthor'].value_counts().head(10)
        
        # Generate insight text
        insight_parts = []
        if not starter_counts.empty:
            insight_parts.append(f"{starter_counts.index[0]} is the conversation igniter, breaking {int(starter_counts.values[0])} silences! 🔥")
        if not ender_counts.empty:
            insight_parts.append(f"{ender_counts.index[0]} has the last word {int(ender_counts.values[0])} times... conversation killer or mic drop master? 🎤⬇️")
        insight = " ".join(insight_parts) if insight_parts else None
        
        return {
            "starters": [
                {"name": name, "count": int(count)}
                for name, count in starter_counts.items()
            ],
            "enders": [
                {"name": name, "count": int(count)}
                for name, count in ender_counts.items()
            ],
            "top_starter": starter_counts.index[0] if not starter_counts.empty else None,
            "top_ender": ender_counts.index[0] if not ender_counts.empty else None,
            "insight": insight
        }
    
    def detect_monologues(self, min_consecutive: int = 3) -> dict[str, Any]:
        """
        Find who sends multiple messages in a row.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            min_consecutive: Minimum consecutive messages to count
            
        Returns:
            Monologue data
        """
        df = self.df.sort_values('DateTime').reset_index(drop=True)
        
        monologue_data = []
        current_author = None
        current_count = 0
        
        for _, row in df.iterrows():
            if row['Author'] == current_author:
                current_count += 1
            else:
                if current_count >= min_consecutive:
                    monologue_data.append({
                        'author': clean_name(current_author),
                        'count': current_count
                    })
                current_author = row['Author']
                current_count = 1
        
        if current_count >= min_consecutive:
            monologue_data.append({
                'author': clean_name(current_author),
                'count': current_count
            })
        
        if not monologue_data:
            return {"data": [], "top_monologuer": None, "insight": "No monologues detected! Everyone's pretty balanced."}
        
        # Aggregate by author
        from collections import defaultdict
        totals = defaultdict(int)
        for item in monologue_data:
            totals[item['author']] += item['count']
        
        sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Generate insight text
        insight = None
        if sorted_totals:
            top_name = sorted_totals[0][0]
            total_count = sorted_totals[0][1]
            insight = f"{top_name} loves to send multiple messages in a row! Total: {total_count:,} consecutive messages. 📱💨"
        
        return {
            "data": [
                {"name": name, "consecutive_messages": count}
                for name, count in sorted_totals
            ],
            "top_monologuer": sorted_totals[0][0] if sorted_totals else None,
            "insight": insight
        }
    
    def calculate_achievements(self) -> dict[str, Any]:
        """
        Award achievement badges based on behavior.
        
        Time Complexity: O(n)
        Space Complexity: O(k)
        
        Returns:
            Achievements per person
        """
        df = self.df
        achievements = {}
        
        # Night Owl - most messages after midnight (0-5)
        night_msgs = df[df['Hour'].between(0, 5)]
        if not night_msgs.empty:
            night_owl = night_msgs['CleanAuthor'].value_counts().index[0]
            achievements[night_owl] = achievements.get(night_owl, []) + ['🦉 Night Owl']
        
        # Early Bird - most messages 5-7am
        early_msgs = df[df['Hour'].between(5, 7)]
        if not early_msgs.empty:
            early_bird = early_msgs['CleanAuthor'].value_counts().index[0]
            achievements[early_bird] = achievements.get(early_bird, []) + ['🐦 Early Bird']
        
        # Comedian - highest emoji to text ratio
        df['emojis'] = df['Message'].apply(extract_emojis)
        df['emoji_count'] = df['emojis'].apply(len)
        df['emoji_ratio'] = df['emoji_count'] / (df['Message'].str.len() + 1)
        top_authors = df['CleanAuthor'].value_counts().head(10).index
        if not top_authors.empty:
            emoji_ratios = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['emoji_ratio'].mean()
            if not emoji_ratios.empty:
                comedian = emoji_ratios.idxmax()
                achievements[comedian] = achievements.get(comedian, []) + ['😂 Comedian']

        # Lightning - fastest average response
        # Using 12h limit for "conversations"
        df_sorted = df.sort_values('DateTime')
        df_sorted['Prev_Author'] = df_sorted['Author'].shift(1)
        df_sorted['Time_Diff'] = df_sorted['DateTime'].diff().dt.total_seconds() / 60
        replies = df_sorted[(df_sorted['Author'] != df_sorted['Prev_Author']) & 
                           (df_sorted['Time_Diff'] < 720) & (df_sorted['Time_Diff'] > 0)]
        if not replies.empty:
            avg_response = replies[replies['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['Time_Diff'].mean()
            if not avg_response.empty:
                lightning = avg_response.idxmin()
                achievements[lightning] = achievements.get(lightning, []) + ['⚡ Lightning']

        # Chatterbox - most messages overall
        chatterbox = df['CleanAuthor'].value_counts().index[0]
        achievements[chatterbox] = achievements.get(chatterbox, []) + ['💬 Chatterbox']
        
        # Professor - longest average message
        avg_length = df[df['CleanAuthor'].isin(top_authors)].groupby('CleanAuthor')['msg_length'].mean()
        if not avg_length.empty:
            professor = avg_length.idxmax()
            achievements[professor] = achievements.get(professor, []) + ['👨‍🏫 Professor']
        
        return {
            "achievements": [
                {"name": name, "badges": badges}
                for name, badges in achievements.items()
            ],
            "insight": f"{chatterbox} is the primary chatterbox, but watch out for {lightning if not replies.empty else 'everyone'}'s response speed!"
        }
    
    def compare_user_to_group(self, user_name: str) -> dict[str, Any] | None:
        """
        Compare a specific user to group averages.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            user_name: Name to look up (will clean and match)
            
        Returns:
            Comparison data or None if user not found
        """
        clean_user = clean_name(user_name)
        
        if clean_user not in self.df['CleanAuthor'].values:
            return None
        
        user_df = self.df[self.df['CleanAuthor'] == clean_user]
        num_authors = self.df['Author'].nunique()
        
        # 1. Messages
        user_msgs = len(user_df)
        group_avg_msgs = len(self.df) / num_authors
        
        # 2. Response Time
        df_sorted = self.df.sort_values('DateTime')
        df_sorted['Prev_Author'] = df_sorted['Author'].shift(1)
        df_sorted['Time_Diff'] = df_sorted['DateTime'].diff().dt.total_seconds() / 60
        replies = df_sorted[(df_sorted['Author'] != df_sorted['Prev_Author']) & 
                           (df_sorted['Time_Diff'] < 720) & (df_sorted['Time_Diff'] > 0)]
        
        user_response = 0
        group_response = 0
        if not replies.empty:
            user_response = replies[replies['CleanAuthor'] == clean_user]['Time_Diff'].mean() or 0
            group_response = replies['Time_Diff'].mean() or 0

        # 3. Sentiment
        user_sentiment = user_df.apply(lambda r: get_sentiment(r['Message']), axis=1).mean() * 100
        group_sentiment = self.df.apply(lambda r: get_sentiment(r['Message']), axis=1).mean() * 100

        # 4. Emojis
        user_emojis = user_df['Message'].apply(lambda x: len(extract_emojis(x))).sum()
        group_emojis = self.df['Message'].apply(lambda x: len(extract_emojis(x))).sum() / num_authors

        metrics = {
            "user_name": clean_user,
            "messages": {
                "user": int(user_msgs),
                "group_avg": round(group_avg_msgs, 1)
            },
            "avg_message_length": {
                "user": round(user_df['msg_length'].mean(), 1),
                "group_avg": round(self.df['msg_length'].mean(), 1)
            },
            "response_time": {
                "user": round(user_response, 1),
                "group_avg": round(group_response, 1)
            },
            "positivity": {
                "user": round(user_sentiment, 1),
                "group_avg": round(group_sentiment, 1)
            },
            "emojis": {
                "user": int(user_emojis),
                "group_avg": round(group_emojis, 1)
            }
        }
        
        return metrics

    def analyze_word_frequency(self, limit: int = 100) -> dict[str, Any]:
        """
        Get word frequency for Word Cloud.
        
        Time Complexity: O(n*m)
        Space Complexity: O(unique words)
        
        Returns:
            List of {text: word, value: count}
        """
        import re
        from collections import Counter
        
        # Stopwords
        STOPWORDS = {"media", "omitted", "image", "video", "sticker", "message", "deleted", "null", "the", "and", "is", "a", "of", "to"}
        
        all_text = " ".join(self.df['Message'].astype(str).tolist()).lower()
        words = re.findall(r'\b\w{3,}\b', all_text) # Only words 3+ chars
        
        filtered_words = [w for w in words if w not in STOPWORDS]
        word_counts = Counter(filtered_words).most_common(limit)
        
        return {
            "data": [
                {"text": word, "value": count}
                for word, count in word_counts
            ],
            "insight": "This cloud shows the most common topics discussed. Bigger words were mentioned more often!"
        }
