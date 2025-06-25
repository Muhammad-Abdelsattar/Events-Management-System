resource "aws_iam_role" "lambda_exec_role_events" {
  name = "lambda-exec-role-events"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "dynamodb_policy_events" {
  name        = "dynamodb-policy-events"
  description = "Policy for full access to the events DynamoDB table"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "dynamodb:*",
        Effect   = "Allow",
        Resource = aws_dynamodb_table.events_table.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "dynamodb_attachment_events" {
  role       = aws_iam_role.lambda_exec_role_events.name
  policy_arn = aws_iam_policy.dynamodb_policy_events.arn
}

resource "aws_iam_role_policy_attachment" "lambda_logs_events" {
  role       = aws_iam_role.lambda_exec_role_events.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
