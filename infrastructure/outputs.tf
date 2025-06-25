output "api_gateway_invoke_url" {
  description = "The invoke URL for the API Gateway."
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "events_function_name" {
  description = "The name of the events Lambda function."
  value       = aws_lambda_function.events_function.function_name
}

output "events_table_name" {
  description = "The name of the events DynamoDB table."
  value       = aws_dynamodb_table.events_table.name
}
