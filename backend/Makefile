all: build deploy

ORIGIN ?= http://localhost:8080
STACKNAME ?= aws-serverless-shopping-cart
AWS_PROFILE ?= default

# File template nằm cùng thư mục Makefile con
TEMPLATE_FILE = $(CURDIR)/$(TEMPLATE).yaml

build:
	@echo "Building SAM template: $(TEMPLATE_FILE)"
	@test -f $(TEMPLATE_FILE) || (echo "ERROR: Template file $(TEMPLATE_FILE) NOT FOUND!" && exit 1)
	@sam build \
		--template-file $(TEMPLATE_FILE) \
		--base-dir $(CURDIR) \
		--profile $(AWS_PROFILE)

deploy:
	@echo "Deploying stack $(STACKNAME)-$(TEMPLATE) ..."
	@sam deploy \
		--stack-name $(STACKNAME)-$(TEMPLATE) \
		--s3-bucket $(S3_BUCKET) \
		--region $(REGION) \
		--capabilities CAPABILITY_NAMED_IAM \
		--parameter-overrides AllowedOrigin=$(ORIGIN) \
		--profile $(AWS_PROFILE) \
		--no-fail-on-empty-changeset

delete:
	@echo "Deleting stack $(STACKNAME)-$(TEMPLATE) ..."
	@aws cloudformation delete-stack \
		--stack-name $(STACKNAME)-$(TEMPLATE) \
		--region $(REGION) \
		--profile $(AWS_PROFILE)

	@aws cloudformation wait stack-delete-complete \
		--stack-name $(STACKNAME)-$(TEMPLATE) \
		--profile $(AWS_PROFILE)

	@echo "Stack deleted."

tests:
	pytest -v

.PHONY: build deploy delete tests
