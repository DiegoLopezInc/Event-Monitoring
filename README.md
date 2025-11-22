# Campus Event Monitoring System

A comprehensive Python-based intelligence system for tracking quantitative finance firms. Automatically monitors campus events, job postings, engineering blogs, investor reports, and video content. Extracts insights from multiple sources, stores historical data, and sends intelligent notifications about new opportunities and technical content.

## Features

### Core Monitoring
- **Event Monitoring**: Scrapes campus event websites for quantitative finance-related events
- **Job Portal Monitoring**: Tracks job postings from firm career pages
- **Blog Post Scraping**: Monitors engineering blogs for technical content and problem-solving approaches
- **Investor Report Analysis**: Downloads and processes investor reports, fund offerings, and financial disclosures
- **Video Transcription**: Extracts and transcribes video content from firm YouTube channels

### Intelligence & Analysis
- **Firm Detection**: Automatically identifies content from 50+ major quant firms (Citadel, Two Sigma, Jane Street, etc.)
- **Smart Filtering**: Uses keyword matching to identify relevant quantitative finance and technical content
- **Historical Tracking**: Maintains comprehensive database of all firm activities and content over time
- **Content Search**: Full-text search across all content types
- **Metrics Extraction**: Automatically extracts key financial metrics from reports

### Storage & Organization
- **Hybrid Storage**: Database for metadata + file system for full content (blog posts, reports, transcripts)
- **Persistent Memory**: SQLite database with full historical data
- **Organized File Structure**: Automatically organizes downloaded content by type and firm
- **Markdown Conversion**: Converts blog posts to markdown for easy reading

### Automation & Notifications
- **Scheduled Execution**: Runs as a lightweight cron job (default: 8 PM daily)
- **Multi-Channel Notifications**: Email and console alerts for new content
- **Batch Processing**: Efficiently processes multiple sources in a single run
- **Comprehensive Testing**: Full test suite included

## Example Use Case

Monitors sites like [MIT CSAIL Events](https://www.csail.mit.edu/event/buy-side-equity-quant-analysis-tools-and-open-problems-featuring-bam) to catch events from firms like:
- Citadel, Two Sigma, Jane Street
- Jump Trading, Hudson River Trading, Optiver
- DE Shaw, AQR, Point72
- And 50+ more quantitative finance firms

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Event-Monitoring.git
cd Event-Monitoring
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create configuration file:
```bash
python main.py --create-config
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
```

4. (Optional) Configure email notifications:
- Edit `config.yaml` and set `email.enabled: true`
- Add your SMTP credentials
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)

## Usage

### Run Once

Test the system by running it once:
```bash
python main.py --run-once
```

### Scheduled Execution (Recommended for VM)

Run daily at 8:00 PM:
```bash
python main.py
```

Custom schedule time:
```bash
python main.py --schedule-time 14:00  # Run at 2:00 PM
```

### Test Notifications

Send a test notification to verify configuration:
```bash
python main.py --test-notification
```

### Using with Cron (Alternative)

Add to your crontab for daily execution at 8 PM:
```bash
crontab -e
# Add this line:
0 20 * * * cd /path/to/Event-Monitoring && /usr/bin/python3 main.py --run-once
```

## Configuration

Edit `config.yaml` to customize:

### Event Sources

Add your university's event pages:
```yaml
event_sources:
  - name: MIT CSAIL
    url: https://www.csail.mit.edu/events
  - name: Stanford CS
    url: https://cs.stanford.edu/events
```

### Email Notifications

```yaml
email:
  enabled: true
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: your-email@gmail.com
  sender_password: your-app-password
  recipient_email: recipient@example.com
```

### Job Monitoring

```yaml
job_monitoring:
  scrape_known_firms: true  # Monitor predefined firms
  scrape_event_firms: true  # Monitor firms from detected events
```

## Architecture

```
Event-Monitoring/
├── src/
│   ├── database/          # SQLAlchemy models and database manager
│   ├── scrapers/          # Event and job scrapers
│   ├── firms/             # Firm detection and lists
│   ├── notifications/     # Email/console notifications
│   ├── scheduler/         # APScheduler job runner
│   └── config.py          # Configuration management
├── tests/                 # Comprehensive test suite
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── config.yaml           # Configuration file
```

