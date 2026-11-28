resource "random_pet" "db_name" {
  prefix = "orders-${var.environment}"
}

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "local_file" "orders_config" {
  filename = "${path.module}/out/orders.env"
  content  = <<-EOT
    DB_NAME=${random_pet.db_name.id}
    DB_USER=orders
    ENVIRONMENT=${var.environment}
  EOT
}

resource "terraform_data" "db_migration" {
  triggers_replace = timestamp()

  provisioner "local-exec" {
    command = "echo migrating ${random_pet.db_name.id}; sleep ${var.migration_seconds}; echo done"
  }

  depends_on = [local_file.orders_config]
}

resource "local_file" "promo" {
  count    = var.enable_promo ? 1 : 0
  filename = "${path.module}/out/promo.env"
  content  = "PROMO_CODE=BLACKFRIDAY\n"
}

output "db_name" {
  value = random_pet.db_name.id
}
