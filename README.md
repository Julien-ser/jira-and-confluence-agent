# Jira and Confluence Agent

An autonomous agent that creates and modifies Jira and Confluence spaces, similar to what a Jira/Confluence administrator would do manually.

## Features

- **Jira Operations**: Create and manage projects, issue types, custom fields, workflows, screens, and permissions
- **Confluence Operations**: Create and manage spaces, pages, templates, and permissions
- **Configuration-driven**: Define operations in YAML configuration files
- **Dry-run mode**: Preview changes before applying them
- **Idempotent operations**: Safe to run multiple times
- **Structured logging**: Complete audit trail in `logs/` directory
- **Detailed reporting**: JSON and text summaries of all operations

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design and technical specifications.

## Project Structure

```
jira-and-confluence-agent/
├── src/
│   ├── __init__.py
│   ├── models.py          # Data models and types
│   ├── parser.py          # Configuration parser
│   ├── jira_client.py     # Jira REST API client
│   ├── confluence_client.py  # Confluence REST API client (planned)
│   ├── engine.py          # Operation orchestrator (planned)
│   ├── reporter.py        # Report generation
│   └── utils.py           # Utility functions
├── config/                # Configuration files (create your own)
├── tests/                 # Unit and integration tests
├── logs/                  # Execution logs and reports
├── requirements.txt       # Python dependencies
├── ARCHITECTURE.md        # Architecture documentation
├── TASKS.md               # Development progress
└── README.md              # This file
```

## Setup

### Prerequisites

- Python 3.10+
- Jira/Confluence instance with admin credentials
- API tokens for authentication

### Installation

```bash
# Install dependencies using system Python (no virtualenv needed)
pip install -r requirements.txt
```

## Configuration

Create a configuration file (YAML format) defining the operations you want to perform:

```yaml
# example_config.yaml
connections:
  jira:
    url: "https://your-jira-instance.atlassian.net"
    username: "admin@example.com"
    password: "YOUR_API_TOKEN"
  confluence:
    url: "https://your-confluence-instance.atlassian.net"
    username: "admin@example.com"
    password: "YOUR_API_TOKEN"

jira:
  projects:
    - key: "TEST"
      name: "Test Project"
      description: "A test project"
      projectTypeKey: "business"

confluence:
  spaces:
    - key: "TEST"
      name: "Test Space"
      description: "A test space"
```

## Usage

### Command Line

```bash
# Run with dry-run to preview changes
python run_agent.py config/example_config.yaml --dry-run

# Execute actual operations
python run_agent.py config/example_config.yaml

# Enable verbose logging
python run_agent.py config/example_config.yaml --verbose

# Custom log directory
python run_agent.py config/example_config.yaml --log-dir mylogs
```

### Programmatic Usage

```python
from src.parser import OperationParser
from src.engine import Engine
from src.reporter import Reporter

# Parse configuration
parser = OperationParser()
operations = parser.parse_file("config/example.yaml")

# Execute operations
engine = Engine(config["connections"], dry_run=False)
with engine:
    report = engine.run(operations)

# Report is automatically generated in logs/ directory
```

## Deployment

The Jira and Confluence Agent can be deployed in multiple ways:

### Option 1: Docker (Recommended)

The easiest way to deploy is using Docker:

```bash
# Build the Docker image
docker build -t jira-confluence-agent .

# Run with a specific config file
docker run -v $(pwd)/config:/app/config:ro \
           -v $(pwd)/logs:/app/logs \
           -e AGENT_CONFIG=/app/config/example_config.yaml \
           jira-confluence-agent

# Or use docker-compose for easier setup
docker-compose up
```

**Using environment variables with Docker Compose:**

1. Copy `.env.example` to `.env` and fill in your credentials
2. Update `config/agent_config.yaml` or use the example config
3. Run: `docker-compose up`

The container is designed for manual execution only (restart: "no"). For scheduled/automated runs, consider:

- Using cron to execute `docker-compose run jira-agent`
- Setting up a CI/CD pipeline (see below)

### Option 2: Direct Python Execution

For simple deployments, run directly on the host:

```bash
# Install dependencies system-wide
pip install -r requirements.txt

# Run the agent
python run_agent.py config/example_config.yaml --dry-run

# With environment variables (recommended for credentials)
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="admin@example.com"
export JIRA_PASSWORD="your_api_token"
# ... set other variables as needed
python run_agent.py config/example_config.yaml
```

### Option 3: Package Installation

Create a pip-installable package (requires `setup.py` - to be added):

```bash
pip install -e .
jira-agent config/example_config.yaml
```

### Production Considerations

#### Security
- **Never store credentials in config files** for production. Use environment variables or a secrets manager
- The agent supports reading credentials from environment variables:
  - `JIRA_URL`, `JIRA_USERNAME`, `JIRA_PASSWORD`
  - `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_PASSWORD`
- Rotate API tokens regularly
- Use SSL verification (default: true)

#### Scheduling Automated Runs
Use cron (with Docker) or systemd timers:

```bash
# Example cron job (runs daily at 2 AM)
0 2 * * * cd /path/to/agent && docker-compose run --rm jira-agent /app/config/daily_ops.yaml >> /var/log/jira-agent.log 2>&1
```

#### Monitoring
- Check `logs/` directory for `agent.log`, `audit.log`, and reports
- Set up log rotation for `logs/` directory
- Monitor exit codes: `0` = success, `1` = failure

#### High Availability
- The agent is idempotent and can be safely re-run
- Design configurations to be modular and reusable
- Use dry-run mode (`--dry-run`) to validate before production runs

### CI/CD Integration

Example GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy Jira Agent
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  run-agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run agent
        env:
          JIRA_URL: ${{ secrets.JIRA_URL }}
          JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
          JIRA_PASSWORD: ${{ secrets.JIRA_PASSWORD }}
          CONFLUENCE_URL: ${{ secrets.CONFLUENCE_URL }}
          CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }}
          CONFLUENCE_PASSWORD: ${{ secrets.CONFLUENCE_PASSWORD }}
        run: |
          python run_agent.py config/production.yaml --dry-run
          python run_agent.py config/production.yaml
```

## Current Status

**Project Status: Production Ready** ✅

All core features implemented and tested:

- ✅ Configuration parser (YAML/JSON)
- ✅ Jira REST API client (projects, issue types, custom fields, workflows)
- ✅ Confluence REST API client (spaces, pages, templates)
- ✅ Operation engine with dry-run support
- ✅ Comprehensive reporting and audit logging
- ✅ 40 passing unit and integration tests
- ✅ Command-line interface (run_agent.py)
- ✅ Example configuration file

See [TASKS.md](TASKS.md) for detailed development progress.

## Development

Run tests (when available):
```bash
pytest tests/
```

Check linting (when configured):
```bash
ruff check src/
```

## Logging

All operations are logged to the `logs/` directory:
- `agent.log` - Structured application logs
- `audit.log` - JSON audit trail of each operation
- `report_<timestamp>.json` - Machine-readable execution report
- `summary_<timestamp>.txt` - Human-readable summary

## Security

- Never commit credentials or API tokens to version control
- Use environment variables or secure credential stores
- The `.gitignore` excludes sensitive files

## Contributing

This is an autonomous project managed by OpenCode. See TASKS.md for current development status.

## License

[Add your license here]
