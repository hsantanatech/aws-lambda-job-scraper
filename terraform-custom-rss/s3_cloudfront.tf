# 🔹 Use the existing S3 bucket instead of creating a new one
data "aws_s3_bucket" "job_board" {
  bucket = "hs-my-jobsearch-bucket"
}

# 🔹 Enable Public Access for Static Website Hosting
resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket                  = data.aws_s3_bucket.job_board.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# 🔹 Configure S3 as a Static Website
resource "aws_s3_bucket_website_configuration" "website_config" {
  bucket = data.aws_s3_bucket.job_board.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# 🔹 S3 Bucket Policy to Allow Public Read Access
resource "aws_s3_bucket_policy" "public_read" {
  bucket = data.aws_s3_bucket.job_board.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${data.aws_s3_bucket.job_board.arn}/*"
      }
    ]
  })
}

# 🔹 Upload Index Page to S3
resource "aws_s3_object" "index" {
  bucket = data.aws_s3_bucket.job_board.id
  key    = "index.html"
  source = "../index.html"  # ✅ Ensure this file exists
  content_type = "text/html"
}

# 🔹 CloudFront Distribution
resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = data.aws_s3_bucket.job_board.bucket_regional_domain_name
    origin_id   = "S3Origin"
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3Origin"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}