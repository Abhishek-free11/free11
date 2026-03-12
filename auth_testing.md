# Emergent Google Auth Testing Playbook

## Step 1: Create Test User & Session
```
mongosh --eval "
use('free11_db');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  id: userId,
  email: 'test.google.' + Date.now() + '@example.com',
  name: 'Test Google User',
  auth_provider: 'google',
  coins_balance: 50,
  is_admin: false,
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend Auth
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl -X GET "$API_URL/api/auth/me" -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Step 3: Browser Testing
```javascript
await page.context.add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "your-app.com",
    "path": "/",
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
}]);
await page.goto("https://your-app.com");
```

## Checklist
- [ ] Google login button visible on Login page
- [ ] Clicking Google button redirects to Emergent Auth
- [ ] After auth, session_id in URL fragment is processed
- [ ] JWT token stored in localStorage
- [ ] User redirected to /dashboard
- [ ] /api/auth/me returns user data with token

## Success Indicators
✅ /api/auth/me returns user data
✅ Dashboard loads without redirect
✅ Existing OTP login still works