## Database Schema

- **Firms**: Stores quantitative finance firms and their metadata
- **Events**: Campus events with firm associations and timing
- **JobPostings**: Job openings from tracked firms
- **ScrapeLog**: Audit log of scraping activities

## Testing

Run the test suite:
```bash
pytest
```

With coverage:
```bash
pytest --cov=src --cov-report=html
```

## Deployment to VM

### Lightweight Deployment

This system is designed to run efficiently on cheap VMs:

1. **Resource Requirements**:
   - RAM: 256 MB minimum
   - Disk: ~50 MB for code + database
   - CPU: Minimal (runs only once daily)

2. **Setup on VM**:
```bash
# Install Python
sudo apt-get update
sudo apt-get install python3 python3-pip

# Clone and setup
git clone <repo-url> Event-Monitoring
cd Event-Monitoring
pip3 install -r requirements.txt

# Configure
python3 main.py --create-config
nano config.yaml

# Test
python3 main.py --run-once

# Run as background service
nohup python3 main.py > output.log 2>&1 &
```

3. **Using systemd** (recommended):

Create `/etc/systemd/system/event-monitoring.service`:
```ini
[Unit]
Description=Campus Event Monitoring
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Event-Monitoring
ExecStart=/usr/bin/python3 main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable event-monitoring
sudo systemctl start event-monitoring
```

## How It Works

1. **Daily Execution**: Scheduler runs at configured time (default 8 PM)
2. **Event Scraping**: Scrapes configured campus event websites
3. **Firm Detection**: Identifies events from quantitative finance firms
4. **Database Update**: Stores new events and updates firm history
5. **Job Scraping**: Checks job portals of tracked firms
6. **Filtering**: Identifies relevant quantitative finance positions
7. **Notifications**: Sends alerts for new events/jobs via email or console
8. **Logging**: Records all activity for monitoring

## Supported Firms

The system tracks 50+ quantitative finance firms including:

**Hedge Funds**: Citadel, Two Sigma, Renaissance Technologies, DE Shaw, AQR

**Prop Trading**: Jane Street, Jump Trading, Optiver, IMC Trading, DRW, SIG

**HFT**: Hudson River Trading, Tower Research, Virtu Financial, Old Mission

**Investment Banks**: Goldman Sachs, Morgan Stanley, JP Morgan (quant divisions)

See `src/firms/firms_list.py` for the complete list.

## Customization

### Add More Firms

Edit `src/firms/firms_list.py`:
```python
QUANT_FIRMS.append("Your Firm Name")
FIRM_CAREERS_URLS["Your Firm Name"] = "https://..."
```

### Add Event Sources

Add to `config.yaml`:
```yaml
event_sources:
  - name: Your University
    url: https://your-university.edu/events
```

### Customize Keywords

Edit `src/firms/firms_list.py` to add detection keywords:
```python
QUANT_KEYWORDS.extend(["your", "keywords"])
```

## Troubleshooting

### No events found
- Verify event source URLs are accessible
- Check logs in `event_monitoring.log`
- Run with `--run-once` to see immediate output

### Email not working
- Verify SMTP settings in `config.yaml`
- For Gmail, ensure 2FA is enabled and use App Password
- Test with `--test-notification`

### Database errors
- Ensure write permissions in project directory
- Check `event_monitoring.db` file exists
- For issues, delete database to recreate: `rm event_monitoring.db`

## Contributing

Contributions welcome! Areas for improvement:
- Additional campus event sources
- More sophisticated scraping for specific sites
- Integration with job board APIs
- Slack/Discord notification support
- Web dashboard for viewing tracked data

## License

MIT License - feel free to use and modify for your needs.

## Acknowledgments

Built with open-source Python libraries:
- SQLAlchemy (database)
- BeautifulSoup4 (web scraping)
- APScheduler (job scheduling)
- Requests (HTTP)
- PyYAML (configuration)
- Pytest (testing)