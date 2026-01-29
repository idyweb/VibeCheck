# 📱 VibeCheck: WhatsApp Chat Analyzer

**VibeCheck** is a privacy-first analytics tool that turns your WhatsApp chat exports into beautiful, interactive insights. Visualize who talks the most, who takes the longest to reply, and the overall "vibe" (sentiment) of the conversation.

🔗 **Live Demo:** [analyze.idyvalour.space](https://analyze.idyvalour.space)

---

## 🚀 Features

* **📊 Volume Analysis:** See who dominates the conversation with message count breakdowns.
* **⚡ Ghost Meter:** Calculate average response times to see who leaves you on read.
* **🕰️ Hourly Activity:** Discover when the group is most active (are you night owls or early birds?).
* **☁️ Word Cloud:** Visualize the most used words and slang in your chat.
* **❤️ Sentiment Analysis:** A built-in "Vibe Check" that uses NLP to score the positivity of the chat.
* **🔒 Privacy First:** All processing happens in-memory. No data is ever stored or saved to a database.

---

## 🛠️ Tech Stack

## 🛠️ Tech Stack

* **Python 3.12**
* **Streamlit** (Frontend)
* **Pandas & Matplotlib** (Data Analysis)
* **uv** (Package Management)

---

## ⚙️ Installation & Local Run

Want to run this on your own machine? Follow these steps:

### 1. Clone the repository
```bash
git clone [https://github.com/yourusername/vibecheck.git](https://github.com/yourusername/vibecheck.git)
cd vibecheck

```


### 2. Install dependencies

```bash
uv sync
```
### 3. Run the app
```bash
uv run streamlit run app.py
```
The app will open in your browser at http://localhost:8501.

## How to Export Your Chat
1. Open the WhatsApp chat on your phone.

2. Tap the contact/group name -> **Export Chat**.

3. Select "**Without Media**".

4. Upload the ``.zip`` or ``_chat.txt`` file to the app.

Built with ❤️ by _Idyweb_