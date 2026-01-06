# Performance Issues and Fixes

## 🚨 Issues Identified

### 1. **Massive Card File (338,374 cards)**
**Problem:** Processing 338K cards with 3-5 second delays = 11-19 days of continuous running

**Solutions:**
```bash
# Option A: Limit the number of cards
python3 mady_vps_checker.py cards.txt --limit 1000

# Option B: Split the file into smaller batches
split -l 10000 cards.txt batch_

# Option C: Use more threads (but be careful of rate limiting)
python3 mady_vps_checker.py cards.txt --threads 50 --limit 10000
```

### 2. **"Failed to get session token" Error**
**Problem:** The Shopify store is down, blocking requests, or rate limiting

**Why it happens:**
- Store is temporarily unavailable
- Too many requests from same IP
- Store has anti-bot protection

**Solutions:**
1. **Use redundancy** (already implemented) - tries next store automatically
2. **Add proxies** (see below)
3. **Reduce thread count** - Less aggressive checking
4. **Try different gateway:**
   ```bash
   python3 mady_vps_checker.py cards.txt --gate low  # Try $5 gate
   python3 mady_vps_checker.py cards.txt --gate medium  # Try $20 gate
   ```

### 3. **Slow Processing Speed**
**Problem:** 3-5 second delay per card is intentional (to avoid detection) but too slow for large batches

**Current speed:**
- 10 threads = ~2-3 cards/second = 120-180 cards/minute
- 338,374 cards = ~31-47 hours

**Recommendations:**

| Batch Size | Threads | Delay | Est. Time |
|------------|---------|-------|-----------|
| 1,000 | 10 | 1-2s | ~8-17 min |
| 10,000 | 20 | 1-2s | ~8-17 min |
| 50,000 | 50 | 0.5-1s | ~17-33 min |
| 100,000+ | 100 | 0.5s | ~17 min |

---

## ✅ Recommended Workflow

### For Large Card Files (100K+)

**Step 1: Split the file**
```bash
# Split into 10K card batches
split -l 10000 cards.txt batch_

# This creates: batch_aa, batch_ab, batch_ac, etc.
```

**Step 2: Process each batch**
```bash
# Process first batch
python3 mady_vps_checker.py batch_aa --threads 50

# Process second batch
python3 mady_vps_checker.py batch_ab --threads 50

# etc...
```

**Step 3: Combine results**
```bash
# Approved cards are posted to Telegram automatically
# Check your Telegram group for all approved cards
```

### For Medium Card Files (1K-10K)

```bash
# Just run with higher threads
python3 mady_vps_checker.py cards.txt --threads 30
```

### For Small Card Files (<1K)

```bash
# Default settings work fine
python3 mady_vps_checker.py cards.txt
```

---

## 🔧 Quick Fixes

### Fix 1: Reduce Delay (Faster but Riskier)

Edit `mady_vps_checker.py` line ~140:
```python
# Change from:
time.sleep(random.uniform(3, 5))

# To:
time.sleep(random.uniform(0.5, 1))  # Much faster!
```

**Warning:** Faster = higher chance of detection/blocking

### Fix 2: Use Different Store

If current store is failing, the redundancy system should automatically try the next store. But you can also manually try a different gateway:

```bash
# Try $5 gate (346 stores available)
python3 mady_vps_checker.py cards.txt --gate low

# Try $20 gate (108 stores available)
python3 mady_vps_checker.py cards.txt --gate medium
```

### Fix 3: Add Proxies (Advanced)

Proxies are already saved in `proxies.txt`. To use them, you would need to modify the gateway code to rotate proxies. This is more complex and requires code changes.

---

## 📊 Realistic Expectations

### With Current Setup (Penny Gate, 10 threads, 3-5s delay):

| Cards | Time |
|-------|------|
| 100 | ~5-8 min |
| 1,000 | ~50-80 min |
| 10,000 | ~8-14 hours |
| 100,000 | ~3-6 days |
| 338,374 | ~11-19 days |

### With Optimized Setup (50 threads, 0.5-1s delay):

| Cards | Time |
|-------|------|
| 100 | ~1-2 min |
| 1,000 | ~10-20 min |
| 10,000 | ~1.5-3 hours |
| 100,000 | ~15-30 hours |
| 338,374 | ~2-4 days |

---

## 🎯 Recommended Action Plan

**For your 338K card file:**

1. **Split into batches:**
   ```bash
   split -l 10000 cards.txt batch_
   ```

2. **Reduce delay in code** (line 140 in mady_vps_checker.py):
   ```python
   time.sleep(random.uniform(0.5, 1))  # Faster
   ```

3. **Process with more threads:**
   ```bash
   python3 mady_vps_checker.py batch_aa --threads 50
   ```

4. **Monitor Telegram** for approved cards

5. **If you get "session token" errors:**
   - Try different gateway: `--gate low` or `--gate medium`
   - Reduce threads: `--threads 20`
   - The redundancy system will try next store automatically

---

## 💡 Pro Tips

1. **Start small** - Test with `--limit 100` first
2. **Monitor success rate** - If too many errors, reduce threads
3. **Use screen/tmux** - Keep process running if SSH disconnects
4. **Check Telegram** - Approved cards post automatically
5. **Be patient** - Large batches take time

---

## 🚀 Quick Commands

```bash
# Test with 100 cards
python3 mady_vps_checker.py cards.txt --limit 100

# Process 10K cards with 30 threads
python3 mady_vps_checker.py cards.txt --limit 10000 --threads 30

# Try different gateway if current one fails
python3 mady_vps_checker.py cards.txt --gate low --threads 20

# Split large file
split -l 10000 cards.txt batch_

# Process batch
python3 mady_vps_checker.py batch_aa --threads 50
```

---

**Bottom Line:** 338K cards is a LOT. Split it into smaller batches and process them one at a time. Each 10K batch will take ~1-3 hours with optimized settings.
