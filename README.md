# Incident Management System

## Summary

This is a web-based [**Incident Management System**](doc/Incident.md) designed to help teams track and manage incidents effectively. It provides a _centralized platform_ for **reporting**, **tracking**, **resolving** incidents.

Conducting [**Postmortems**](doc/Postmortem.md), ensuring a **streamlined workflow**, **clear communication**, and **continuous improvement**.

## Tech Stack

This project is built with a modern and robust technology stack:

- **Backend:** **Python** with the **FastAPI** _async_ framework.
- **Database:** **PostgreSQL** for reliable and relational data storage.
- **Task Queue:** **Celery** for running asynchronous background tasks.
- **Message Broker & Cache:** **Redis** to work with Celery and for caching purposes.
- **Containerization:** **Docker** and **Docker Compose** for creating a consistent development and deployment environment.
- **Frontend:** Standard **HTML**, **CSS**, and **JavaScript** for the user interface.

## Features

- **User Authentication & Authorization:**

  - Secure user registration to create a new account.
  - **JWT-based authentication:** User login is handled via JSON Web Tokens (JWT) for secure and stateless authentication.
  - **Role-Based Access Control (RBAC):** The system supports different user roles (e.g., administrator, user), with specific permissions for actions like creating, updating, and managing incidents.
  - Password hashing for enhanced security.

- **Incident Reporting:**

  - Create new incidents with a title, detailed description, and priority level.
  - Each incident is automatically assigned a unique ID and timestamp.

- **Automated Incident Creation:**

  - Define custom filters to monitor alerts from an external alert manager.
  - Automatically create a new incident in the system when an alert matches your predefined criteria for critical issues.

- **Incident Tracking and Management:**

  - A central dashboard to view all reported incidents in a clear, tabular format.
  - Each incident in the list displays its ID, title, status, priority, and creation date.
  - Ability to update the status of an incident (e.g., "Open", "In Progress", "Closed").

- **Persistent Storage:**
  - Incidents and user data are stored in a relational database, ensuring data is saved between sessions.

## Installation (with Docker)

This project is configured to run in a Docker container, which makes the setup process straightforward.

### Prerequisites

- **Docker:** You will need to have Docker installed on your system. For Linux, follow the [official Docker installation guide](https://docs.docker.com/engine/install/).
- **Docker Compose:** Install Docker Compose following the [official installation guide](https://docs.docker.com/compose/install/). On most Linux distributions, you can install it via package manager:

  ```bash
  # Ubuntu/Debian
  sudo apt update -y
  sudo apt install -y docker-compose-plugin

  # CentOS/RHEL/Fedora
  sudo yum install -y docker-compose-plugin
  ```

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/mhrdq8i/asas.git
   ```

2. **Navigate to the project directory**

   ```bash
   cd asas
   ```

3. **Set up environment variables**

   Copy the example environment file and configure it as needed:

   ```bash
   cp .env.example docker/.env.prod
   ```

   Edit `docker/.env.prod` to customize your configuration (database credentials, JWT secret, etc.):

   ```bash
   # Use your preferred editor
   nano docker/.env.prod
   # or
   vim docker/.env.prod
   ```

4. **Build and run the containers**

   Navigate to the docker directory and use Docker Compose to build and start the services:

   ```bash
   cd docker
   docker compose up --build -d
   ```

5. **Access the application**

   Once the containers are running, you can access the application:

   - **Web Application:** [http://localhost:80] (via nginx proxy)
   - **Direct API Access:** [http://localhost:8000] (FastAPI backend)

6. **Stopping the application**

   To stop the running containers, use the following command from the docker directory:

   ```bash
   docker compose down
   ```

### Services

The application consists of the following services:

- **nginx:** Reverse proxy server (port 80)
- **backend:** FastAPI application (port 8000)
- **database:** PostgreSQL database (port 5432, internal)
- **redis:** Redis cache and message broker (port 6379, internal)
- **celery_worker:** Background task processor
- **celery_beat:** Periodic task scheduler

### Project Structure

After following the installation steps, your Docker-related files will be organized as follows:

```
asas/
├── docker/
│   ├── .env.prod              # Environment variables
│   ├── docker-compose.yml     # Docker Compose configuration
│   ├── docker-run.sh          # Management script
│   ├── dockerfile             # Backend service Dockerfile
│   └── nginx.conf             # Nginx configuration
├── src/                       # Application source code
└── .env.example              # Example environment file
```

### Common Docker Commands

Here are some useful Docker Compose commands for managing the application:

**Option 1: Using the provided shell script (recommended)**

```bash
# Navigate to docker directory
cd docker

# Make the script executable
chmod +x docker-run.sh

# Start the application
./docker-run.sh

# Start with rebuild
./docker-run.sh "up --build -d"

# Stop the application
./docker-run.sh "down"

# View logs
./docker-run.sh "logs -f"
```

**Option 2: Manual Docker Compose commands**

```bash
# Navigate to docker directory (if not already there)
cd docker

# Start the application
docker compose up -d

# Start with rebuild
docker compose up --build -d

# Stop the application
docker compose down

# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f backend

# Restart a specific service
docker compose restart backend

# Check service status
docker compose ps
```

### Troubleshooting

**Permission Issues:**
If you encounter permission issues with Docker, you may need to add your user to the docker group:

```bash
sudo usermod -aG docker $USER
# Log out and log back in for changes to take effect
```

**Port Already in Use:**
If ports 80 or 8000 are already in use, you can modify the port mappings in `docker/docker-compose.yml`:

```yaml
ports:
  - "8080:80" # Change host port from 80 to 8080
```

**Database Connection Issues:**
Ensure that the database service is fully started before other services by checking logs:

```bash
docker compose logs database
```

## API Documentation

This application provides a full REST API for interacting with the incident management system programmatically.

The API documentation is automatically generated by FastAPI and is available at the following endpoints when the application is running:

- **Swagger UI:** [http://localhost:8000/docs]
- **ReDoc:** [http://localhost:8000/redoc]

These interfaces allow you to explore all available API endpoints, view their parameters, and test them directly from your browser.
