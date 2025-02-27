🚀 AWS Lambda Job Scraper (v0.5)
This AWS Lambda project automates job searching by pulling job listings from multiple RSS feeds, storing them in S3, and sending email notifications. It also prevents duplicate jobs using DynamoDB.

📌 Features
✅ Fetches jobs from multiple RSS feeds every 20 minutes
✅ Stores job listings in S3 as CSV files
✅ Sends email notifications via AWS SES
✅ Uses DynamoDB to prevent duplicate job listings

🛠️ Tech Stack
AWS Lambda – Serverless function for automation
AWS S3 – Stores job data as CSV files
AWS SES – Sends job listing notifications via email
AWS DynamoDB – Tracks job postings to avoid duplicates
EventBridge – Schedules execution every 20 minutes
Python – Processes RSS feeds and handles data storage
🚀 Setup & Deployment
1️⃣ AWS Configuration
Before running this project, ensure you have:
✅ AWS CLI configured
✅ An IAM Role with Lambda, S3, SES, and DynamoDB permissions
✅ A verified email in AWS SES
✅ A DynamoDB table named JobListings

2️⃣ Clone the Repository
git clone https://github.com/YOUR_GITHUB_USERNAME/aws-lambda-job-scraper.git
cd aws-lambda-job-scraper

3️⃣ Install Dependencises
pip install -r requirements.txt

4️⃣ Deploy to AWS Lambda
    1.  Zip the function
    2.  Upload to AWS Lambda Console
    3.  Schedule with EventBridge (rate(20 minutes))
    
    🛠️ How It Works

1️⃣ The Lambda function fetches job listings from RSS feeds
2️⃣ It checks DynamoDB → If a job is already stored, it’s skipped
3️⃣ New jobs are:
    •   ✅ Saved to S3 as a CSV file
    •   ✅ Emailed via AWS SES
4️⃣ The next run only includes fresh job listings
