# Use the official PostgreSQL image as the base image
FROM pgvector/pgvector:pg14

# Set the working directory
WORKDIR /app

# Expose the port
EXPOSE 5432

# Run the application
CMD ["postgres"]