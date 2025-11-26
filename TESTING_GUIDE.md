# Testing the Background Voice Listener

## Quick Start Testing

### Prerequisites
1. Open your FYP application in a web browser (Chrome recommended)
2. Grant microphone permission when prompted
3. Open browser Developer Console (F12 → Console tab)

## Test Cases

### Test 1: Wake Word Detection
**Steps:**
1. Navigate to any page in the application
2. Say clearly: "Hey Bot"
3. Watch for:
   - Green dot changes to red
   - Chat panel opens automatically
   - Bot message: "I'm listening! What would you like to do?"
4. Console should show: "✨ Wake word detected! Opening chatbot and listening..."

**Result:** ✅ PASS / ❌ FAIL

---

### Test 2: Navigation Command
**Steps:**
1. Activate with "Hey Bot"
2. Say: "Go to admin login" or "Navigate to doctor dashboard"
3. Watch for:
   - Bot message: "✅ Navigating to: [Page Name]"
   - Page redirects after ~800ms

**Result:** ✅ PASS / ❌ FAIL

---

### Test 3: Form Filling Without Navigation
**Steps:**
1. Go to login page manually
2. Activate with "Hey Bot"
3. Say: "Enter username as bilal"
4. Watch for:
   - Bot message: "📝 Filling form fields..."
   - Username field fills with "bilal"
   - Page DOES NOT redirect

**Result:** ✅ PASS / ❌ FAIL

---

### Test 4: Form Filling + Button Click
**Steps:**
1. Say: "Enter username as bilal and password as bilal1234"
2. Watch for:
   - Both fields fill
   - Page stays on login
3. Say: "Click login button"
4. Watch for:
   - Bot message: "🔘 Clicking button..."
   - Login button is clicked
   - Form submits (backend handles result)

**Result:** ✅ PASS / ❌ FAIL

---

### Test 5: Conversational Response
**Steps:**
1. Activate with "Hey Bot"
2. Say: "What is shoulder fracture?"
3. Watch for:
   - Bot responds with conversational answer
   - No navigation occurs
   - Message appears in chat

**Result:** ✅ PASS / ❌ FAIL

---

### Test 6: Background Listening Resume
**Steps:**
1. Close chat panel (click X button)
2. Watch for:
   - Indicator changes from red to green
   - Background listening resumes
3. Say: "Hey Bot" after a few seconds
4. Watch for:
   - Chat opens again
   - Bot is ready for next command

**Result:** ✅ PASS / ❌ FAIL

---

### Test 7: Multiple Wake Words
**Steps:**
1. Say: "Hello Bot" (instead of "Hey Bot")
2. Verify it activates
3. Close panel, try "Ok Bot"
4. Verify it activates
5. Close panel, try "Bot" (just the word)
6. Verify it activates

**Result:** ✅ PASS / ❌ FAIL

---

### Test 8: Text Input Fallback
**Steps:**
1. Type a command in the text input box
2. Press Enter
3. Verify it's processed correctly

**Result:** ✅ PASS / ❌ FAIL

---

## Troubleshooting

### Microphone Not Working
- [ ] Check browser permission for microphone (🔒 in address bar)
- [ ] Ensure microphone is not in use by another app
- [ ] Reload page and try again
- [ ] Check console for error messages

### Wake Word Not Detected
- [ ] Speak clearly and naturally
- [ ] Try different wake words: "Hey Bot", "Hello Bot", "Ok Bot"
- [ ] Wait for green indicator to show before speaking
- [ ] Check console: `🎤 Background voice listening enabled...`

### Form Not Filling
- [ ] Verify form field names match what bot understands
- [ ] Try speaking: "Enter [field_label] as [value]"
- [ ] Check console for field detection logs

### Page Redirects When Shouldn't
- [ ] This indicates Gemini is returning TYPE=navigation instead of TYPE=form_fill
- [ ] Try being specific: "Fill the username field" vs "Login"

### Chat Panel Doesn't Open on Wake Word
- [ ] Check browser console for errors
- [ ] Verify microphone permission is granted
- [ ] Try refreshing the page
- [ ] Check if background listening is active (green indicator visible)

---

## Console Debugging

**Expected console messages in order:**

```
Page Load:
🎤 Background voice listening enabled. Say "Hey Bot" to activate.

After saying "Hey Bot":
✨ Wake word detected! Opening chatbot and listening...
I'm listening! What would you like to do?

After voice command:
📝 Filling form fields... (or)
🔘 Clicking button... (or)
✅ Navigating to: [Page] (or)
[Conversational response]
```

---

## Performance Notes

- ⚡ Background listening uses minimal resources
- 🎙️ Once activated, main listening is responsive
- 📱 May use more battery on mobile (normal for voice apps)
- 🌐 Requires internet for Gemini API calls

---

## Test Results Summary

| Test | Result | Notes |
|------|--------|-------|
| Wake Word Detection | ✅/❌ | |
| Navigation | ✅/❌ | |
| Form Fill | ✅/❌ | |
| Form + Button | ✅/❌ | |
| Conversation | ✅/❌ | |
| Resume Listening | ✅/❌ | |
| Multiple Wake Words | ✅/❌ | |
| Text Input Fallback | ✅/❌ | |

Fill in results after testing!
