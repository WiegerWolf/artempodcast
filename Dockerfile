# Use an official lightweight Alpine image as a parent image
FROM alpine:latest

# Set the working directory in the container
WORKDIR /usr/src/app

# Install hugo and other dependencies
RUN apk add --no-cache hugo git npm python3 py3-pip

# Optional: Install any other software or libraries you need for development
# RUN apk add --no-cache <your-software>

# Set up the user. Replace 1000 with your user/group id.
RUN addgroup -g 1000 -S user && \
    adduser -u 1000 -S user -G user
USER user

# Expose port for Hugo server
EXPOSE 1313
