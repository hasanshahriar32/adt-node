FROM node:20-alpine

# Install Python3 and Bash
RUN apk add --no-cache python3 bash

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application files
COPY . .

# Ensure start script is executable
RUN chmod +x start_simulation.sh

# Environment variables
ENV PORT=10000
EXPOSE 10000

# Start command
CMD ["./start_simulation.sh"]
