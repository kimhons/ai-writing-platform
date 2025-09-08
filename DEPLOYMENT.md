# Deployment Guide - AI Writing Platform

This guide provides comprehensive instructions for deploying the AI Writing Platform in various environments.

## 🚀 Quick Deployment Options

### 1. Local Development

```bash
# Clone the repository
git clone https://github.com/kimhons/ai-writing-platform.git
cd ai-writing-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"

# Run the application
python src/main.py
```

Access the application at `http://localhost:5000`

### 2. Docker Deployment

```bash
# Build and run with Docker
docker build -t ai-writing-platform .
docker run -p 5000:5000 -e OPENAI_API_KEY=your-key ai-writing-platform
```

### 3. Docker Compose (Recommended for Development)

```bash
# Set environment variables
echo "OPENAI_API_KEY=your-openai-api-key" > .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web
```

## 🌐 Production Deployment

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (recommended for production)
- Redis 7+ (for caching and sessions)
- SSL certificate (for HTTPS)
- Domain name

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/database

# Optional
ANTHROPIC_API_KEY=your-anthropic-api-key
REDIS_URL=redis://localhost:6379
FLASK_ENV=production
FLASK_DEBUG=0
```

### Database Setup

#### PostgreSQL Setup
```sql
-- Create database and user
CREATE DATABASE ai_writing_platform;
CREATE USER ai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_writing_platform TO ai_user;
```

#### Database Migration
```bash
# Initialize database tables
python src/main.py
# Tables will be created automatically on first run
```

### Production Server Setup

#### Using Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 src.main:app
```

#### Using uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Create uwsgi.ini
[uwsgi]
module = src.main:app
master = true
processes = 4
socket = /tmp/ai-writing-platform.sock
chmod-socket = 666
vacuum = true
die-on-term = true
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if serving directly)
    location /static {
        alias /path/to/ai-writing-platform/src/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## ☁️ Cloud Platform Deployment

### AWS Deployment

#### Using Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB Application**
   ```bash
   eb init ai-writing-platform
   ```

3. **Create Environment**
   ```bash
   eb create production
   ```

4. **Set Environment Variables**
   ```bash
   eb setenv OPENAI_API_KEY=your-key SECRET_KEY=your-secret
   ```

5. **Deploy**
   ```bash
   eb deploy
   ```

#### Using ECS (Container Service)

1. **Build and Push to ECR**
   ```bash
   # Create ECR repository
   aws ecr create-repository --repository-name ai-writing-platform

   # Build and tag image
   docker build -t ai-writing-platform .
   docker tag ai-writing-platform:latest 123456789012.dkr.ecr.region.amazonaws.com/ai-writing-platform:latest

   # Push to ECR
   docker push 123456789012.dkr.ecr.region.amazonaws.com/ai-writing-platform:latest
   ```

2. **Create ECS Task Definition**
   ```json
   {
     "family": "ai-writing-platform",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "ai-writing-platform",
         "image": "123456789012.dkr.ecr.region.amazonaws.com/ai-writing-platform:latest",
         "portMappings": [
           {
             "containerPort": 5000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "OPENAI_API_KEY",
             "value": "your-openai-api-key"
           }
         ]
       }
     ]
   }
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and Deploy**
   ```bash
   # Build and submit to Cloud Build
   gcloud builds submit --tag gcr.io/PROJECT-ID/ai-writing-platform

   # Deploy to Cloud Run
   gcloud run deploy ai-writing-platform \
     --image gcr.io/PROJECT-ID/ai-writing-platform \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars OPENAI_API_KEY=your-key
   ```

#### Using App Engine

1. **Create app.yaml**
   ```yaml
   runtime: python311
   
   env_variables:
     OPENAI_API_KEY: "your-openai-api-key"
     SECRET_KEY: "your-secret-key"
   
   automatic_scaling:
     min_instances: 1
     max_instances: 10
   ```

2. **Deploy**
   ```bash
   gcloud app deploy
   ```

### Microsoft Azure

#### Using App Service

1. **Create Resource Group**
   ```bash
   az group create --name ai-writing-platform-rg --location eastus
   ```

2. **Create App Service Plan**
   ```bash
   az appservice plan create --name ai-writing-platform-plan \
     --resource-group ai-writing-platform-rg --sku B1 --is-linux
   ```

3. **Create Web App**
   ```bash
   az webapp create --resource-group ai-writing-platform-rg \
     --plan ai-writing-platform-plan --name ai-writing-platform \
     --runtime "PYTHON|3.11"
   ```

4. **Configure Environment Variables**
   ```bash
   az webapp config appsettings set --resource-group ai-writing-platform-rg \
     --name ai-writing-platform --settings OPENAI_API_KEY=your-key
   ```

5. **Deploy Code**
   ```bash
   az webapp deployment source config --resource-group ai-writing-platform-rg \
     --name ai-writing-platform --repo-url https://github.com/kimhons/ai-writing-platform \
     --branch main --manual-integration
   ```

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   # Install Heroku CLI and login
   heroku login
   ```

2. **Create Heroku App**
   ```bash
   heroku create ai-writing-platform
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set OPENAI_API_KEY=your-openai-api-key
   heroku config:set SECRET_KEY=your-secret-key
   ```

4. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

## 🔧 Configuration Management

### Environment-Specific Configurations

#### Development
```python
# config/development.py
DEBUG = True
TESTING = False
DATABASE_URL = 'sqlite:///database/app.db'
SECRET_KEY = 'dev-secret-key'
```

#### Production
```python
# config/production.py
DEBUG = False
TESTING = False
DATABASE_URL = os.environ.get('DATABASE_URL')
SECRET_KEY = os.environ.get('SECRET_KEY')
```

### SSL/TLS Configuration

#### Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring and Logging

### Application Monitoring

#### Health Checks
```bash
# Check application health
curl https://your-domain.com/api/health
```

#### Log Configuration
```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler('logs/ai-writing-platform.log', 
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
```

### Performance Monitoring

#### Using New Relic
```bash
# Install New Relic
pip install newrelic

# Add to requirements.txt
echo "newrelic" >> requirements.txt

# Initialize
newrelic-admin generate-config YOUR_LICENSE_KEY newrelic.ini

# Run with New Relic
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn src.main:app
```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Use HTTPS with valid SSL certificate
- [ ] Set secure session cookies
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable request rate limiting
- [ ] Set up Web Application Firewall (WAF)
- [ ] Regular security updates
- [ ] Database connection encryption
- [ ] API key rotation policy
- [ ] Audit logging enabled

### Security Headers
```python
# Add to main.py
from flask_talisman import Talisman

Talisman(app, force_https=True)

@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
python -c "from src.models.user import db; print('Database connection successful')"
```

#### Memory Issues
```bash
# Monitor memory usage
htop
# Or
docker stats
```

#### API Key Issues
```bash
# Verify API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### Log Analysis
```bash
# View application logs
tail -f logs/ai-writing-platform.log

# Docker logs
docker-compose logs -f web

# System logs
journalctl -u ai-writing-platform -f
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx, HAProxy, AWS ALB)
- Stateless application design
- Shared session storage (Redis)
- Database connection pooling

### Vertical Scaling
- Monitor CPU and memory usage
- Optimize database queries
- Implement caching strategies
- Use CDN for static assets

### Database Scaling
- Read replicas for read-heavy workloads
- Connection pooling
- Query optimization
- Database sharding (if needed)

---

For additional support or questions about deployment, please refer to the [README](README.md) or create an issue in the GitHub repository.

