output "lambda_function_name" {
  value       = aws_lambda_function.cloud_jobs_rss_lambda.function_name
  description = "Name of the deployed Lambda function"
}

output "lambda_layer_arn" {
  value       = aws_lambda_layer_version.rss_dependencies_layer.arn
  description = "ARN of the deployed Lambda layer"
}
