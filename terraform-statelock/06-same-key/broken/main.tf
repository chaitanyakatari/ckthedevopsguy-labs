terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

resource "local_file" "payments_config" {
  filename = "${path.module}/out/payments.env"
  content  = "PAYMENTS_PROVIDER=stripe\nENVIRONMENT=prod\n"
}
