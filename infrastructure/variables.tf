variable "aws_region" {
  description = "The AWS region to deploy the resources."
  type        = string
  default     = "us-east-1"
}

variable "cognito_user_pool_id" {
  description = "The ID of the existing Cognito User Pool."
  type        = string
}

variable "events_function_name" {
  description = "The name of the events Lambda function."
  type        = string
  default     = "events-function"
}

variable "events_table_name" {
  description = "The name of the events DynamoDB table."
  type        = string
  default     = "events-table"
}

variable "events_function_path" {
  description = "The API Gateway path for the events function."
  type        = string
  default     = "/events/{proxy+}"
}
