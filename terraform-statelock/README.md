# Terraform "Error acquiring the state lock": 7 causes on an S3 backend, reproduced and fixed live

🎬 Watch the video: https://youtu.be/gZGaUoDeQzo

Every error in the video is real output from **Terraform v1.17.2** with an **S3 backend and `use_lockfile = true`**
(the native S3 lock, no DynamoDB table). The S3 is **RustFS** (`rustfs/rustfs:1.0.6`) in a local Docker container, so
you need no cloud account. The lock is a file next to the state, `orders/terraform.tfstate.tflock`, and Terraform
writes it only if it doesn't exist yet (`If-None-Match: *`). If it exists, S3 answers 412 and you get the error.

## What you need
Docker, Terraform 1.11 or newer (`use_lockfile` is GA since 1.11), and the AWS CLI v2. Two terminals: one plays the
CI pipeline, one is you.

## Start
Pick your own local keys for the lab (they only exist in your container):
```bash
export LAB_ADMIN_KEY=labadmin LAB_ADMIN_SECRET=change-me-admin
export LAB_CI_SECRET=change-me-orders-ci

docker run -d --name ck-tf-s3 -p 127.0.0.1:9000:9000 \
  -e RUSTFS_ACCESS_KEY=$LAB_ADMIN_KEY -e RUSTFS_SECRET_KEY=$LAB_ADMIN_SECRET \
  -v ck-tf-s3-data:/data rustfs/rustfs:1.0.6
```
Port 9000 taken? Use e.g. `-p 127.0.0.1:9500:9000` and change `localhost:9000` in the three `backend.tf` files and
in `.lab/aws-config` below (the `rc alias` line stays on 9000: it runs inside the container).
AWS profiles for the lab, kept out of your real `~/.aws` (run this from the `terraform-statelock` folder):
```bash
mkdir -p .lab
cat > .lab/aws-config <<EOF
[profile admin]
region = us-east-1
endpoint_url = http://localhost:9000
[profile orders-ci]
region = us-east-1
endpoint_url = http://localhost:9000
EOF
cat > .lab/aws-credentials <<EOF
[admin]
aws_access_key_id = $LAB_ADMIN_KEY
aws_secret_access_key = $LAB_ADMIN_SECRET
[orders-ci]
aws_access_key_id = orders-ci
aws_secret_access_key = $LAB_CI_SECRET
EOF
export AWS_CONFIG_FILE=$PWD/.lab/aws-config AWS_SHARED_CREDENTIALS_FILE=$PWD/.lab/aws-credentials
```
The bucket, and the `orders-ci` user with the full policy (`aws s3 mb` fails on RustFS, `create-bucket` works):
```bash
AWS_PROFILE=admin aws s3api create-bucket --bucket tfstate

docker cp 05-no-delete-permission/fixed/policy.json ck-tf-s3:/tmp/fixed.json
docker cp 05-no-delete-permission/broken/policy.json ck-tf-s3:/tmp/broken.json
docker exec ck-tf-s3 rc alias set lab http://127.0.0.1:9000 $LAB_ADMIN_KEY $LAB_ADMIN_SECRET
docker exec ck-tf-s3 rc admin user add lab orders-ci $LAB_CI_SECRET
docker exec ck-tf-s3 rc admin policy create lab orders-ci /tmp/fixed.json
docker exec ck-tf-s3 rc admin policy create lab orders-ci-nodelete /tmp/broken.json
docker exec ck-tf-s3 rc admin policy attach lab orders-ci --user orders-ci
```
The orders stack. Every apply replaces `terraform_data.db_migration` (`triggers_replace = timestamp()`) and its
migration sleeps `migration_seconds` (40 by default), so every apply holds the lock for about 40 s:
```bash
export AWS_PROFILE=orders-ci
cd orders
terraform init
terraform apply -auto-approve -var migration_seconds=1
```
In **both** terminals, export `AWS_CONFIG_FILE`, `AWS_SHARED_CREDENTIALS_FILE` and `AWS_PROFILE=orders-ci`, and work in
`orders/`. To see the lock file itself:
```bash
aws s3 cp s3://tfstate/orders/terraform.tfstate.tflock -     # "(404) ... Not Found" when nothing holds the lock
```
Lock IDs are random. In the video the lab pinned the IDs of the stale locks (causes 3, 4 and 5) so the force-unlock
commands could be typed on camera; on your machine, copy the ID from Lock Info.

## Break, read, fix
"Pipeline" below means: in the other terminal, `terraform apply -auto-approve` (it holds the lock about 40 s).

