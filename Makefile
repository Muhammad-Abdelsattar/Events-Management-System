# Makefile for managing the project's AWS infrastructure and Lambda dependencies.
# All commands are run from the project root.

# Use a more specific shell.
SHELL := /bin/bash

# ====================================================================================
# VARIABLES
# ====================================================================================

# Directories
TF_DIR := infrastructure
LAMBDA_SRC_DIR := events_manager_lambda
BUILD_DIR := build

# Terraform command with the -chdir flag to run it in the correct directory
TERRAFORM := terraform -chdir=$(TF_DIR)

# ====================================================================================
# HELP
# ====================================================================================

.DEFAULT_GOAL := help

# Self-documenting targets.
.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ====================================================================================
# PROJECT WORKFLOW
# ====================================================================================

.PHONY: deps
deps: clean ## Build the Lambda package in the 'build/' directory.
	@echo "📦 Creating Lambda package in '$(BUILD_DIR)' directory..."
	@# 1. Create the build directory
	@mkdir -p $(BUILD_DIR)
	@# 2. Copy the Lambda source code into the build directory
	@cp -r $(LAMBDA_SRC_DIR)/* $(BUILD_DIR)/
	@# 3. Install Python dependencies directly into the build directory
	@pip install --quiet --requirement "$(LAMBDA_SRC_DIR)/requirements.txt" --target "$(BUILD_DIR)"
	@echo "✅ Lambda package is ready in '$(BUILD_DIR)'."

.PHONY: init
init: deps ## Initialize Terraform (downloads providers). Depends on 'deps'.
	@echo "🚀 Initializing Terraform in '$(TF_DIR)'..."
	@$(TERRAFORM) init -upgrade

.PHONY: plan
plan: init ## Generate a Terraform execution plan.
	@echo "📝 Generating Terraform plan..."
	@$(TERRAFORM) plan

.PHONY: apply
apply: init ## Apply the Terraform plan (prompts for confirmation).
	@echo "🚀 Applying Terraform configuration (will prompt for approval)..."
	@$(TERRAFORM) apply

.PHONY: destroy
destroy: init ## Destroy all Terraform-managed resources (prompts for confirmation).
	@echo "🔥 Destroying all resources (will prompt for approval)..."
	@$(TERRAFORM) destroy

# ====================================================================================
# UTILITY
# ====================================================================================

.PHONY: clean
clean: ## Remove the build directory and Terraform cache files.
	@echo "🧹 Cleaning up project..."
	@echo "--- Removing build artifacts and Terraform cache ---"
	@rm -rf $(BUILD_DIR)
	@rm -rf $(TF_DIR)/.terraform
	@rm -f $(TF_DIR)/.terraform.lock.hcl
	@rm -f $(TF_DIR)/*.zip
	@echo "✅ Cleanup complete."
