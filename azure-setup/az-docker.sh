#!/bin/bash

# Azure CLI Docker wrapper
# Usage: ./az-docker.sh <azure-cli-commands>
# Example: ./az-docker.sh login
# Example: ./az-docker.sh account show

# Create .azure directory if it doesn't exist
mkdir -p "$HOME/.azure"

docker run -it --rm \
  -v "$HOME/.azure:/root/.azure:rw" \
  -v "$(pwd)/..:/work:rw" \
  -w /work/azure-setup \
  mcr.microsoft.com/azure-cli:latest \
  az "$@"