| # | Cause | Do this | What you'll see | Fix |
|---|---|---|---|---|
| 1 | Another run holds the lock | Pipeline, then `terraform apply` | `Error: Error acquiring the state lock` at once, with `StatusCode: 412` ... `api error PreconditionFailed: At least one of the pre-conditions you specified did not hold`, and Lock Info (ID, Path, Operation, Who, Version, Created) | Let the other run finish: it removes its own lock |
| 2 | `-lock-timeout` too short | Pipeline, then `terraform apply -auto-approve -lock-timeout=5s` | `Acquiring state lock. This may take a few moments...`, 5 s of retrying, then the same error | `-lock-timeout=90s`: it gets the lock after the pipeline finishes, `Apply complete!`, exit code 0. In CI, longer than your slowest apply |
| 3 | A killed run leaves its lock | Pipeline, and 5 s in, `kill -9` it (e.g. `pkill -9 -f "terraform apply"`). Then `terraform plan` | The error, and `Created:` is the dead run. Ctrl-C does **not** do this: `Error: execution halted`, and the lock is released | Check nothing runs (`pgrep -fl "terraform apply"`, your CI runs, your team), then `terraform force-unlock <ID from Lock Info>`, answer `yes`: `Terraform state has been successfully unlocked!` |
| 4 | force-unlock with the wrong ID | Make a stale lock as in 3, then `terraform force-unlock 1234`, answer `yes` | `Failed to unlock state: lock ID '1234' does not match the existing lock ID '...'`. It asks for yes first and checks the ID after | The ID from the current Lock Info, never one from an older error |
| 5 | Can't delete its own lock | Swap the policy (below), then `terraform apply -auto-approve` | The migration runs, then `Error: Error releasing the state lock` ... `failed to delete the lock file: operation error S3: DeleteObject, https response error StatusCode: 403` ... `api error AccessDenied: Access Denied`, exit code 1. Every later run: the acquiring error. force-unlock as `orders-ci` gets the same 403 | `diff 05-no-delete-permission/{broken,fixed}/policy.json`: `s3:DeleteObject` on `arn:aws:s3:::tfstate/*.tflock`. Swap back, then force-unlock |
| 6 | Two stacks, one state key | Pipeline, then `cd ../06-same-key/broken && terraform init && terraform apply -auto-approve` | The error in the payments stack, with `Path: tfstate/orders/terraform.tfstate`. Once the lock is free, `terraform plan` says `Plan: 1 to add, 0 to change, 3 to destroy` (the orders resources). **Don't apply it** | `06-same-key/fixed`: its own key `payments/terraform.tfstate`, plus `deploy.yml` with a concurrency group per state, `cancel-in-progress: false` and `-lock-timeout=10m` |
| 7 | `-lock=false` | Pipeline, then `terraform apply -lock=false -auto-approve -var enable_promo=true -var migration_seconds=1` | No warning, `Apply complete!`. `terraform state list` shows `local_file.promo[0]`. When the pipeline finishes, it's gone from the state, `ls out` still shows `promo.env`, and `terraform plan -var enable_promo=true` says `local_file.promo[0] will be created`: a lost update | Never apply with `-lock=false`. Wait for the lock with `-lock-timeout` |

Swap the policy for cause 5, and back:
```bash
docker exec ck-tf-s3 rc admin policy detach lab orders-ci --user orders-ci
docker exec ck-tf-s3 rc admin policy attach lab orders-ci-nodelete --user orders-ci
# fix:
docker exec ck-tf-s3 rc admin policy detach lab orders-ci-nodelete --user orders-ci
docker exec ck-tf-s3 rc admin policy attach lab orders-ci --user orders-ci
```

## In production
- `use_lockfile` became generally available in Terraform 1.11, and DynamoDB-based locking is deprecated in its favour.
- The lock file needs `s3:GetObject`, `s3:PutObject` and `s3:DeleteObject` (cause 5 is the missing delete).
- A GitHub Actions concurrency group runs at most one job at a time, but a newer pending run cancels an older pending one.
- HCP Terraform queues runs per workspace and processes them in order.
- This lab covers the S3 backend with `use_lockfile`. DynamoDB lock tables and other backends are not shown.

## Clean up
```bash
docker rm -f ck-tf-s3 && docker volume rm ck-tf-s3-data
rm -rf .lab orders/.terraform* orders/out 06-same-key/*/.terraform* 06-same-key/*/out
```

Need help with Terraform, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
