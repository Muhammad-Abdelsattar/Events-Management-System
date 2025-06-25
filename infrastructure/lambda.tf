data "archive_file" "lambda_zip_events" {
  type        = "zip"
  source_dir  = "${path.module}/../build"
  output_path = "${path.module}/../build.zip"
}

resource "aws_lambda_function" "events_function" {
  function_name = var.events_function_name
  handler       = "main.handler"
  runtime       = "python3.12"
  memory_size   = 256
  timeout       = 15
  role          = aws_iam_role.lambda_exec_role_events.arn
  filename      = data.archive_file.lambda_zip_events.output_path
  source_code_hash = data.archive_file.lambda_zip_events.output_base64sha256

  environment {
    variables = {
      BASE_PATH         = replace(var.events_function_path, "/{proxy+}", "")
      EVENTS_TABLE_NAME = var.events_table_name
    }
  }
}
