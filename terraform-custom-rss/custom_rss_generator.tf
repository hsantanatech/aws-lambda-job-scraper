resource "aws_lambda_layer_version" "rss_dependencies_layer" {
  filename            = "lambda_layer_payload.zip"
  layer_name          = "rss_dependencies_layer"
  compatible_runtimes = ["python3.11"]
}

resource "aws_lambda_function" "cloud_jobs_rss_lambda" {
  filename         = "lambda_function_payload.zip"
  function_name    = "cloud_jobs_rss_lambda"
  runtime          = "python3.11"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.lambda_exec_role.arn
  source_code_hash = filebase64sha256("lambda_function_payload.zip")
  
  layers = [aws_lambda_layer_version.rss_dependencies_layer.arn]

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }
}
