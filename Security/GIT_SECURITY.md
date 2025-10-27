# 🔒 Git Security Guide for Renify Bot

## ✅ Your Sensitive Files are Protected!

I've created a comprehensive `.gitignore` file that protects:

### 🔴 NEVER Committed:
- ✅ `.env` - Environment variables with tokens
- ✅ `*.log` - Log files
- ✅ `renify_bot.log` - Bot logs
- ✅ `*_token.txt` - Any token files
- ✅ `Lavalink.jar` - Large binary file
- ✅ `*.db` - Database files
- ✅ `*.sqlite` - SQLite databases
- ✅ Python cache files (`__pycache__/`, `*.pyc`)
- ✅ IDE files (`.vscode/`, `.idea/`)
- ✅ OS files (`.DS_Store`, `Thumbs.db`)
- ✅ Backup files

---

## 📝 Before Your First Commit

### 1. Copy Environment Template:
```bash
copy env.example .env
```

### 2. Edit .env and add your token:
```bash
DISCORD_TOKEN=your_actual_token_here
LAVALINK_PASSWORD=renifythoushallnotpass
```

### 3. Verify .env is in .gitignore:
```bash
git check-ignore -v .env
```

Should output: `.gitignore:1:.env` ✅

---

## 🚀 Safe Git Commands

### Initial Setup:
```bash
git init
git add .gitignore  # Add this first!
git add *.py
git add requirements.txt
git add Dockerfile*
git add renify_lavalink/application.yml
git add *.md
git add start_*.bat
git add render.yaml
git add .dockerignore

# Verify sensitive files are NOT added
git status

# Commit
git commit -m "Initial commit: Renify Bot with security"
```

### Check What Will Be Committed:
```bash
# See what will be committed
git status

# Double-check sensitive files are ignored
git status --ignored
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ NEVER Commit:
```bash
# DON'T DO THIS!
git add .env
git add *.log
git add renify_bot.log
git add Lavalink.jar
```

### ✅ ALWAYS:
```bash
# Check before committing
git status

# If you see sensitive files, don't commit!
```

---

## 🔍 Checking for Exposed Secrets

### Before Pushing to GitHub:

Run this to check for sensitive data:
```bash
# Check for Discord tokens
git diff --cached | grep -i "discord.*token"

# Check for environment variables
git diff --cached | grep -i "DISCORD_TOKEN\|LAVALINK_PASSWORD"

# Check for SQL inserts with passwords
git diff --cached | grep -i "password"
```

If anything shows up with actual values, **DON'T COMMIT!**

---

## 🛡️ If You Already Committed Secrets

### If you accidentally committed `.env`:

**DANGER: Secrets are now in Git history!**

1. **Immediately revoke your Discord bot token**
   - Go to: https://discord.com/developers/applications
   - Generate a new token

2. **Remove the file from Git:**
   ```bash
   git rm --cached .env
   git commit -m "Remove sensitive .env file"
   git push
   ```

3. **If it's already pushed to GitHub:**
   - Secrets are now compromised!
   - Regenerate ALL exposed tokens
   - Consider the repository compromised
   - Delete and recreate if public

---

## 🔐 Best Practices

### ✅ DO:
- Use `.env` for sensitive data
- Check `git status` before committing
- Use `.env.example` as a template
- Add tokens to `.gitignore` before first commit
- Review all files with `git diff` before commit

### ❌ DON'T:
- Commit `.env` file
- Hardcode tokens in Python files
- Share `.env` files in screenshots
- Commit `.log` files with errors
- Upload to public GitHub without checking

---

## 📋 Safe Repository Checklist

Before pushing to GitHub, verify:

- [ ] `.env` is NOT tracked (check with `git status`)
- [ ] `.log` files are NOT tracked
- [ ] No hardcoded tokens in Python files
- [ ] `Lavalink.jar` is NOT tracked (too large anyway)
- [ ] Database files are NOT tracked
- [ ] All sensitive configs in `.gitignore`

Check with:
```bash
git ls-files | grep -E "\.(env|log|jar|db|sqlite)$"
```

Should return **nothing** or only `env.example` ✅

---

## 🚨 Emergency: Token Exposed

If your Discord token was committed and pushed:

1. **Immediately**: Go to Discord Developer Portal
2. **Reset Bot Token**: Generate new token
3. **Update Bot**: Use new token in `.env`
4. **Git History**: Remove from history (advanced)
5. **Notify**: Anyone with repo access

---

## 📖 Quick Reference

```bash
# See ignored files
git status --ignored

# Check if file is ignored
git check-ignore .env

# See what will be committed
git diff --cached

# Remove sensitive file from Git
git rm --cached .env
```

---

## ✅ You're Protected!

With the `.gitignore` I created, your sensitive files are safe. Just remember:

1. ✅ Never manually add `.env` to Git
2. ✅ Use environment variables
3. ✅ Check `git status` before commit
4. ✅ Keep `.env` file local only

**Your bot is secure! 🔒**

