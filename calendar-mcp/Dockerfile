# calendar-mcp/Dockerfile
FROM node:20-slim

WORKDIR /app

# Install the published npm package
RUN npm install @cocal/google-calendar-mcp@latest

# OAuth credentials and tokens are mounted at runtime
VOLUME ["/app/credentials"]

# HTTP transport on port 3000
EXPOSE 3000

# Start in HTTP transport mode
CMD ["node", "node_modules/@cocal/google-calendar-mcp/build/index.js", "--transport", "http", "--port", "3000", "--host", "0.0.0.0"]
