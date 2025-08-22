\# 👕 QueryTee: AI T-Shirt Store Assistant



QueryTee is a natural language to SQL query system that allows store managers to get real-time inventory information by asking questions in plain English. This project uses Google's Gemini AI to translate questions into database queries.



!\[App Screenshot]<img width="1920" height="1080" alt="app-screenshot" src="https://github.com/user-attachments/assets/c7091904-e66b-48db-9b13-88a1a2eea4f3" />




\## Key Features



\-   \*\*Natural Language Queries:\*\* Ask questions like "Any discounts on Adidas?" or "Show me all black t-shirts."

\-   \*\*AI-Powered SQL Generation:\*\* Uses Google's Gemini 1.5 Pro model to dynamically convert questions into accurate SQL queries.

\-   \*\*Real-time Database Interaction:\*\* Queries a live MySQL database for up-to-the-minute inventory information.

\-   \*\*Conversational Responses:\*\* Formats database results into friendly, easy-to-understand answers, explaining complex conditions like minimum quantity discounts.

\-   \*\*Web-Based UI:\*\* Built with Streamlit for a simple and interactive user experience.

\-   \*\*Quick Stats Dashboard:\*\* Provides an at-a-glance view of key inventory metrics.



\## Tech Stack



\-   \*\*AI:\*\* Google Gemini 1.5 Pro (`google-generativeai`)

\-   \*\*Web Framework:\*\* Streamlit

\-   \*\*Database:\*\* MySQL (`mysql-connector-python`)

\-   \*\*Data Handling:\*\* Pandas

\-   \*\*Configuration:\*\* `python-dotenv`



\## Local Setup



\### 1. Prerequisites



\-   Python 3.8+

\-   MySQL Server

\-   A Google AI API Key



\### 2. Clone \& Install



```bash

\# Clone the repository

git clone \[https://github.com/your-username/QueryTee.git](https://github.com/your-username/QueryTee.git)

cd QueryTee



\# Create and activate a virtual environment

python -m venv venv

source venv/bin/activate  # On Windows: venv\\Scripts\\activate



\# Install the required packages

pip install -r requirements.txt

```



\### 3. Database \& Environment Setup



1\.  \*\*Database:\*\* Connect to your MySQL instance, create a database named `tshirt\_store`, and run the SQL scripts to create the `inventory` and `discounts` tables and insert the sample data.

2\.  \*\*Environment:\*\* Create a `.env` file in the root of the project and add your credentials:

&nbsp;   ```

&nbsp;   GOOGLE\_API\_KEY="your\_gemini\_api\_key\_here"

&nbsp;   DB\_HOST="localhost"

&nbsp;   DB\_USER="your\_db\_username"

&nbsp;   DB\_PASSWORD="your\_db\_password"

&nbsp;   DB\_NAME="tshirt\_store"

&nbsp;   ```



\### 4. Run the Application



```bash

streamlit run app.py

