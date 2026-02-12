# PETS Production Deployment Guide

## Prerequisites

- Ubuntu 22.04 LTS VPS (4+ vCPUs, 8+ GB RAM, 100+ GB SSD)
- Docker & Docker Compose installed
- Domain name with SSL certificate
- Firewall configured
- Backup strategy

## 1. Server Setup

### Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Clone Repository

```bash
git clone https://github.com/juankaspain/PETS.git
cd PETS
```

## 2. Configuration

### Environment Variables

```bash
cp .env.example .env
nano .env
```

**CRITICAL - Fill in all values:**
- `HOT_WALLET_PRIVATE_KEY`: Your hot wallet private key (NEVER share!)
- `ENCRYPTION_KEY`: Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `DB_PASSWORD`: Strong database password
- `REDIS_PASSWORD`: Strong Redis password
- `SLACK_WEBHOOK_URL`: Slack webhook for alerts
- `EMAIL_PASSWORD`: Email password for alerts

### Generate Wallet (if needed)

```python
from eth_account import Account
import secrets

# Generate new wallet
private_key = "0x" + secrets.token_hex(32)
account = Account.from_key(private_key)

print(f"Address: {account.address}")
print(f"Private Key: {private_key}")
print("\n🚨 SAVE THIS PRIVATE KEY SECURELY!")
print("🚨 NEVER SHARE OR COMMIT TO GIT!")
```

## 3. Security Hardening

### Firewall Configuration

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSH Hardening

```bash
sudo nano /etc/ssh/sshd_config

# Set:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

sudo systemctl restart sshd
```

### File Permissions

```bash
chmod 600 .env
chmod 700 logs/
```

## 4. Database Initialization

```bash
# Start database
docker-compose -f docker-compose.prod.yml up -d timescaledb redis

# Wait 10 seconds
sleep 10

# Run migrations
python scripts/init_database.py
```

## 5. Deploy Services

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 6. Monitoring Setup

### Grafana Access

1. Open http://your-domain:3000
2. Login: `admin` / `${GRAFANA_PASSWORD}`
3. Import dashboard from `monitoring/grafana/dashboards/pets-dashboard.json`

### Prometheus

1. Open http://your-domain:9090
2. Verify targets are up

### Alerts

1. Test Slack webhook: `curl -X POST -H 'Content-type: application/json' --data '{"text":"PETS Alert Test"}' ${SLACK_WEBHOOK_URL}`
2. Verify alert received

## 7. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 8. Backup Strategy

### Database Backup

```bash
# Daily backup
0 2 * * * docker exec pets_timescaledb pg_dump -U pets pets > /backup/pets_$(date +\%Y\%m\%d).sql

# Compress and upload to S3
0 3 * * * gzip /backup/pets_$(date +\%Y\%m\%d).sql && aws s3 cp /backup/pets_$(date +\%Y\%m\%d).sql.gz s3://your-backup-bucket/
```

### Wallet Backup

1. **CRITICAL**: Write down recovery phrase on paper
2. Store in secure location (safe, bank vault)
3. NEVER store digitally
4. Test recovery process

## 9. Start Production Bot

### Paper Trading First (Validation)

```bash
# Start paper trading for 7 days
curl -X POST http://localhost:8000/api/paper/start

# Monitor for 100+ trades, 60%+ win rate
# Check dashboard: http://your-domain:8501
```

### Production Trading

**ONLY after paper trading validation:**

```bash
# Transfer USDC to hot wallet
# Start production bot
curl -X POST http://localhost:8000/api/production/start

# 🚨 MONITOR CLOSELY FOR FIRST 24 HOURS
```

## 10. Maintenance

### View Logs

```bash
docker-compose -f docker-compose.prod.yml logs -f api
```

### Restart Services

```bash
docker-compose -f docker-compose.prod.yml restart api
```

### Update Code

```bash
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### Emergency Stop

```bash
curl -X POST http://localhost:8000/api/production/emergency-stop
```

## 11. Monitoring Checklist

**Daily:**
- [ ] Check Grafana dashboards
- [ ] Review P&L
- [ ] Verify no circuit breakers triggered
- [ ] Check bot health

**Weekly:**
- [ ] Review win rate (target ≥60%)
- [ ] Check profit factor (target ≥1.5)
- [ ] Verify backups working
- [ ] Update dependencies

**Monthly:**
- [ ] Security audit
- [ ] Performance optimization
- [ ] Rebalance hot/cold wallets

## 12. Troubleshooting

### Bot Stopped

```bash
# Check circuit breaker status
curl http://localhost:8000/api/circuit-breaker/status/1

# Reset if needed (admin approval required)
curl -X POST http://localhost:8000/api/circuit-breaker/reset/1
```

### High Gas Costs

- Check Polygon network status
- Adjust gas price buffer
- Consider batching transactions

### Database Performance

```bash
# Check hypertable stats
docker exec pets_timescaledb psql -U pets -c "SELECT * FROM timescaledb_information.hypertables;"

# Rebuild continuous aggregates
docker exec pets_timescaledb psql -U pets -c "CALL refresh_continuous_aggregate('portfolio_1h', NULL, NULL);"
```

## Support

For issues:
1. Check logs
2. Review monitoring dashboards
3. Contact: juankaspain@github.com

## 🚨 CRITICAL REMINDERS

- **NEVER log or commit private keys**
- **Monitor circuit breakers**
- **Test emergency stop regularly**
- **Keep backups current**
- **Start with paper trading**
- **Use small capital initially**
