# PETS Security Checklist

## 🚨 BEFORE PRODUCTION DEPLOYMENT

### Wallet Security

- [ ] **Private keys NEVER logged**
  - Check all logger calls
  - Verify no print statements
  - Review exception handlers

- [ ] **Private keys NEVER committed**
  - `.env` in `.gitignore`
  - No keys in code
  - No keys in comments
  - Run `git log --all --full-history --source -- .env` (should be empty)

- [ ] **Environment variables encrypted**
  - `.env` permissions 600
  - ENCRYPTION_KEY generated (Fernet)
  - Keys stored encrypted at rest

- [ ] **Recovery phrase backup**
  - Written on paper (not digital)
  - Stored in secure location (safe/vault)
  - Recovery process tested
  - Multiple copies in different locations

- [ ] **Hot/Cold wallet split**
  - Hot wallet: 10-20% capital only
  - Cold wallet: 80-90% capital (offline)
  - Rebalancing schedule defined
  - Manual cold wallet operations only

### Circuit Breakers

- [ ] **All circuit breakers tested**
  - 3 consecutive losses → STOP
  - 5% daily loss → STOP
  - 25% bot drawdown → STOP
  - 40% portfolio drawdown → EMERGENCY STOP
  - Z4-Z5 trades → BLOCK

- [ ] **Emergency stop working**
  - Tested in staging
  - Closes all positions
  - Stops all bots
  - Alerts admin
  - Requires manual reset

- [ ] **Circuit breaker state persisted**
  - Redis backup configured
  - State survives restarts
  - No race conditions

### Monitoring & Alerts

- [ ] **Prometheus metrics exported**
  - Portfolio value
  - P&L (realized/unrealized)
  - Circuit breaker status
  - Bot health
  - Trade results

- [ ] **Grafana dashboards configured**
  - Portfolio overview
  - Bot performance
  - Circuit breaker status
  - Alert history

- [ ] **Slack alerts configured**
  - Webhook tested
  - Circuit breaker triggers
  - Emergency stop
  - Large losses
  - Bot errors

- [ ] **Email alerts configured**
  - SMTP settings correct
  - Test email sent
  - Critical alerts only

- [ ] **SMS alerts configured (optional)**
  - Twilio configured
  - Emergency stop only
  - Phone number verified

### Infrastructure

- [ ] **Firewall configured**
  - Default deny incoming
  - SSH allowed (key-only)
  - HTTP/HTTPS allowed
  - All other ports closed
  - `sudo ufw status` verified

- [ ] **SSL/TLS enabled**
  - Let's Encrypt certificate
  - Auto-renewal configured
  - HTTPS enforced
  - Certificate expiry monitored

- [ ] **SSH hardened**
  - Root login disabled
  - Password auth disabled
  - Key-only authentication
  - Fail2ban installed

- [ ] **Docker security**
  - Non-root user
  - Resource limits set
  - Network isolation
  - Secrets management

### Database

- [ ] **Database password strong**
  - 32+ characters
  - Random generated
  - Not in code
  - Stored in .env only

- [ ] **Database backups configured**
  - Daily backups
  - Offsite storage (S3/DO Spaces)
  - Backup encryption
  - Recovery tested

- [ ] **Redis password set**
  - Strong password
  - requirepass enabled
  - Persistence enabled
  - AOF or RDB configured

- [ ] **SQL injection prevention**
  - Parameterized queries only
  - No string concatenation
  - ORM used correctly
  - Input validation

### API Security

- [ ] **Rate limiting enabled**
  - 100 requests/minute
  - Per IP tracking
  - DDoS protection
  - Slowloris protection

- [ ] **CORS configured**
  - Specific origins only
  - No wildcard (*)
  - Credentials allowed
  - Preflight cached

- [ ] **Input validation**
  - Pydantic models
  - Type checking
  - Range validation
  - Sanitization

- [ ] **Error handling**
  - No sensitive data in errors
  - Generic messages to clients
  - Detailed logs internally
  - Stack traces hidden

### Code Quality

- [ ] **Type hints complete**
  - mypy --strict passes
  - No `Any` types
  - Return types specified
  - Function signatures complete

- [ ] **Tests coverage ≥80%**
  - Unit tests
  - Integration tests
  - Circuit breaker tests
  - Emergency stop tests

- [ ] **Linting clean**
  - black formatted
  - ruff passed
  - No warnings
  - Docstrings complete

- [ ] **Dependencies updated**
  - No known vulnerabilities
  - pip-audit passed
  - Safety check passed
  - Dependabot enabled

### Trading Logic

- [ ] **Bot 8 strategy validated**
  - Paper trading 100+ trades
  - Win rate ≥60%
  - Profit factor ≥1.5
  - Sharpe ratio ≥1.0
  - Max drawdown ≤15%

- [ ] **Position sizing correct**
  - Kelly calculator tested
  - Max 15% per position
  - Zone-based sizing
  - Available balance checked

- [ ] **Post-only orders enforced**
  - No taker orders
  - Maker rebate applied
  - Slippage = 0
  - Order rejection handled

- [ ] **Gas optimization**
  - EIP-1559 used
  - Gas estimation accurate
  - Max gas cap set
  - Cost tracking

### Deployment

- [ ] **Staging environment tested**
  - All features working
  - Performance acceptable
  - No errors in logs
  - Monitoring working

- [ ] **Production checklist complete**
  - All items above ✓
  - Backups verified
  - Alerts tested
  - Emergency contacts ready

- [ ] **Rollback plan ready**
  - Previous version tagged
  - Rollback script tested
  - Database migrations reversible
  - Downtime minimized

- [ ] **Documentation complete**
  - Deployment guide
  - Architecture diagrams
  - API documentation
  - Troubleshooting guide

## 🚨 PRODUCTION START PROTOCOL

1. **Paper Trading Validation (7 days minimum)**
   - Start paper bot
   - Monitor for 100+ trades
   - Verify win rate ≥60%
   - Check circuit breakers not triggered
   - Review all alerts

2. **Small Capital Test (3 days)**
   - Transfer $1,000 to hot wallet
   - Start production bot
   - Monitor CLOSELY
   - Verify all metrics
   - Check gas costs

3. **Scale Up Gradually**
   - Week 1: $5K
   - Week 2: $10K
   - Week 3: $20K
   - Month 2+: Full capital

4. **Continuous Monitoring**
   - Check dashboards daily
   - Review P&L daily
   - Verify circuit breakers
   - Rebalance hot/cold weekly

## 🔴 RED FLAGS - STOP IMMEDIATELY

- Private key logged
- Circuit breaker not working
- Emergency stop fails
- Win rate <50%
- Drawdown >40%
- Gas costs >$50/day
- Monitoring down
- Alerts not received
- Database backup failed
- Unauthorized access attempt

## ✅ SIGN-OFF

Before production:

- [ ] Developer reviewed checklist
- [ ] Security audit complete
- [ ] Paper trading successful
- [ ] All stakeholders approved
- [ ] Emergency contacts ready
- [ ] Monitoring confirmed

**Production Start Date**: _______________

**Approved By**: _______________

**Date**: _______________

---

🚨 **REMEMBER**: Real money, real risk. Safety FIRST, profits second.
