all: backend frontend-build

# REGION override từ CLI, ví dụ:
#   make backend REGION=ap-southeast-1
REGION ?= us-east-1

# Lấy AWS Account ID
ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)

# S3 bucket dùng để deploy SAM
S3_BUCKET = aws-serverless-shopping-cart-src-$(ACCOUNT_ID)-$(REGION)

# ====================== BACKEND DEPLOY ======================
backend: create-bucket
	$(MAKE) -C backend TEMPLATE=auth S3_BUCKET=$(S3_BUCKET) REGION=$(REGION)
	$(MAKE) -C backend TEMPLATE=product-mock S3_BUCKET=$(S3_BUCKET) REGION=$(REGION)
	$(MAKE) -C backend TEMPLATE=shoppingcart-service S3_BUCKET=$(S3_BUCKET) REGION=$(REGION)

backend-delete:
	$(MAKE) -C backend delete TEMPLATE=auth REGION=$(REGION)
	$(MAKE) -C backend delete TEMPLATE=product-mock REGION=$(REGION)
	$(MAKE) -C backend delete TEMPLATE=shoppingcart-service REGION=$(REGION)

backend-tests:
	$(MAKE) -C backend tests REGION=$(REGION)

# ====================== CREATE S3 BUCKET ======================
create-bucket:
	@echo "Checking if S3 bucket exists s3://$(S3_BUCKET)"
	@aws s3api head-bucket --bucket $(S3_BUCKET) 2>/dev/null || \
		(echo "Bucket not found. Creating s3://$(S3_BUCKET) ..." ; \
		if [ "$(REGION)" = "us-east-1" ]; then \
			aws s3api create-bucket --bucket $(S3_BUCKET) --region $(REGION); \
		else \
			aws s3api create-bucket --bucket $(S3_BUCKET) --region $(REGION) \
			--create-bucket-configuration LocationConstraint=$(REGION); \
		fi)

# ====================== FRONTEND ======================
frontend-serve:
	$(MAKE) -C frontend serve REGION=$(REGION)

frontend-build:
	$(MAKE) -C frontend build REGION=$(REGION)

.PHONY: all backend backend-delete backend-tests create-bucket frontend-serve frontend-build
