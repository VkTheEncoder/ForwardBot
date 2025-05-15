# Use an official Python runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code
COPY forward_bot.py ./

# Expose nothing (bot is outbound-only)
# Set default command
CMD ["python", "forward_bot.py"]
