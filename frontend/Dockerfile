FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --legacy-peer-deps && \
    ls -la node_modules/.bin/vite && \
    echo "Vite installed successfully"
COPY . .
EXPOSE 5173
CMD ["node_modules/.bin/vite", "--host", "0.0.0.0", "--port", "5173"]
