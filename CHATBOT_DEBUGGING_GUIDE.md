# 🤖 Chatbot Voice Command Debugging Guide

## What Was Fixed

The unified chatbot widget now has **comprehensive console logging** to help diagnose voice command issues. The widget also **auto-opens the chat panel** when "Hey Bot" is detected, making the response more visible.

## How to Test

### Step 1: Open Developer Console
1. Go to any page with the chatbot (e.g., http://localhost:8000/video_Recommendation)
2. Press **F12** or **Ctrl+Shift+I** to open Developer Tools
3. Click the **Console** tab

### Step 2: Test Voice Command
1. Say: **"Hey Bot go to login page"**
2. Watch the console for debug logs (see expected output below)

## Console Debug Output - What You Should See

When everything is working correctly, you'll see this sequence in the console:

```
🎤 Raw transcript: hey bot go to login page
🌐 Detected language: en
📝 Processed text: hey bot go to login page
🔍 Checking for "hey bot"... true
✅ "Hey Bot" detected!
📂 Chat panel opened automatically
🎯 Extracted command: go to login page
📤 Sending command: go to login page
📨 Sending message: go to login page
📡 Calling API: /api/chatbot/query/
📥 API Response status: 200
✅ API Response data: {response_type: 'navigation', path: '/patient_login/', ...}
🗺️ Single navigation command: /patient_login/
🚀 Navigating to: /patient_login/
```

## Troubleshooting

### Issue 1: Speech not being recognized
**Console will show:**
```
🎤 Raw transcript: (empty)
```
**Solutions:**
- Check your microphone is working
- Check browser permissions (allow microphone access)
- Try speaking more clearly
- Ensure you say "Hey Bot" first

### Issue 2: "Hey Bot" not detected
**Console will show:**
```
🎤 Raw transcript: hello bot
ℹ️ Text does not contain "Hey Bot", ignoring
```
**Solutions:**
- Say "Hey Bot" (exact phrase, case-insensitive)
- Try: "hey bot", "HEY BOT", "Hey bot", etc.
- Clear enunciation helps

### Issue 3: Command extracted but not sent
**Console will show:**
```
✅ "Hey Bot" detected!
⚠️ No command found after "Hey Bot"
```
**Solutions:**
- Say something after "Hey Bot"
- Example: "Hey Bot go to login" (not just "Hey Bot")

### Issue 4: API call failing
**Console will show:**
```
❌ API returned error status: 404
```
**Solutions:**
- Check if backend is running: `docker compose ps`
- Verify CSRF token is being sent
- Check Django logs: `docker compose logs django-app`

### Issue 5: Navigation not happening
**Console will show:**
```
🚀 Navigating to: /patient_login/
(but page doesn't change)
```
**Solutions:**
- Wait 1-2 seconds for navigation
- Check browser console for any other errors
- Try refreshing the page first

## Commands to Test

### Navigation Commands
- "Hey Bot go to login page"
- "Hey Bot navigate to patient dashboard"
- "Hey Bot take me to recommendations"
- "Hey Bot open diagnosis page"

### Multi-Commands
- "Hey Bot scroll down and go to login"
- "Hey Bot click submit then navigate home"

### Urdu Commands
- "ہے بوٹ لاگ ان صفحہ پر جائیں" (Hey Bot go to login page in Urdu)

## What's New in This Version

1. **Auto-opens chat panel** - When "Hey Bot" is detected, the panel auto-opens
2. **Detailed console logs** - Every step is logged with emoji for easy reading
3. **Error messages** - Users see helpful messages if something fails
4. **Better error handling** - API errors are now clearly reported
5. **Command timing** - Logs show exact timing of each action

## Advanced Debugging

If you want even more detail, edit `chatbot_widget_unified.html` and add these to any function:

```javascript
console.log('🔍 Variable name:', variableName);
console.table(arrayOfItems);
console.time('operation-name');
// ... your code ...
console.timeEnd('operation-name');
```

## Backend Logs

To see what the backend is receiving:

```bash
docker compose logs django-app -f
```

Look for lines like:
```
[INFO] Processing query: go to login page
[INFO] Multi-command detected: 1 commands
```

## Still Not Working?

1. **Open Console** (F12 → Console tab)
2. **Say your command** ("Hey Bot go to login")
3. **Copy all console output** (Ctrl+A, Ctrl+C)
4. **Share the console output** with the debugging team

The console output will show exactly where the problem is occurring.

---

## Quick Reference: Where Things Happen

| Step | Component | File | What Happens |
|------|-----------|------|--------------|
| 1 | Microphone | Browser API | Speech captured |
| 2 | Recognition | `chatbot_widget_unified.html` line 566 | Transcript extracted |
| 3 | Language Detection | `detectLanguage()` | English or Urdu? |
| 4 | Translation (if needed) | `translateUrduToEnglish()` | Convert to English |
| 5 | Wake Word Check | `includes('hey bot')` | Wait for wake word |
| 6 | Command Extraction | `.replace(/hey bot/i, '')` | Remove wake word |
| 7 | API Call | `/api/chatbot/query/` | Send to backend |
| 8 | Backend Processing | `chatbot_service.py` | Gemini AI processes |
| 9 | Response Parsing | `parse_gemini_response()` | Extract action type |
| 10 | Execution | JavaScript | Navigation/click/scroll |

