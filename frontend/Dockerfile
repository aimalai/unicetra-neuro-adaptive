# Use an official Node.js lightweight image
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json (if it exists) first to leverage Docker caching
COPY package*.json ./

# Install the necessary Node dependencies
RUN npm install

# Copy the rest of your frontend code into the container
COPY . .

# Expose the standard Vite/SvelteKit development port
EXPOSE 5173

# Command to run the Svelte development server, binding to all network interfaces
# so it is accessible from the host machine
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]