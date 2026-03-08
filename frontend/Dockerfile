FROM node:20-alpine

WORKDIR /app

# Copy package.json + package-lock.json from the correct folder
COPY package*.json ./

RUN npm install

# Copy the rest of the app
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
