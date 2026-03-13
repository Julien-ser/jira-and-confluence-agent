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
