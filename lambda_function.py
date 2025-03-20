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
]
S3_BUCKET = "hs-my-jobsearch-bucket"
SES_SENDER_EMAIL = "hsantana@renacentis.org"  # Must be verified in SES
SES_RECIPIENT_EMAIL = "hsantana@renacentis.org"  # Can be verified if in sandbox mode

def fetch_rss_jobs():
    """Fetch job listings from RSS feeds."""
    jobs = []
    for feed_url in RSS_FEED_URLS:
        try:
            response = requests.get(feed_url)
            if response.status_code != 200:
                continue
            root = ET.fromstring(response.content)
            for item in root.findall(".//item"):
                title = item.find("title").text or "No Title"
                link = item.find("link").text or "No Link"
                pub_date = item.find("pubDate").text or "No Date"
                source = feed_url
                jobs.append({"title": title, "link": link, "pub_date": pub_date, "source": source})
        except Exception as e:
            print(f"❌ Error fetching RSS feed: {feed_url} - {e}")
    return jobs

def generate_rss(jobs):
    """Generate an RSS XML feed from job listings."""
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "AWS Cloud Engineer Jobs"
    ET.SubElement(channel, "link").text = "https://your-api-gateway-endpoint.com/jobs/rss"
    ET.SubElement(channel, "description").text = "Aggregated AWS Cloud Engineer Job Listings"
    ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    for job in jobs:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = job["title"]
        ET.SubElement(item, "link").text = job["link"]
        ET.SubElement(item, "description").text = job["title"]
    return ET.tostring(rss, encoding='utf-8', method='xml')

def send_email_notification(jobs):
    """Send job listings via AWS SES email."""
    try:
        if not jobs:
            print("📭 No new jobs to send. Skipping email notification.")
            return

        subject = f"📌 New Cloud Engineer Jobs - {datetime.utcnow().strftime('%Y-%m-%d')}"
        body = "\n".join([f"{job['title']} - {job['link']}" for job in jobs])

        response = ses.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={"ToAddresses": [SES_RECIPIENT_EMAIL]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}}
            }
        )

        print(f"📧 Email sent successfully! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")

def lambda_handler(event, context):
    """AWS Lambda entry point."""
    try:
        print(f"🔎 Event received: {json.dumps(event)}")  # Debugging

        jobs = fetch_rss_jobs()

        if not jobs:
            print("⚠️ No jobs were fetched. Returning JSON error message.")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "⚠️ No jobs were fetched. Check your RSS source URLs."})
            }

        rss_feed = generate_rss(jobs)

        # Send an email with job listings
        send_email_notification(jobs)

        # ✅ Detect JSON request correctly
        headers = event.get("headers", {})
        accept_header = headers.get("accept", "").lower()  # Normalize case

        print(f"📡 Accept Header Received: {accept_header}")  # Debugging

        if "application/json" in accept_header:
            print("🔍 JSON requested, returning JSON response")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(jobs)
            }

        print("📡 Returning RSS feed as default")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/rss+xml"},
            "body": rss_feed.decode('utf-8') if isinstance(rss_feed, bytes) else rss_feed
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Error fetching jobs: {str(e)}"})
        }