import json
import requests
import csv
import boto3
import os
import xml.etree.ElementTree as ET
from datetime import datetime

# AWS Resources
s3 = boto3.client('s3')
ses = boto3.client('ses', region_name='us-east-2')
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('JobListings')

# Configuration
RSS_FEED_URLS = [
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://rss.app/feeds/0mcW7nhSasSgLc5P.xml"
]  # ✅ Updated RSS feed
S3_BUCKET = "hs-my-jobsearch-bucket"
S3_FILE_NAME = f"jobs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
EMAIL_SENDER = "hsantana@renacentis.org"  # Must be verified in AWS SES
EMAIL_RECIPIENT = "hsantana@renacentis.org"

def is_job_new(job_link):
    """Check if a job already exists in DynamoDB."""
    response = table.get_item(Key={'job_link': job_link})
    return 'Item' not in response

def save_job_to_dynamodb(job_link, title, pub_date, source):
    """Store new job in DynamoDB to prevent duplicates."""
    table.put_item(Item={
        'job_link': job_link,
        'title': title,
        'pub_date': pub_date,
        'source': source
    })

def fetch_rss_jobs():
    """Fetch job listings from existing RSS feed(s)."""
    jobs = []
    for feed_url in RSS_FEED_URLS:
        try:
            print(f"🔍 Fetching RSS Feed: {feed_url}")
            response = requests.get(feed_url)
            if response.status_code != 200:
                print(f"❌ Failed to fetch RSS feed: {feed_url} - Status Code: {response.status_code}")
                continue
            root = ET.fromstring(response.content)
            for item in root.findall(".//item"):
                title = item.find("title").text or "No Title"
                link = item.find("link").text or "No Link"
                pub_date = item.find("pubDate").text or "No Date"
                source = "WeWorkRemotely"
                if is_job_new(link):
                    jobs.append([title, link, pub_date, source])
                    save_job_to_dynamodb(link, title, pub_date, source)
        except Exception as e:
            print(f"❌ Error fetching RSS feed: {feed_url} - {e}")
    return jobs

def generate_rss(jobs):
    """Generate an RSS XML feed from the job listings."""
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "AWS Cloud Engineer Jobs"
    ET.SubElement(channel, "link").text = "https://your-api-gateway-endpoint.com/jobs/rss"
    ET.SubElement(channel, "description").text = "Aggregated AWS Cloud Engineer Job Listings"
    ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    for job in jobs:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = job[0]
        ET.SubElement(item, "link").text = job[1]
        ET.SubElement(item, "description").text = job[0]  # or another field as needed
    return ET.tostring(rss, encoding='utf-8', method='xml')

def save_to_csv(jobs):
    """Save the job listings to a CSV file and upload it to S3."""
    local_file = "/tmp/" + S3_FILE_NAME  # Lambda's writable directory
    with open(local_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Job Title", "Link", "Published Date", "Source"])
        writer.writerows(jobs)
    s3.upload_file(local_file, S3_BUCKET, S3_FILE_NAME)
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{S3_FILE_NAME}"

def send_email(jobs, s3_url):
    """Send an email with job listings and a link to the CSV file."""
    subject = "🚀 New Job Listings Available!"
    job_list_html = "".join(
        f"<li><strong>{job[0]}</strong> - <a href='{job[1]}' target='_blank'>Apply Now</a> (Posted: {job[2]})<br>"
        f"<small>Source: <a href='{job[3]}' target='_blank'>{job[3]}</a></small></li>"
        for job in jobs[:25]  # ✅ Increased to 25 jobs per email
    )
    body_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            ul {{ padding: 0; list-style-type: none; }}
            li {{ margin-bottom: 8px; }}
            small {{ color: gray; }}
        </style>
    </head>
    <body>
        <h2>🚀 New Job Listings Available!</h2>
        <p>The latest job opportunities have been collected from multiple sources:</p>
        <ul>{job_list_html}</ul>
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
            }
        }
    )

def lambda_handler(event, context):
    """AWS Lambda entry point."""
    try:
        # Fetch jobs from all sources
        jobs = fetch_rss_jobs()
        
        if not jobs:
            print("⚠️ No jobs were fetched. Check your source URLs.")
            return {"statusCode": 200, "body": "⚠️ No jobs were fetched. Check your source URLs."}
        
        # Generate the RSS XML feed
        rss_feed = generate_rss(jobs)

        # Save jobs to CSV and send an email
        s3_url = save_to_csv(jobs)
        send_email(jobs, s3_url)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/rss+xml'},
            'body': rss_feed.decode('utf-8') if isinstance(rss_feed, bytes) else rss_feed
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(str(e))}
