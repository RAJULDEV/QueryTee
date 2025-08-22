import os
import mysql.connector
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure Google AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def clean_response_text(text):
    """Cleans up common AI formatting issues like missing spaces."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\.([A-Z])', r'. \1', text)      # Add space after a period followed by a capital letter
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text) # Add space between a lowercase and an uppercase letter
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)# Add space between a number and a letter
    return text

class TShirtStoreAI:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME')
        }
        # FIX 1: Updated to a current and more powerful model
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
    def get_db_connection(self):
        """Create database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as e:
            st.error(f"Database connection failed: {e}")
            return None
    
    def get_schema_info(self):
        """Get database schema information for the AI model"""
        return f"""
        Database Schema:
        
        Table: inventory
        - id (INT, PRIMARY KEY), brand (VARCHAR), product_name (VARCHAR), size (ENUM), 
        - color (VARCHAR), stock_quantity (INT), price_per_item (DECIMAL)
        
        Table: discounts
        - id (INT, PRIMARY KEY), brand (VARCHAR), product_name (VARCHAR), 
        - discount_type (ENUM: 'percentage', 'fixed_amount'), discount_value (DECIMAL), 
        - start_date (DATE), end_date (DATE), min_quantity (INT), is_active (BOOLEAN)
        
        Current date for all queries is: {datetime.now().strftime('%Y-%m-%d')}
        """
    
    def natural_language_to_sql(self, question):
        """Convert natural language question to SQL query using Gemini"""
        
        # FIX 2: Added a much more robust prompt to handle edge cases
        prompt = f"""
        You are a SQL expert for a t-shirt store database. Your goal is to convert a natural language question into a single, accurate SQL query.
        {self.get_schema_info()}
        ---
        **CRITICAL RULES:**
        1.  **Always JOIN for Discounts:** If the question mentions "discount," "sale," or "price," you **MUST** JOIN `inventory` (aliased as `i`) with `discounts` (aliased as `d`) on `i.brand = d.brand`.
        2.  **Handle Minimum Quantity Correctly:** A user's question about a single item (e.g., "a nike shirt") implies a quantity of 1. If the discount in the database requires a `min_quantity` > 1, your query **MUST NOT** filter this discount out. The goal is to show that a discount *is available* but has conditions. Therefore, **DO NOT** add a `WHERE` clause that filters based on `min_quantity` unless the user explicitly states a quantity (e.g., "discount for 3 shirts").
        3.  **Filter by Active Discounts:** Always include this condition in your `WHERE` clause for discount-related queries: `d.is_active = TRUE AND CURDATE() BETWEEN d.start_date AND d.end_date`.
        4.  **Use LOWER() for Case-Insensitive Matches:** Always wrap text-based columns like `brand` or `color` in the `LOWER()` function in the `WHERE` clause for comparisons.
        5.  **Return Only the SQL Query:** Your entire response should be only the SQL code, with no explanations or markdown.
        ---
        Question: {question}
        SQL Query:
        """
        
        try:
            response = self.model.generate_content(prompt)
            sql_query = response.text.strip()
            
            sql_query = re.sub(r'```sql\n?', '', sql_query)
            sql_query = re.sub(r'```\n?', '', sql_query)
            sql_query = sql_query.strip()
            
            return sql_query
            
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    def execute_query(self, sql_query):
        """Execute SQL query and return results"""
        conn = self.get_db_connection()
        if not conn:
            return None, "Database connection failed"
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return results, None
            
        except Exception as e:
            if conn.is_connected():
                conn.close()
            return None, str(e)
    
    def format_response(self, question, results, error=None):
        """Format the response for the manager"""
        if error:
            return f"I apologize, but I encountered an error processing your question: {error}"
        
        if not results:
            return "I couldn't find any matching results for your question."
        
        df = pd.DataFrame(results)
        
        response_prompt = f"""
        Based on this database query result, provide a natural, conversational response to the original question.
        Original question: {question}
        Query results: {df.head(10).to_string(index=False)}
        
        Make the response:
        1. Conversational and helpful.
        2. If the query result contains a 'min_quantity' greater than 1, explain that condition to the user (e.g., "This discount applies if you buy X or more items.").
        3. Summarize the results clearly. Use bullet points for lists of items.
        4. Ensure correct grammar, punctuation, and spacing between sentences.
        5. Use proper currency formatting ($XX.XX).
        
        Response:
        """
        
        try:
            response = self.model.generate_content(response_prompt)
            formatted_response = response.text.strip()
            return clean_response_text(formatted_response)
        except Exception:
            return self.format_dataframe_simple(df)
            
    def format_dataframe_simple(self, df):
        """Simple dataframe formatting for fallback"""
        if df.empty:
            return "No results found."
        
        result_text = f"Found {len(df)} results:\n\n"
        
        for _, row in df.iterrows():
            if 'brand' in row and 'product_name' in row:
                result_text += f"**{row.get('brand', 'N/A')} - {row.get('product_name', 'N/A')}**\n"
                details = [
                    f"Size: {row['size']}" if 'size' in row else None,
                    f"Color: {row['color']}" if 'color' in row else None,
                    f"Price: ${float(row['price_per_item']):.2f}" if 'price_per_item' in row else None,
                    f"Stock: {row['stock_quantity']} units" if 'stock_quantity' in row else None
                ]
                result_text += " • ".join(filter(None, details)) + "\n\n"
            else:
                # Fallback for other query types (like discount info)
                result_text += " | ".join([f"{col}: {val}" for col, val in row.items()]) + "\n\n"
        
        # FIX 3: Moved the return statement outside the loop to ensure all rows are processed.
        return result_text

