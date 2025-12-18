#!/bin/bash

# Build Docker image with ADT URL from .env.docker
cd "$(dirname "$0")"

if [ -f .env.docker ]; then
  source .env.docker
  echo "Building with REACT_APP_ADT_URL: $REACT_APP_ADT_URL"
else
  echo "Error: .env.docker not found"
  exit 1
fi

docker build \
  --build-arg REACT_APP_ADT_URL="$REACT_APP_ADT_URL" \
  -t digital-twins-explorer:latest \
  .

echo ""
echo "Build complete! Run with:"
echo "docker run -p 3000:3000 digital-twins-explorer:latest"
