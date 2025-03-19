# Create an HTTP API
resource "aws_apigatewayv2_api" "rss_api" {
  name          = "rss-api"
  protocol_type = "HTTP"
}

# Create a Lambda integration for the API
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                   = aws_apigatewayv2_api.rss_api.id
  integration_type         = "AWS_PROXY"
  integration_uri          = aws_lambda_function.cloud_jobs_rss_lambda.invoke_arn
  payload_format_version   = "2.0"
}

# Set up a default route that sends all requests to the Lambda integration
resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.rss_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Deploy the API to a stage (auto deploy is enabled for simplicity)
resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.rss_api.id
  name        = "$default"
  auto_deploy = true
}

# Add permission for API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cloud_jobs_rss_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.rss_api.execution_arn}/*/*"
}
