# LinkedIn Auto Job Applier (Custom Edition)

Customized automated job application bot for LinkedIn targeting Software Engineering, Backend, Fullstack, and AI/LLM roles.

- **Author**: [Seraj Khan](https://www.linkedin.com/in/its-seraj/)
- **GitHub**: [https://github.com/its-seraj](https://github.com/its-seraj)

## 🚀 Features

- **Persistent Login Session**: Saves your login cookies and browser profile locally so you only have to log in once.
- **Fast Job Application**: Configurable application delay (default 3 seconds) for quick execution.
- **Intelligent Matching**: Uses deterministic resume-aware filtering and Gemini AI for answering custom application questions.
- **Custom Search & Filtering**: Configurable search terms, allowed titles, and location preferences.

---

## 🛠️ Setup Instructions

### 1. Prerequisites

- **Python 3.10+** installed.
- **Google Chrome** installed.
- **Resume PDF** in project directory (`Seraj_Khan___Senior_Software_Engineer.pdf`).
- **Gemini API Key** (configured in `config/secrets.py`).

### 2. Running the Bot

```bash
python runAiBot.py
```

- **First Run**: Log in to LinkedIn once in the opened Chrome window. Your session is saved automatically.
- **Subsequent Runs**: The bot directly opens your LinkedIn feed with saved login and immediately starts applying.

