variable "environment" {
  type    = string
  default = "prod"
}

variable "migration_seconds" {
  type    = number
  default = 40
}

variable "enable_promo" {
  type    = bool
  default = false
}
