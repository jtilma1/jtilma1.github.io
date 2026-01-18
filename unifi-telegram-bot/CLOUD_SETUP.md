# ☁️ UniFi Cloud Access Setup Guide

This guide will help you configure the bot to use UniFi's cloud API (unifi.ui.com) instead of a local controller. This allows your bot to run anywhere (like your home Docker server) and still control doors at your church.

## 📋 Prerequisites

1. UniFi Access controller online and accessible via unifi.ui.com
2. UniFi account with access to your Access system
3. Admin permissions on the UniFi Access console

## Step 1: Get Your UniFi API Key

1. Go to [https://account.ui.com/](https://account.ui.com/)
2. Sign in with your UniFi account
3. Navigate to **Account Settings** → **API Access**
4. Click **Create New API Key** or **Generate API Key**
5. Give it a name like "Church Telegram Bot"
6. **Copy the API key** - it looks like a long string of random characters
7. **IMPORTANT**: Save this key securely - you won't be able to see it again!

## Step 2: Find Your Site ID

1. Go to [https://unifi.ui.com](https://unifi.ui.com)
2. Sign in and navigate to your **UniFi Access console**
3. Look at the URL in your browser address bar
4. The URL will look something like:
   ```
   https://access.ui.com/site/12345abcdef67890/overview
   ```
5. Your **Site ID** is the part after `/site/` and before the next `/`
   - In the example above: `12345abcdef67890`
6. **Copy this Site ID** - you'll need it for configuration

## Step 3: Configure for Cloud Access in Portainer

When setting up your stack in Portainer, use these environment variables:

```yaml
environment:
  - TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

  # Cloud Mode Configuration
  - UNIFI_ACCESS_HOST=https://api.ui.com
  - UNIFI_API_KEY=your_api_key_from_step_1
  - UNIFI_SITE_ID=your_site_id_from_step_2

  - ALLOWED_TELEGRAM_USERS=123456789,987654321
  - VERIFY_SSL=true
  - TZ=America/New_York
```

### Important Notes:

- **DO NOT** set `UNIFI_ACCESS_USERNAME` or `UNIFI_ACCESS_PASSWORD` when using cloud mode
- The bot will automatically detect cloud mode based on the host URL
- Use `https://api.ui.com` exactly as shown (not `unifi.ui.com`)

## Step 4: Deploy and Test

1. Deploy the stack in Portainer
2. Check the logs - you should see:
   ```
   Configured for UniFi Cloud API access
   Using UniFi Cloud API with API key - no login required
   ```
3. Open Telegram and message your bot
4. Try checking door status first to verify connectivity

## 🔧 Troubleshooting Cloud Access

### "Missing required environment variables"
- Make sure you set both `UNIFI_API_KEY` and `UNIFI_SITE_ID`
- Don't set username/password in cloud mode

### "Failed to get doors" or 401/403 errors
- **API Key Invalid**: Regenerate your API key at account.ui.com
- **Wrong Site ID**: Double-check the site ID from your console URL
- **Permissions**: Ensure your UniFi account has admin access to the site

### "Connection timeout" or network errors
- Verify your Docker server has internet access
- Check firewall rules aren't blocking outbound HTTPS
- Try accessing https://api.ui.com from your server:
  ```bash
  curl -v https://api.ui.com
  ```

### Cloud API endpoints not working
UniFi's cloud API structure might differ slightly. The bot uses:
- Doors list: `https://api.ui.com/api/s/{site_id}/v1/developer/doors`
- Unlock: `https://api.ui.com/api/s/{site_id}/v1/developer/doors/{door_id}/unlock`
- Lock: `https://api.ui.com/api/s/{site_id}/v1/developer/doors/{door_id}/lock`

If you get 404 errors, the endpoint structure may have changed. Check UniFi's API documentation or logs for the correct endpoints.

## 🔒 Security Considerations for Cloud Access

### Advantages:
- ✅ Bot can run anywhere (home server, cloud, etc.)
- ✅ No need for VPN between bot and church
- ✅ Easy remote management

### Security Best Practices:
- 🔐 Keep your API key secret - treat it like a password
- 🔐 Only grant API key access to the specific site needed
- 🔐 Use a dedicated UniFi user account for the bot
- 🔐 Regularly rotate your API key (every 90 days)
- 🔐 Monitor bot logs for unauthorized access attempts
- 🔐 Limit Telegram user access via `ALLOWED_TELEGRAM_USERS`

### Revoking Access:
If your API key is compromised:
1. Go to [account.ui.com](https://account.ui.com/)
2. Navigate to API Access
3. Delete the compromised key
4. Generate a new one
5. Update your Portainer environment variables

## 📊 Performance Comparison

| Feature | Local Controller | Cloud API |
|---------|-----------------|-----------|
| Response Time | Faster (direct) | Slightly slower |
| Reliability | Depends on local network | Depends on internet |
| Setup Complexity | Lower | Higher (API key needed) |
| Bot Location | Must be on same network | Can be anywhere |
| Firewall Config | May need port forwarding | No special config |

## ❓ FAQ

**Q: Can I switch between local and cloud mode?**
A: Yes! Just update the environment variables in Portainer and restart the stack.

**Q: Does the cloud API have rate limits?**
A: UniFi's API may have rate limits. The bot should work fine for typical church usage, but avoid rapid repeated commands.

**Q: Will this work with UniFi Protect/Network/Talk too?**
A: This bot is specifically for UniFi Access. Other UniFi products have different APIs.

**Q: My church's internet is unreliable. Should I use cloud mode?**
A: If internet at church is unreliable, consider local mode with the bot hosted at church, or use a UPS/backup internet for the Access controller.

**Q: Can I control multiple sites with one bot?**
A: Currently the bot supports one site. You'd need to run multiple bot instances for multiple sites.

## 📞 Need Help?

- Check the main README.md for general troubleshooting
- Review Portainer logs for specific error messages
- Verify your API key and Site ID are correct
- Test API access manually using curl or Postman
- Check UniFi community forums for API changes

---

**Ready to deploy?** Go back to the main README and follow the Portainer deployment instructions with your cloud configuration!
