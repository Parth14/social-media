# Social Media Scraper and Keyword Generator

This project consists of several scripts for scraping posts from Twitter/X.com, generating keywords for those posts using LLMs, and viewing the results.

## Scripts Overview

1. **social_media_scraper.py**: Scrapes posts from Twitter/X.com and stores them in a SQLite database.
2. **generate_keywords.py**: Generates keywords for posts using OpenRouter (with GPT-4o by default) and stores them in the database.
3. **view_posts_db.py**: Views posts from the database (original viewer).
4. **view_posts_with_keywords.py**: Enhanced viewer that displays posts with their keywords and keyword statistics.

## Setup

1. Install required dependencies:

```bash
pip install requests sqlite3 langchain-openai python-dotenv
```

2. Set up environment variables (create a `.env` file in the project root):

```
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o  # Optional, defaults to GPT-4o
```

You can get an OpenRouter API key by signing up at [openrouter.ai](https://openrouter.ai/).

## Usage

### 1. Scrape Posts from Twitter/X.com

Run the social media scraper to collect posts:

```bash
python social_media_scraper.py
```

This will:
- Prompt you for your Twitter/X.com username and password
- Open a browser and log in to Twitter/X.com
- Navigate to the home feed
- Extract the top 10 posts with their metrics
- Store the posts in a SQLite database (`x_com_posts.db`)

### 2. Generate Keywords for Posts

After scraping posts, generate keywords for them:

```bash
python generate_keywords.py
```

Options:
- `--limit <number>`: Process only a specific number of posts
- `--batch-size <number>`: Number of posts to process before pausing (default: 10)
- `--stats`: View keyword statistics only without processing posts

This will:
- Add a `keywords` column to the posts table if it doesn't exist
- Create a `keywords` table to track unique keywords and their frequency
- Call OpenRouter API to generate 3-5 keywords for each post
- Update the database with the generated keywords

### 3. View Posts with Keywords

View the posts with their generated keywords:

```bash
python view_posts_with_keywords.py
```

Options:
- `--db <path>`: Specify a different database file (default: `x_com_posts.db`)
- `--limit <number>`: Limit the number of posts to display
- `--keywords-only`: Show only keyword statistics without posts
- `--no-keywords`: Don't show keywords with posts

## Database Structure

The SQLite database (`x_com_posts.db`) contains two tables:

### Posts Table
- `id`: Unique identifier for each post
- `post_text`: The text content of the post
- `post_url`: URL of the post
- `username`: Username of the account that made the post
- `image_url`: URL of any image in the post (if present)
- `views`: View count
- `comments`: Comment count
- `retweets`: Retweet count
- `likes`: Like count
- `saves`: Save count
- `post_time`: Time the post was made
- `scraped_at`: Time the post was scraped
- `keywords`: JSON array of keywords for the post (added by generate_keywords.py)

### Keywords Table
- `id`: Unique identifier for each keyword
- `keyword`: The keyword text
- `frequency`: Number of times this keyword appears across all posts
- `first_seen_at`: When this keyword was first added to the database

## Customizing the LLM

By default, the keyword generator uses GPT-4o through OpenRouter. You can change the model by:

1. Setting the `OPENROUTER_MODEL` environment variable in your `.env` file
2. Using any model supported by OpenRouter (e.g., `anthropic/claude-3-opus`, `google/gemini-pro`, etc.)

## Troubleshooting

- If the scraper fails to extract post metrics, try running it again. Twitter/X.com's UI can be dynamic and sometimes elements take time to load.
- If you encounter rate limits with OpenRouter, increase the `--batch-size` parameter when running `generate_keywords.py`.
- Make sure JavaScript is enabled in the browser used by the scraper.
