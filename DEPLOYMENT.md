# Deployment Guide

This guide provides detailed instructions for deploying the Jira and Confluence Agent in various environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Native Python Deployment](#native-python-deployment)
- [Configuration](#configuration)
- [Security Best Practices](#security-best-practices)
- [Automation](#automation)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Quick Start

For a quick test run (non-production):

```bash
# 1. Clone the repository
git clone <repository-url>
cd jira-and-confluence-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create config file
cp config/example_config.yaml config/my_config.yaml
# Edit my_config.yaml with your credentials

# 4. Dry run (preview changes)
python run_agent.py config/my_config.yaml --dry-run

# 5. Execute (if dry run looks good)
python run_agent.py config/my_config.yaml
```

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Steps

1. **Prepare configuration**
   ```bash
   cp config/example_config.yaml config/agent_config.yaml
   # Edit the file with your Jira/Confluence details
   ```

2. **Set up environment variables** (recommended for credentials)
   ```bash
   cp .env.example .env
   # Edit .env with your API tokens and URLs
   ```

3. **Build and run**
   ```bash
   # Build image
   docker build -t jira-confluence-agent .

   # Run manually
   docker run -v $(pwd)/config:/app/config:ro \
              -v $(pwd)/logs:/app/logs \
              -e AGENT_CONFIG=/app/config/agent_config.yaml \
              jira-confluence-agent

   # Or use docker-compose (automatically uses .env)
   docker-compose up
   ```

### Docker Image Details

- **Base image**: `python:3.11-slim` (lightweight, secure)
- **Entrypoint**: `python run_agent.py`
- **Volumes**: Config and logs are mounted for persistence
- **Security**: Runs as root (consider adding USER directive for production if needed)

## Native Python Deployment

For direct deployment on a server without Docker:

### Installation

```bash
# 1. Transfer the codebase to your server
scp -r . user@server:/opt/jira-agent
cd /opt/jira-agent

# 2. Install system-wide (or use a virtualenv if preferred)
pip install --upgrade pip
pip install -r requirements.txt

# 3. Set up environment variables (recommended)
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="admin@example.com"
export JIRA_PASSWORD="your_api_token"
# ... other variables

# 4. Run the agent
python run_agent.py config/example_config.yaml
```

### Systemd Service (for scheduled runs)

Create `/etc/systemd/system/jira-agent.service`:

```ini
[Unit]
Description=Jira and Confluence Agent
After=network.target

[Service]
Type=oneshot
EnvironmentFile=/opt/jira-agent/.env
WorkingDirectory=/opt/jira-agent
ExecStart=/usr/bin/python /opt/jira-agent/run_agent.py /opt/jira-agent/config/agent_config.yaml
StandardOutput=append:/var/log/jira-agent/output.log
StandardError=append:/var/log/jira-agent/error.log

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jira-agent.service
sudo systemctl start jira-agent.service
```

### Cron Job

```bash
# Edit crontab
crontab -e

# Add line to run daily at 2 AM
0 2 * * * cd /opt/jira-agent && /usr/bin/python run_agent.py config/agent_config.yaml >> /var/log/jira-agent/cron.log 2>&1
```

## Configuration

### Config File Structure

The agent uses YAML configuration files. See `config/example_config.yaml` for full example.

Key sections:
- `connections`: Jira/Confluence instance details
- `jira`: Jira operations (projects, issue types, custom fields, workflows)
- `confluence`: Confluence operations (spaces, pages, templates)

### Environment Variables

The following environment variables can override config file credentials:

| Variable | Purpose |
|----------|---------|
| `JIRA_URL` | Jira instance URL |
| `JIRA_USERNAME` | Jira admin username/email |
| `JIRA_PASSWORD` | Jira API token |
| `CONFLUENCE_URL` | Confluence instance URL |
| `CONFLUENCE_USERNAME` | Confluence admin username/email |
| `CONFLUENCE_PASSWORD` | Confluence API token |

**Note**: Environment variables take precedence over config file values.

## Security Best Practices

1. **Use API tokens, not passwords** - Generate tokens from Atlassian account settings
2. **Never commit credentials** - Use `.env` file (git-ignored) or environment variables
3. **Principle of least privilege** - Use admin accounts only when necessary; create dedicated service accounts
4. **SSL verification** - Keep `verify_ssl: true` (default) unless you have a specific reason to disable
5. **Rotate tokens** - Periodically regenerate API tokens
6. **Audit logs** - Review `logs/audit.log` regularly to track changes
7. **Network security** - Deploy agent in same network/VPC as Jira/Confluence if self-hosted

## Automation

### CI/CD Pipelines

See README.md for GitHub Actions example. Adapt for GitLab CI, Jenkins, etc.

### Scheduling

- **Cron**: Simple, built into Linux/macOS
- **Systemd timers**: More feature-rich cron alternative on systemd systems
- **Kubernetes CronJob**: For container-orchestrated environments
- **AWS EventBridge / GCP Cloud Scheduler**: Cloud-native scheduling

### Example: Daily Configuration Drift Detection

```yaml
# config/drift_check.yaml
connections:
  jira:
    url: ${JIRA_URL}
    username: ${JIRA_USERNAME}
    password: ${JIRA_PASSWORD}
  confluence:
    url: ${CONFLUENCE_URL}
    username: ${CONFLUENCE_USERNAME}
    password: ${CONFLUENCE_PASSWORD}

jira:
  # Just read project definitions, no changes
  projects:
    - key: "PROJ"
      read_only: true

confluence:
  spaces:
    - key: "DOC"
      read_only: true
```

Run with: `python run_agent.py config/drift_check.yaml --dry-run`

## Monitoring

### Logs

All logs are written to `logs/` directory:
- `agent.log` - Structured JSON logs (structlog)
- `audit.log` - JSON audit trail of every operation
- `report_<timestamp>.json` - Machine-readable execution report
- `summary_<timestamp>.txt` - Human-readable summary

### Log Rotation

Set up logrotate (Linux):

```bash
# /etc/logrotate.d/jira-agent
/opt/jira-agent/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### Health Checks

The agent exits with:
- `0` = All operations successful
- `1` = One or more operations failed

Use this in monitoring scripts:
```bash
python run_agent.py config/production.yaml
if [ $? -eq 0 ]; then
  echo "Agent execution successful"
else
  echo "Agent execution FAILED - check logs"
  # Send alert to Slack/email/PagerDuty
fi
```

## Troubleshooting

### Common Issues

**Error: "No operations found in configuration"**
- Check your config file syntax (YAML)
- Ensure `jira:` or `confluence:` sections exist and have items

**Authentication failures**
- Verify API tokens are correct (not passwords)
- Check that the account has admin permissions
- Ensure `verify_ssl` is set appropriately for your environment

**Connection timeouts**
- Increase `timeout` value in config (default: 30 seconds)
- Check network connectivity to Jira/Confluence instances
- Consider running agent closer to instances (same VPC/region)

**Permission errors**
- Service account needs admin rights for Jira/Confluence
- Check that API tokens haven't expired

**Container permission issues**
- If mounting host volumes, ensure correct permissions
- Consider running container with specific UID/GID: `user: "1000:1000"`

### Getting Help

- Check logs: `logs/agent.log` and `logs/audit.log`
- Run with `--verbose` flag for detailed output
- Review configuration in dry-run mode: `--dry-run`
- Open an issue on GitHub with logs and config (sanitized)

## Production Checklist

Before deploying to production:

- [ ] All credentials stored securely (environment variables or secrets manager)
- [ ] Dry-run tested and reviewed operations
- [ ] Logs directory exists and is writable
- [ ] Backup/rollback plan defined
- [ ] Monitoring/alerting configured for failures
- [ ] Scheduling aligns with business needs (avoid peak hours)
- [ ] Notification system in place for failures
- [ ] Agent user has appropriate permissions (principle of least privilege)
- [ ] Network/firewall rules allow outbound to Jira/Confluence
- [ ] Documentation updated for your specific deployment

## Upgrading

1. Pull latest code
2. Check `requirements.txt` for dependency changes
3. Test in staging environment
4. Update production
5. Run with `--dry-run` to validate
6. Monitor logs after deployment
