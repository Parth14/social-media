import sqlite3
import json
import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load environment variables
load_dotenv()

# Get OpenRouter API key from environment variable or prompt user
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    OPENROUTER_API_KEY = input("Enter your OpenRouter API key: ")

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model to use (default to GPT-4o)
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

def load_base_profile(profile_file='user_profile.txt'):
    """Load the base user profile from the profile file."""
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = f.read()
        return profile
    except FileNotFoundError:
        print(f"User profile file '{profile_file}' not found.")
        return ""

def get_user_feedback(db_file='user_feedback.db'):
    """Get user feedback from the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all feedback
        cursor.execute("""
            SELECT uf.*, sp.post_text, sp.username, sp.keywords, sp.query
            FROM user_feedback uf
            JOIN posts_selected.db.selected_posts sp ON uf.post_id = sp.id
            ORDER BY uf.feedback_timestamp DESC
        """)
        feedback = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return feedback
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        
        # Try a different approach if the JOIN fails
        try:
            # Connect to the databases
            feedback_conn = sqlite3.connect(db_file)
            feedback_conn.row_factory = sqlite3.Row
            feedback_cursor = feedback_conn.cursor()
            
            posts_conn = sqlite3.connect('posts_selected.db')
            posts_conn.row_factory = sqlite3.Row
            posts_cursor = posts_conn.cursor()
            
            # Get all feedback
            feedback_cursor.execute("SELECT * FROM user_feedback ORDER BY feedback_timestamp DESC")
            feedback = [dict(row) for row in feedback_cursor.fetchall()]
            
            # Get post details for each feedback
            for fb in feedback:
                posts_cursor.execute("SELECT post_text, username, keywords, query FROM selected_posts WHERE id = ?", (fb['post_id'],))
                post = posts_cursor.fetchone()
                if post:
                    fb.update(dict(post))
            
            feedback_conn.close()
            posts_conn.close()
            return feedback
            
        except sqlite3.Error as e2:
            print(f"Second SQLite error: {e2}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def format_feedback_for_llm(feedback):
    """Format user feedback for the LLM."""
    formatted = []
    
    for i, fb in enumerate(feedback, 1):
        entry = f"Feedback #{i}:\n"
        
        # Add post details
        if fb.get('username'):
            entry += f"Post by: {fb.get('username')}\n"
        
        if fb.get('post_text'):
            entry += f"Content: {fb.get('post_text')}\n"
        
        if fb.get('keywords'):
            try:
                keywords = json.loads(fb.get('keywords'))
                if keywords:
                    entry += f"Keywords: {', '.join(keywords)}\n"
            except (json.JSONDecodeError, TypeError):
                pass
        
        if fb.get('query'):
            entry += f"User was searching for: {fb.get('query')}\n"
        
        # Add feedback details
        entry += f"User feedback: {fb.get('feedback_type').upper()}"
        if fb.get('text_feedback'):
            entry += f" - {fb.get('text_feedback')}"
        
        entry += f"\nTimestamp: {fb.get('feedback_timestamp')}\n"
        
        formatted.append(entry)
    
    return "\n".join(formatted)

def generate_dynamic_profile(base_profile, feedback_data):
    """
    Call the LLM to generate a dynamic user profile based on the base profile and feedback.
    
    Args:
        base_profile: The base user profile text
        feedback_data: Formatted user feedback data
        
    Returns:
        The dynamic user profile text
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": """You are a user profiling assistant. Your task is to analyze user feedback on content 
                and update their profile to reflect their evolving preferences and interests.
                
                The base profile represents the initial understanding of the user.
                The feedback data shows how the user has interacted with content.
                
                Create a dynamic user profile that:
                1. Maintains the same structure as the base profile
                2. Strengthens interests that are confirmed by positive feedback
                3. Weakens or removes interests that receive negative feedback
                4. Adds new interests or preferences based on positive feedback
                5. Updates the "Likes" and "Doesn't Like" sections based on feedback
                
                Format the profile in Markdown, maintaining the same sections as the base profile.
                """
            },
            {
                "role": "user",
                "content": f"""Here is the base user profile:

{base_profile}

Here is the recent user feedback on content:

{feedback_data}

Please generate an updated dynamic user profile that reflects the user's evolving preferences.
"""
            }
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        dynamic_profile = result["choices"][0]["message"]["content"]
        
        return dynamic_profile
            
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return base_profile  # Return the base profile if there's an error

def save_dynamic_profile(profile, output_file='dynamic_user_profile.md'):
    """Save the dynamic user profile to a file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(profile)
        print(f"Successfully saved dynamic user profile to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving dynamic user profile: {e}")
        return False

def main():
    """Main function to generate a dynamic user profile."""
    print("Starting dynamic user profile generation...")
    
    # Load base profile
    base_profile = load_base_profile()
    if not base_profile:
        print("Failed to load base user profile. Exiting.")
        return
    
    print("Base user profile loaded successfully.")
    
    # Get user feedback
    feedback = get_user_feedback()
    if not feedback:
        print("No user feedback found. Using base profile only.")
        save_dynamic_profile(base_profile)
        return
    
    print(f"Found {len(feedback)} feedback entries.")
    
    # Format feedback for LLM
    formatted_feedback = format_feedback_for_llm(feedback)
    
    # Generate dynamic profile
    print("Generating dynamic user profile...")
    dynamic_profile = generate_dynamic_profile(base_profile, formatted_feedback)
    
    # Save dynamic profile
    if save_dynamic_profile(dynamic_profile):
        print("Dynamic user profile generated successfully.")
    else:
        print("Failed to save dynamic user profile.")

def get_current_dynamic_profile(profile_file='dynamic_user_profile.md'):
    """Get the current dynamic user profile, or generate one if it doesn't exist."""
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = f.read()
        return profile
    except FileNotFoundError:
        print(f"Dynamic user profile file '{profile_file}' not found. Generating new profile...")
        main()
        return get_current_dynamic_profile(profile_file)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a dynamic user profile based on feedback.")
    parser.add_argument("--force", action="store_true", help="Force regeneration of the dynamic profile")
    
    args = parser.parse_args()
    
    if args.force or not os.path.exists('dynamic_user_profile.md'):
        main()
    else:
        print("Dynamic user profile already exists. Use --force to regenerate.")
        print("Current profile location: dynamic_user_profile.md")
