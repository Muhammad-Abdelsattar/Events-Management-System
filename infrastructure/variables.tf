variable "aws_region" {
  description = "The AWS region to deploy the resources."
  type        = string
  default     = "us-east-1"
}


variable "user_pool_id" {
  description = "The NAME of the existing Cognito User Pool."
  type        = string
}

variable "cognito_client_id" {
  description = "The client id of Cognito User Pool."
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
