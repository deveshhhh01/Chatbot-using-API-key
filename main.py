import tkinter as tk
from tkinter import scrolledtext
import requests
from groq import Groq

# ========= 1. CONFIG =========

# 🔴 PUT YOUR REAL GROQ KEY HERE (same one that worked before)
GROQ_API_KEY = "****"

client = Groq(api_key=GROQ_API_KEY)

# Working Groq model
GROQ_MODEL = "llama-3.3-70b-versatile"

# ---- UI COLORS / FONTS ----
BG_COLOR = "#020617"          # window background (slate-950)
PANEL_COLOR = "#020617"       # same as bg for clean look
CHAT_BG = "#020617"           # chat background
CHAT_BORDER = "#1e293b"       # border line
USER_COLOR = "#38bdf8"        # cyan
BOT_COLOR = "#a5b4fc"         # indigo
TEXT_COLOR = "#e5e7eb"        # light gray
INPUT_BG = "#020617"
INPUT_BORDER = "#1e293b"
ACCENT_COLOR = "#22c55e"      # green button
ACCENT_COLOR_HOVER = "#16a34a"

FONT_NORMAL = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI Semibold", 13)


# ========= 2. WEB SEARCH (DUCKDUCKGO) =========

def search_web(query: str, max_items: int = 5) -> str:
    """
    Uses DuckDuckGo Instant Answer API to get quick info for a query.
    Returns a text block with summary + some related snippets.
    """
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "no_redirect": 1,
        "skip_disambig": 0,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception as e:
            return f"[Web JSON error: {e}. Raw: {resp.text[:200]}]"
    except Exception as e:
        return f"[Web request error: {e}]"

    chunks = []

    if data.get("AbstractText"):
        chunks.append("Main summary: " + data["AbstractText"])

    related = data.get("RelatedTopics", [])[:max_items]
    for item in related:
        if isinstance(item, dict) and item.get("Text"):
            chunks.append("Related: " + item["Text"])

    if not chunks:
        return "[No useful web info found for this query.]"

    return "\n\n".join(chunks)


# ========= 3. GROQ ANSWER USING WEB INFO =========

def answer_with_web(question: str) -> str:
    web_info = search_web(question)

    system_message = (
        "You are a helpful assistant. Use the web info when it looks useful, "
        "but if it looks like an error message or is weak, explain that and "
        "answer from your own knowledge."
    )

    user_message = (
        f"User question:\n{question}\n\n"
        f"Web search information:\n{web_info}\n\n"
        "Now answer the user's question clearly. "
        "If the web info looks like an error, say web search failed "
        "and then answer from your own knowledge."
    )

    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[Groq API error in chat: {e}]"


# ========= 4. TKINTER GUI APP =========

class WebGroqGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Groq Chat Bot")
        self.root.configure(bg=BG_COLOR)

        # Window size & min size
        self.root.geometry("780x520")
        self.root.minsize(650, 420)

        # ---- Top Title Bar ----
        top_frame = tk.Frame(self.root, bg=BG_COLOR)
        top_frame.pack(fill=tk.X, padx=14, pady=(12, 4))

        title_label = tk.Label(
            top_frame,
            text="🌐 Web Groq Bot",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=FONT_TITLE,
            anchor="w",
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = tk.Label(
            top_frame,
            text="Internet-aware AI assistant (powered by Groq + DuckDuckGo)",
            bg=BG_COLOR,
            fg="#64748b",
            font=FONT_SMALL,
            anchor="w",
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # ---- Chat Frame ----
        chat_frame = tk.Frame(self.root, bg=BG_COLOR)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 8))

        # Border around chat
        chat_border = tk.Frame(chat_frame, bg=CHAT_BORDER)
        chat_border.pack(fill=tk.BOTH, expand=True)

        self.chat_box = scrolledtext.ScrolledText(
            chat_border,
            wrap=tk.WORD,
            state="disabled",
            font=FONT_NORMAL,
            bg=CHAT_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            bd=0,
            relief="flat",
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True)

        # Tag styles for user & bot messages
        self.chat_box.tag_configure("user_tag", foreground=USER_COLOR, font=("Segoe UI Semibold", 10))
        self.chat_box.tag_configure("bot_tag", foreground=BOT_COLOR, font=("Segoe UI Semibold", 10))
        self.chat_box.tag_configure("meta_tag", foreground="#9ca3af", font=FONT_SMALL)

        # ---- Bottom Input Area ----
        bottom_outer = tk.Frame(self.root, bg=BG_COLOR)
        bottom_outer.pack(fill=tk.X, padx=12, pady=(0, 12))

        input_border = tk.Frame(bottom_outer, bg=INPUT_BORDER)
        input_border.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.entry = tk.Entry(
            input_border,
            font=FONT_NORMAL,
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=4,
        )
        self.entry.pack(fill=tk.X, ipady=6, padx=1, pady=1)
        self.entry.bind("<Return>", self.on_send)

        self.send_button = tk.Button(
            bottom_outer,
            text="Send",
            font=("Segoe UI Semibold", 10),
            bg=ACCENT_COLOR,
            fg="#022c22",
            activebackground=ACCENT_COLOR_HOVER,
            activeforeground="#ecfdf5",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.on_send,
        )
        self.send_button.pack(side=tk.LEFT, padx=(10, 0))

        # Hover effect for button
        self.send_button.bind("<Enter>", lambda e: self.send_button.configure(bg=ACCENT_COLOR_HOVER))
        self.send_button.bind("<Leave>", lambda e: self.send_button.configure(bg=ACCENT_COLOR))

        # Welcome message
        self._append_message("Bot", "Hi! I'm your Web Groq Bot.\nAsk me anything; I'll use the internet when helpful.", role="bot")

        self.entry.focus_set()

    # ---- Chat helpers ----
    def _append_message(self, speaker: str, text: str, role: str = "bot"):
        """
        role: "user" or "bot" or "meta"
        """
        if role == "user":
            tag = "user_tag"
        elif role == "bot":
            tag = "bot_tag"
        else:
            tag = "meta_tag"

        self.chat_box.configure(state="normal")
        # Speaker label
        self.chat_box.insert(tk.END, f"{speaker}: ", tag)
        # Message text
        self.chat_box.insert(tk.END, text + "\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see(tk.END)

    def on_send(self, event=None):
        user_text = self.entry.get().strip()
        if not user_text:
            return

        self._append_message("You", user_text, role="user")
        self.entry.delete(0, tk.END)

        if user_text.lower() in {"quit", "exit"}:
            self._append_message("Bot", "Goodbye! 👋", role="bot")
            self.root.after(800, self.root.destroy)
            return

        # Lock input while processing
        self.entry.configure(state="disabled")
        self.send_button.configure(state="disabled")

        # Show thinking indicator
        self._append_message("Bot", "Thinking... please wait 🔄", role="meta")

        # Run the heavy work shortly after so UI can update
        self.root.after(100, self._generate_answer, user_text)

    def _generate_answer(self, question: str):
        reply = answer_with_web(question)

        # Just append the actual reply
        self._append_message("Bot", reply, role="bot")

        # Re-enable input
        self.entry.configure(state="normal")
        self.send_button.configure(state="normal")
        self.entry.focus_set()


def main():
    if GROQ_API_KEY == "gsk_your_real_key_here":
        print("⚠ Please edit the script and put your Groq API key in GROQ_API_KEY first.")
        return

    root = tk.Tk()
    app = WebGroqGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
