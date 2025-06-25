data "aws_cognito_user_pool" "existing_pool" {
  user_pool_id= var.user_pool_id
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "MyApiGateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_authorizer" "cognito_auth" {
  api_id           = aws_apigatewayv2_api.http_api.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-authorizer"

  jwt_configuration {
    audience = [var.cognito_client_id]
    issuer   = "https://cognito-idp.${data.aws_cognito_user_pool.existing_pool.region}.amazonaws.com/${data.aws_cognito_user_pool.existing_pool.id}"
  }
}

resource "aws_apigatewayv2_integration" "integration_events" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.events_function.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "route_events" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY ${var.events_function_path}"
  target    = "integrations/${aws_apigatewayv2_integration.integration_events.id}"

  authorizer_id      = aws_apigatewayv2_authorizer.cognito_auth.id
  authorization_type = "JWT"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gw_permission_events" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.events_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
