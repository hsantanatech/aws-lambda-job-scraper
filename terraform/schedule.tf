resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "job_scraper_schedule"
  schedule_expression = "rate(6 hours)"  # Adjust the interval as needed
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "job_scraper"
  arn       = aws_lambda_function.job_feed_scrub.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job_feed_scrub.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}