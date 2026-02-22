# FREE11 - The Consumption Operating System for Bharat 🪙

Transform Your Time into Real Rewards!

## 🌟 Overview

FREE11 is India's first Consumption Operating System that enables users to earn FREE11 Coins through engagement activities and redeem them for real products. Built on the principle: **Time → Skill → Coins → Goods → Utility → Repeat**.

## ✨ Features

### User Features
- **🎮 Earn Coins**: Multiple ways to earn
  - Daily Check-in with Streak System
  - Complete Daily Tasks
  - Play Mini-Games (Quiz, Spin Wheel, Scratch Card)
  
- **🛍️ Shop**: Redeem coins for real products
  - Electronics (iPhones, Headphones, etc.)
  - Vouchers (Amazon, Swiggy, etc.)
  - Fashion (Nike, Levi's)
  - Groceries

- **📊 Gamification**:
  - Level System (Bronze → Silver → Gold → Diamond)
  - Streak Tracking
  - Leaderboard
  - Achievements & Badges
  
- **👤 Profile**: Track your stats
  - Coin Balance
  - Total Earned & Redeemed
  - Activity History
  - Achievements

### Admin Features
- **📈 Analytics Dashboard**
  - Total Users
  - Total Products
  - Total Redemptions
  - Coins in Circulation
  
- **🛠️ Product Management**
  - Add new products
  - Manage inventory
  - Track all orders

## 🚀 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database
- **Motor** - Async MongoDB driver
- **JWT** - Authentication
- **Pydantic** - Data validation

### Frontend
- **React 19** - UI framework
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Component library
- **React Router** - Navigation
- **Axios** - HTTP client

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Yarn

### Backend Setup
```bash
cd /app/backend
pip install -r requirements.txt

# Set environment variables in .env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="free11_db"
JWT_SECRET_KEY="your-secret-key"

# Start backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup
```bash
cd /app/frontend
yarn install

# Set environment variables in .env
REACT_APP_BACKEND_URL=http://localhost:8001

# Start frontend
yarn start
```

### Seed Initial Data
```bash
curl -X POST http://localhost:8001/api/seed-products
```

## 🎮 How to Use

### 1. Register/Login
- Visit the landing page
- Click "Get Started" to create an account
- Get 50 welcome coins instantly!

### 2. Earn Coins
- **Daily Check-in**: Visit daily to maintain your streak
- **Complete Tasks**: Watch videos, fill surveys, share on social
- **Play Games**:
  - Quiz Challenge: Answer questions correctly
  - Spin the Wheel: Daily spin for rewards
  - Scratch Card: 3 attempts per day

### 3. Shop & Redeem
- Browse products by category
- Check coin prices
- Redeem products using your coins
- Track your orders

### 4. Level Up
- Earn XP through activities
- Progress through levels
- Unlock achievements
- Compete on leaderboard

## 🔐 Security Features

- **PRORGA Compliant**: Non-purchasable, non-withdrawable coins
- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt encryption
- **CORS Protection**: Configured for security

## 📱 API Documentation

### Authentication
```
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Coins
```
GET  /api/coins/balance
GET  /api/coins/transactions
POST /api/coins/checkin
```

### Games
```
POST /api/games/quiz
POST /api/games/spin
POST /api/games/scratch
```

### Tasks
```
GET  /api/tasks
POST /api/tasks/complete
```

### Products
```
GET  /api/products
GET  /api/products/{id}
POST /api/products
```

### Redemptions
```
POST /api/redemptions
GET  /api/redemptions
GET  /api/redemptions/all
```

### User
```
GET /api/user/stats
GET /api/leaderboard
```

### Admin
```
GET /api/admin/analytics
```

## 🎨 Design System

### Colors
- **Gold**: `#FFD700` - Primary brand color
- **Black**: `#000000` - Power and sophistication
- **Red**: `#DC2626` - Energy and action
- **Blue**: `#3B82F6` - Trust and reliability

### Typography
- Headings: Black weight (900)
- Body: Medium weight (500)
- Special: Gradient text effects

## 🌟 Key Differentiators

1. **No Purchase Required**: All coins earned through engagement
2. **Real Products**: Actual goods, not virtual items
3. **PRORGA Compliant**: Legally sound business model
4. **Gamified Experience**: Fun and engaging
5. **360° Loop**: Complete consumption cycle

## 📊 Database Schema

### Collections
- `users` - User accounts and profiles
- `coin_transactions` - All coin movements
- `products` - Product catalog
- `redemptions` - Order tracking
- `activities` - User engagement history
- `achievements` - User achievements

## 🚧 Roadmap

- [ ] Google OAuth Integration
- [ ] Mobile App (React Native)
- [ ] ONDC Integration
- [ ] Advanced Analytics
- [ ] Social Features
- [ ] Brand Partnership Portal
- [ ] Multi-language Support
- [ ] Regional Products

## 🤝 Contributing

This is an MVP/POC. Future contributions welcome!

## 📄 License

Proprietary - FREE11.com

## 🔗 Links

- Website: https://free11.com
- Presentation: See attached deck

## 👥 Contact

For more information about FREE11, please refer to the business presentation.

---

**Built with ❤️ for India's Next 150 Million Consumers**

*Transforming Attention into Consumption*
