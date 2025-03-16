variable "region" {
  default = "us-east-2"
}

variable "account_id" {
  default = "342311524694"
}

variable "lambda_function_name" {
  default = "MyJobFeedScrubFunction"
}

variable "s3_bucket" {
  default = "hs-my-jobsearch-bucket"
}

variable "email_sender" {
  default = "hsantana@renacentis.org"
}

variable "email_recipient" {
  default = "hsantana@renacentis.org"
}