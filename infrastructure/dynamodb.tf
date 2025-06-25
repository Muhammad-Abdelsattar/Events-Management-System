resource "aws_dynamodb_table" "events_table" {
  name         = var.events_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "eventId"

  attribute {
    name = "eventId"
    type = "S"
  }

  attribute {
    name = "organizerId"
    type = "S"
  }

  global_secondary_index {
    name            = "organizerId-index"
    hash_key        = "organizerId"
    projection_type = "ALL"
  }
}
