provider "aws" {
  region = var.region
}

resource "aws_lambda_function" "job_feed_scrub" {
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_exec.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  filename         = "${path.module}/../lambda_function.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda_function.zip")

  environment {
    variables = {
      S3_BUCKET       = var.s3_bucket
      EMAIL_SENDER    = var.email_sender
      EMAIL_RECIPIENT = var.email_recipient
    }
  }
}