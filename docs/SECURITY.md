# PETS Security Guidelines

## Overview

Security is **CRITICAL** for production trading with real money. This document outlines security requirements and best practices.

## 🔐 Security Checklist

Before deploying to production, verify ALL items:

### Private Keys
- [ ] Private keys NEVER logged anywhere
- [ ] Private keys NEVER printed or displayed
- [ ] Private keys NEVER stored in database unencrypted
- [ ] Private keys NEVER sent over network unencrypted
- [ ] Private keys NEVER committed to git
- [ ] Private keys encrypted at rest (Fernet)
- [ ] Private keys only in memory during signing
- [ ] PrivateKey value object used (secure repr)

### Mnemonic Phrase
- [ ] Mnemonic phrase stored OFFLINE (written on paper)
- [ ] Mnemonic phrase in secure location (safe, vault)
- [ ] Mnemonic phrase NEVER logged
- [ ] Mnemonic phrase NEVER committed to git
- [ ] Backup mnemonic phrase created
- [ ] Recovery process tested

### Environment Variables
- [ ] .env file created from .env.example
- [ ] .env file added to .gitignore
- [ ] All sensitive values in .env (not hardcoded)
- [ ] .env file has restrictive permissions (600)
- [ ] Encryption key generated (Fernet)
- [ ] Strong RPC URL configured

### Wallet Management
- [ ] Hot/cold split configured (10-20% hot)
- [ ] Cold wallet address verified
- [ ] Hot wallet address verified
- [ ] Initial balance split correctly
- [ ] Rebalance logic tested
- [ ] Manual cold wallet operations only

### Circuit Breakers
- [ ] All circuit breakers configured
- [ ] Circuit breakers tested (unit tests)
- [ ] Emergency stop tested
- [ ] Max consecutive losses enforced
- [ ] Max daily loss enforced
- [ ] Max bot drawdown enforced
- [ ] Max portfolio drawdown enforced
- [ ] Z4-Z5 directional trades blocked

### Monitoring
- [ ] Prometheus metrics configured
- [ ] Grafana dashboards created
- [ ] Slack alerts configured
- [ ] Email alerts configured
- [ ] Alert thresholds set
- [ ] Alert delivery tested

### Infrastructure
- [ ] Firewall configured (only required ports)
- [ ] SSH key-based auth only (no password)
- [ ] Fail2ban installed
- [ ] Auto-updates enabled
- [ ] Backups configured
- [ ] SSL/TLS enabled
- [ ] Rate limiting enabled

### Testing
- [ ] Paper trading completed (100+ trades)
- [ ] Win rate ≥60% validated
- [ ] Profit factor ≥1.5 validated
- [ ] Max drawdown ≤15% validated
- [ ] Backtesting passed
- [ ] All tests passing (pytest)
- [ ] No TODO or FIXME in critical paths

## 🚨 Critical Security Rules

### NEVER

1. **NEVER** log private keys or mnemonic phrases
2. **NEVER** commit secrets to git
3. **NEVER** store private keys unencrypted
4. **NEVER** disable circuit breakers in production
5. **NEVER** use hot wallet for large amounts (>20%)
6. **NEVER** bypass manual approval for cold wallet operations
7. **NEVER** deploy without testing on paper trading first

### ALWAYS

1. **ALWAYS** encrypt private keys at rest
2. **ALWAYS** use environment variables for secrets
3. **ALWAYS** validate mnemonic phrase before use
4. **ALWAYS** test recovery process
5. **ALWAYS** monitor circuit breaker status
6. **ALWAYS** have emergency stop ready
7. **ALWAYS** backup wallet and configuration

## 🔑 Key Management

### Mnemonic Phrase Storage

**Best Practice**: Write mnemonic phrase on paper and store in secure location.

**DO**:
- Write clearly on acid-free paper
- Store in fireproof safe or bank vault
- Create backup copy in separate location
- Test recovery periodically
- Use BIP39 standard (24 words)

**DON'T**:
- Store digitally (text file, photo, email, cloud)
- Share with anyone
- Store near computer
- Keep only one copy

### Private Key Encryption

**Fernet Encryption** (symmetric):
```python
from cryptography.fernet import Fernet

# Generate key (do once, store in .env)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt private key
encrypted = cipher.encrypt(private_key.encode())

# Decrypt for use
decrypted = cipher.decrypt(encrypted).decode()
```

