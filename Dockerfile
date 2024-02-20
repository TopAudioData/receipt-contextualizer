# Use the official PostgreSQL image as the base image
FROM postgres:13.2

# Set the working directory
WORKDIR /app

# Expose the port
EXPOSE 5432

# Run the application
CMD ["postgres"]