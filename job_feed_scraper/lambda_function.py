import json
import requests
import csv
import boto3
import os
import xml.etree.ElementTree as ET
from datetime import datetime

# AWS Resources
s3 = boto3.client('s3')
ses = boto3.client('ses', region_name='us-east-2')  # Ensure this matches your SES region

# Configuration
RSS_FEED_URLS = [
    "https://rss.app/feeds/3hmZ3zBHYBtSPEhC.xml",  
    "https://rss.app/feeds/pjy02GvICirXnyuY.xml",
    "https://rss.app/feeds/ZVpgJBTNE7hDXeQM.xml"
]  # Add more feeds as needed
S3_BUCKET = "hs-my-jobsearch-bucket"
S3_FILE_NAME = f"jobs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
EMAIL_SENDER = "hsantana@renacentis.org"  # Must be verified in AWS SES
EMAIL_RECIPIENT = "hsantana@renacentis.org"  # Change if needed

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('JobListings')

def is_job_new(job_link):  # Check if job is new
    """Check if a job already exists in DynamoDB."""
    response = table.get_item(Key={'job_link': job_link})
    return 'Item' not in response  # Returns True if job is new

def save_job_to_dynamodb(job_link, title, pub_date, source):
    """Store new job in DynamoDB to prevent duplicates."""
    table.put_item(Item={
        'job_link': job_link,
        'title': title,
        'pub_date': pub_date,
        'source': source
    })

def fetch_rss_jobs():
    """Fetch job listings from multiple RSS feeds."""
    jobs = []

    for feed_url in RSS_FEED_URLS:
        response = requests.get(feed_url)
        if response.status_code != 200:
            print(f"Failed to fetch RSS feed: {feed_url} - Status Code: {response.status_code}")
            continue  # Skip this feed and move to the next

        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            title = item.find("title").text or "No Title"
            link = item.find("link").text or "No Link"
            pub_date = item.find("pubDate").text or "No Date"

            if is_job_new(link):  # ✅ Check if job is new
                jobs.append([title, link, pub_date, feed_url])
                save_job_to_dynamodb(link, title, pub_date, feed_url)  # ✅ Store new job  

    return jobs

def save_to_csv(jobs):
    """Save jobs to CSV and upload to S3."""
    local_file = "/tmp/" + S3_FILE_NAME  # Lambda can only write to /tmp/
    
    with open(local_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Job Title", "Link", "Published Date", "Source"])
        writer.writerows(jobs)

    s3.upload_file(local_file, S3_BUCKET, S3_FILE_NAME)
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{S3_FILE_NAME}"

def send_email(jobs, s3_url):
    """Send a formatted HTML email with job listings from multiple sources."""
    subject = "🚀 New Job Listings Available!"
    
    # Generate HTML job listings with source URL
    job_list_html = "".join(
        f"<li><strong>{job[0]}</strong> - <a href='{job[1]}' target='_blank'>Apply Now</a> (Posted: {job[2]})<br><small>Source: <a href='{job[3]}' target='_blank'>{job[3]}</a></small></li>"
        for job in jobs[:10]  # Limit to first 10 jobs in the email
    )

    body_html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            ul {{
                padding: 0;
                list-style-type: none;
            }}
            li {{
                margin-bottom: 8px;
            }}
            small {{
                color: gray;
            }}
        </style>
    </head>
    <body>
        <h2>🚀 New Job Listings Available!</h2>
        <p>The latest job opportunities have been collected from multiple sources:</p>
        <ul>
            {job_list_html}
        </ul>
        <p>🔗 <a href="{s3_url}" target="_blank">Download Full Job List (CSV)</a></p>
    </body>
    </html>
    """

    ses.send_email(
        Source=EMAIL_SENDER,
        Destination={"ToAddresses": [EMAIL_RECIPIENT]},
        Message={
            "Subject": {"Data": subject},
            "Body": {
                "Html": {"Data": body_html},
                "Text": {"Data": f"New job listings available! View the CSV file here: {s3_url}"}
            },
        },
    )

def lambda_handler(event, context):
    """AWS Lambda entry point."""
    try:
        jobs = fetch_rss_jobs()
        s3_url = save_to_csv(jobs)
        send_email(jobs, s3_url)  # ✅ Pass the jobs list to send_email()

        return {"statusCode": 200, "body": json.dumps("Success")}
    
    except Exception as e:
        print(f"Error: {str(e)}")  # ✅ Log errors for debugging
        return {"statusCode": 500, "body": json.dumps(str(e))}