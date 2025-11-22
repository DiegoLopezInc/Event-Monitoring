# Quick Start Guide

Get the Campus Event Monitoring System running in 5 minutes!

## Step 1: Install

```bash
# Clone repository
git clone <your-repo-url> Event-Monitoring
cd Event-Monitoring

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure

```bash
# Create configuration file
python main.py --create-config
cp config.yaml.example config.yaml

# Edit config.yaml - at minimum, add your event sources
nano config.yaml
```

Example minimal configuration:
```yaml
event_sources:
  - name: MIT CSAIL
    url: https://www.csail.mit.edu/events
```

## Step 3: Test

```bash
# Run once to test
python main.py --run-once
```

You should see output like:
```
Starting monitoring job at 2025-11-22 20:00:00
Scraping events from MIT CSAIL: https://www.csail.mit.edu/events
Found 3 relevant events from MIT CSAIL
Found 0 relevant jobs
Job completed: 3 events found, 0 jobs found, 3 notifications sent
```

## Step 4: Run Scheduled

```bash
# Run daily at 8 PM (default)
python main.py

# Or specify custom time
python main.py --schedule-time 14:00
```

Press `Ctrl+C` to stop.

## Optional: Email Notifications

1. Edit `config.yaml`:
```yaml
email:
  enabled: true
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: your-email@gmail.com
  sender_password: your-app-password  # Get from Google Account settings
  recipient_email: recipient@example.com
```

2. Test:
```bash
python main.py --test-notification
```

## Deploy to VM

### Quick VM Setup

```bash
# SSH into your VM
ssh user@your-vm.com

# Install Python
sudo apt-get update && sudo apt-get install -y python3 python3-pip git

# Clone and setup
git clone <your-repo-url> Event-Monitoring
cd Event-Monitoring
pip3 install -r requirements.txt

# Configure
cp config.yaml.example config.yaml
nano config.yaml

# Test
python3 main.py --run-once

# Run in background
nohup python3 main.py > output.log 2>&1 &
```

### Using Systemd (Recommended)

1. Create service file:
```bash
sudo nano /etc/systemd/system/event-monitoring.service
```

2. Add:
```ini
[Unit]
Description=Campus Event Monitoring
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/Event-Monitoring
ExecStart=/usr/bin/python3 main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable event-monitoring
sudo systemctl start event-monitoring
sudo systemctl status event-monitoring
```

## View Results

### Check Logs
```bash
tail -f event_monitoring.log
```

### Query Database
```bash
sqlite3 event_monitoring.db

# List all events
SELECT * FROM events;

# List all firms
SELECT * FROM firms;

# List unnotified events
SELECT * FROM events WHERE notified = 0;
```

## Troubleshooting

**Problem**: No events found
- **Solution**: Verify URLs in config.yaml are accessible. Run with `--run-once` to see output.

**Problem**: Email not sending
- **Solution**: For Gmail, enable 2FA and create an App Password. Test with `--test-notification`.

**Problem**: Permission denied on VM
- **Solution**: Ensure you have write permissions in the project directory.

## Next Steps

1. Add more event sources in `config.yaml`
2. Customize firm list in `src/firms/firms_list.py`
3. Set up email notifications
4. Monitor logs for first few days
5. Adjust keywords/thresholds as needed

## Support

For issues, see the full [README.md](README.md) or check the logs in `event_monitoring.log`.
