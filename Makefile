# ===================== GLOBAL CONFIG =====================
AWS_PROFILE ?= default
REGION ?= ap-southeast-2

# Lấy AWS Account ID bằng đúng profile
ACCOUNT_ID := $(shell aws sts get-caller-identity --profile $(AWS_PROFILE) --query Account --output text)

# S3 bucket dùng để deploy SAM
S3_BUCKET = aws-serverless-shopping-cart-src-$(ACCOUNT_ID)-$(REGION)


# ===================== DEFAULT TARGET =====================
all: backend frontend-build


# ===================== BACKEND DEPLOY =====================
backend: create-bucket
	$(MAKE) -C backend TEMPLATE=auth                S3_BUCKET=$(S3_BUCKET) REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE)
	$(MAKE) -C backend TEMPLATE=product-mock       S3_BUCKET=$(S3_BUCKET) REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE)
	$(MAKE) -C backend TEMPLATE=shoppingcart-service S3_BUCKET=$(S3_BUCKET) REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE)

backend-delete:
	$(MAKE) -C backend delete TEMPLATE=auth                REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE)
	$(MAKE) -C backend delete TEMPLATE=product-mock       REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE)
	$(MAKE) -C backend delete TEMPLATE=shoppingcart-service REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE)

backend-tests:
	$(MAKE) -C backend tests REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE)


# ===================== CREATE S3 BUCKET =====================
create-bucket:
	@echo "Checking if S3 bucket exists: s3://$(S3_BUCKET)"
	@aws s3api head-bucket --profile $(AWS_PROFILE) --bucket $(S3_BUCKET) 2>/dev/null || \
		(echo "Bucket not found. Creating s3://$(S3_BUCKET) ..." ; \
		if [ "$(REGION)" = "us-east-1" ]; then \
			aws s3api create-bucket --profile $(AWS_PROFILE) --bucket $(S3_BUCKET) --region $(REGION); \
		else \
			aws s3api create-bucket --profile $(AWS_PROFILE) --bucket $(S3_BUCKET) --region $(REGION) \
			--create-bucket-configuration LocationConstraint=$(REGION); \
		fi)


# ===================== FRONTEND =====================
frontend-serve:
	$(MAKE) -C frontend serve REGION=$(REGION)

frontend-build:
	$(MAKE) -C frontend build REGION=$(REGION)

.PHONY: all backend backend-delete backend-tests create-bucket frontend-serve frontend-build