**Key Rotation**:
- Rotate encryption key every 90 days
- Re-encrypt all stored private keys
- Test decryption before deleting old key

## 🏦 Hot/Cold Wallet Split

### Rationale

**Hot Wallet** (10-20%):
- Connected to internet
- Active trading
- Higher risk
- Automatic operations

**Cold Wallet** (80-90%):
- Offline storage
- Security
- Lower risk
- Manual operations only

### Configuration

```python
# .env
HOT_WALLET_PERCENTAGE=0.15  # 15% hot, 85% cold
```

### Rebalancing

**Automatic Rebalance Trigger**:
- Hot wallet < 80% of target → Transfer from cold
- Hot wallet > 120% of target → Transfer to cold

**Manual Approval Required**:
- All cold wallet operations
- Transfers > $1,000
- Withdrawals

## 🛡️ Circuit Breakers

### Configuration

```python
# .env
MAX_CONSECUTIVE_LOSSES=3       # Stop after 3 losses
MAX_DAILY_LOSS_PCT=0.05        # Stop at 5% daily loss
MAX_BOT_DRAWDOWN_PCT=0.25      # Stop at 25% bot drawdown
MAX_PORTFOLIO_DRAWDOWN_PCT=0.40 # Emergency stop at 40%
```

### Actions

**On Circuit Breaker Trigger**:
1. Stop all bots immediately
2. Close open positions (optional, configurable)
3. Send alerts (Slack + Email)
4. Log event
5. Require manual reset

**Emergency Stop**:
- 40% portfolio drawdown
- System critical error
- Security breach detected
- Manual trigger by admin

## 📊 Monitoring

### Metrics

**Portfolio**:
- Total value
- Hot/cold balances
- Realized/unrealized P&L
- Win rate
- Profit factor

**Circuit Breakers**:
- Consecutive losses count
- Daily loss percentage
- Bot drawdown percentage
- Portfolio drawdown percentage
- Status (active/triggered)

**System**:
- API latency
- Database query time
- Memory usage
- CPU usage
- Error rate

### Alerts

**Critical** (Slack + Email + SMS):
- Circuit breaker triggered
- Emergency stop
- System error
- Security event

**Warning** (Slack + Email):
- Large position opened
- Approaching circuit breaker
- Unusual activity
- Low balance

**Info** (Slack):
- Bot started/stopped
- Rebalance executed
- Daily summary

## 🔄 Recovery Process

### Wallet Recovery

1. Retrieve mnemonic phrase from secure storage
2. Validate mnemonic with `mnemonic.check()`
3. Derive private key using BIP44 path
4. Verify address matches expected
5. Load wallet with current balance
6. Test with small transaction

### System Recovery

1. Stop all running bots
2. Backup current database
3. Restore from last known good state
4. Verify wallet balances on-chain
5. Reconcile positions
6. Test paper trading mode
7. Gradual production restart

## 📝 Audit Log

All security-relevant events logged:

- Wallet creation/loading
- Private key encryption/decryption
- Hot/cold transfers
- Circuit breaker triggers
- Emergency stops
- Manual overrides
- Configuration changes

**Log Format**: JSON with timestamp, event, user, details

**Log Retention**: 90 days minimum

**Log Access**: Restricted to admins only

## 🚀 Deployment Checklist

Before deploying to production:

1. Complete security checklist above
2. Run all tests (pytest -v)
3. Complete paper trading validation
4. Review and approve all code changes
5. Backup current state
6. Deploy to staging first
7. Test on staging with small amounts
8. Monitor for 24 hours
9. Deploy to production
10. Monitor closely for first week

## 📞 Emergency Contacts

**System Down**:
- Check monitoring dashboards
- Review recent logs
- Restart services
- Escalate if unresolved

**Security Breach**:
1. Execute emergency stop
2. Disconnect from network
3. Transfer funds to new wallet
4. Investigate breach
5. Report incident
6. Review and fix vulnerability

**Large Loss**:
1. Verify circuit breakers triggered
2. Review recent trades
3. Check for bugs
4. Analyze market conditions
5. Document incident
6. Adjust strategy if needed

---

## Summary

**Security is NOT optional**. Follow ALL guidelines before production deployment.

**When in doubt**: 
- Test on paper trading first
- Use smaller amounts
- Enable all circuit breakers
- Monitor closely

**Remember**: Losing money due to bugs is worse than missing profits.
