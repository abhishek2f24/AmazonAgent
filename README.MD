# Amazon to Pinterest Automation

This repository contains a GitHub Actions workflow that automatically:
1. Scrapes Amazon bestseller products daily
2. Generates marketing images using OpenAI's DALL-E
3. Creates SEO-optimized content using GPT
4. Posts the content to Pinterest

## Setup Instructions

### 1. Fork or Clone this Repository

### 2. Set Up Required Secrets in GitHub

Add the following secrets to your GitHub repository:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PINTEREST_ACCESS_TOKEN`: Your Pinterest API access token
- `PINTEREST_BOARD_ID`: The ID of the Pinterest board you want to post to

To add secrets:
1. Go to your repository on GitHub
2. Click on "Settings"
3. In the left sidebar, click on "Secrets and variables" > "Actions"
4. Click on "New repository secret" to add each of the required secrets

### 3. Pinterest API Setup

1. Create a Pinterest Developer account: https://developers.pinterest.com/
2. Create a new app
3. Set the redirect URI to `https://localhost:8000/`
4. Request access to the necessary scopes: `boards:read`, `pins:read`, `pins:write`
5. Generate an access token

### 4. Customize the Workflow (Optional)

You can modify:
- The Amazon categories to scrape in `amazon_scraper.py`
- The cron schedule in `.github/workflows/daily_automation.yml`
- The image design in `image_generator.py`

### 5. Running the Workflow

The workflow runs automatically daily at midnight UTC. 
You can also trigger it manually:
1. Go to the "Actions" tab in your repository
2. Select the "Daily Amazon to Pinterest Automation" workflow
3. Click "Run workflow"

## Local Development

If you want to run the code locally:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your credentials based on `.env.example`

3. Run the main script:
```bash
python main.py
```

## Logging

The script maintains logs in:
- `automation.log` - General application logs
- `logs/pinterest_activity_YYYY-MM-DD.json` - Daily activity summary

## Limitations

- The Amazon scraper may need adjustment if Amazon changes their HTML structure
- Pinterest API tokens expire after a certain period and will need to be refreshed
- DALL-E image generation costs will apply to your OpenAI account
"""