def main():
    st.set_page_config(page_title="T-Shirt Store AI Assistant", page_icon="👕", layout="wide")
    
    st.title("👕 T-Shirt Store AI Assistant")
    st.markdown("Ask me anything about our inventory, prices, and stock levels!")
    
    if 'store_ai' not in st.session_state:
        st.session_state.store_ai = TShirtStoreAI()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Ask a Question")
        
        question = st.text_input("Your question:", placeholder="e.g., Do we have Nike t-shirts in large size?")
        
        if st.button("Get Answer", type="primary"):
            if question:
                with st.spinner("Processing your question..."):
                    store_ai = st.session_state.store_ai
                    sql_query = store_ai.natural_language_to_sql(question)
                    
                    if sql_query.startswith("Error"):
                        st.error(sql_query)
                    else:
                        results, error = store_ai.execute_query(sql_query)
                        response = store_ai.format_response(question, results, error)
                        
                        st.subheader("Answer:")
                        st.success(response)
                        
                        with st.expander("🔧 Technical Details"):
                            st.markdown("**Generated SQL Query:**")
                            st.code(sql_query, language="sql")
                            if results:
                                st.markdown("**Raw Query Results:**")
                                st.dataframe(pd.DataFrame(results))
            else:
                st.warning("Please enter a question!")
    
    with col2:
        st.subheader("📊 Quick Stats")
        try:
            conn = st.session_state.store_ai.get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                
                queries = {
                    "Total Products": "SELECT COUNT(*) as total FROM inventory",
                    "Brands Available": "SELECT COUNT(DISTINCT brand) as total FROM inventory",
                    "Low Stock Items": "SELECT COUNT(*) as total FROM inventory WHERE stock_quantity < 10",
                    "Active Discounts": "SELECT COUNT(*) as total FROM discounts WHERE is_active = TRUE AND CURDATE() BETWEEN start_date AND end_date",
                    "Average Price": "SELECT AVG(price_per_item) as avg_price FROM inventory"
                }
                
                stats = {}
                for key, query in queries.items():
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if key == "Average Price":
                        stats[key] = f"${result['avg_price']:.2f}" if result and result['avg_price'] else "$0.00"
                    else:
                        stats[key] = result['total'] if result else 0

                cursor.close()
                conn.close()
                
                st.metric("Total Products", stats["Total Products"])
                st.metric("Brands Available", stats["Brands Available"])
                st.metric("Low Stock Items (< 10 units)", stats["Low Stock Items"])
                st.metric("Active Discounts", stats["Active Discounts"])
                st.metric("Average Price", stats["Average Price"])
            else:
                st.error("Database connection failed. Cannot load stats.")
        except Exception as e:
            st.error(f"Error loading stats: {e}")

    st.markdown("---")
    st.info("Sample questions: 'Show me all black t-shirts', 'What's the cheapest t-shirt?', 'Any discounts on Adidas?'")

if __name__ == "__main__":
    main()