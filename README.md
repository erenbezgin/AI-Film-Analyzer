#  AI-Powered Film Archive and Audience Analysis System

This project is a high-performance film management and analysis platform that integrates modern web technologies with artificial intelligence. Developed to personalize the movie discovery experience, it leverages Natural Language Processing (NLP) and a robust relational database architecture.

---

##  Overview
The **AI-Powered Film Archive and Audience Analysis System** aims to bridge the gap between user emotions and cinematic content. By analyzing user-provided descriptions of their current mood, the system suggests the most relevant movie categories using advanced AI models.

##  Key Features
*   **Intelligent Recommendation System:** Uses the **Google Gemini API** to perform NLP tasks, mapping user mood inputs to specific film genres.
*   **Rich Data Integration:** Seamlessly fetches high-resolution posters, trailers, and metadata using the **TMDb (The Movie Database) API**.
*   **Advanced Database Architecture:** A professional MySQL structure consisting of **10 interconnected tables**, optimized for scalability and data integrity.
*   **Responsive User Experience:** A modern, mobile-friendly interface built with **Flask (Python)** and **Bootstrap 5**.

## Tech Stack
| Category | Technology |
| :--- | :--- |
| **Backend** | Python / Flask |
| **Database** | MySQL (Relational Model) |
| **Artificial Intelligence** | Google Gemini AI (NLP) |
| **Data Source** | TMDb API |
| **Frontend** | HTML5, CSS3, Bootstrap 5 |
| **Version Control** | Git / GitHub |

## Database Schema & Analytics
The system is built on a complex relational schema to handle:
*   User preferences and watchlists.
*   Dynamic content metadata (actors, directors, awards).
*   Sentiment-based query logs for audience analysis.

A suitability score is calculated for each recommendation using the following logic:
$$Score = \frac{(\text{Mood Match Weight} \times 0.6) + (\text{TMDb Rating} \times 0.4)}{\text{Max Potential Score}}$$

##  Getting Started

### Prerequisites
*   Python 3+
*   MySQL Server
*   API Keys for **Google Gemini** and **TMDb**

### Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/erenbezgin/AI-Film-Analyzer.git](https://github.com/erenbezgin/AI-Film-Analyzer.git)
Install dependencies:

Bash
pip install -r requirements.txt


Configuration:
Create a .env file in the root directory and add your credentials:

Kod snippet'i
GEMINI_API_KEY=your_gemini_key_here
TMDB_API_KEY=your_tmdb_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
Run the application:

Bash
python app.py


 License
Distributed under the MIT License. See LICENSE for more information.

Developed by Eren Bezgin