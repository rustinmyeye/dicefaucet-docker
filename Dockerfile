FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    git \
    sqlite3 \
    expect

# Set working directory
WORKDIR /app

# Clone EWC repository
RUN git clone https://github.com/ThierryM1212/ewc.git

# Change working directory to the EWC directory
WORKDIR /app/ewc

# Install EWC dependencies
RUN npm install

# Build EWC
RUN npm run build

# Install EWC locally
RUN npm run localinstall

# Copy the expect script into the container
COPY ewc_expect_script.sh .

# Make the script executable
RUN chmod +x ewc_expect_script.sh

# Run the expect script to automate the input of the wallet password
RUN ./ewc_expect_script.sh

# Change working directory back to the parent directory
WORKDIR /app

# Copy necessary files
COPY entrypoint.sh .
COPY dicefaucet.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Set the entrypoint for the container
ENTRYPOINT ["./entrypoint.sh"]
