# CodeClinic Setup Guide

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd src/backend

# Install dependencies
pip install fastapi uvicorn python-dotenv requests pydantic

# Optional: Install AI and database dependencies
pip install google-generativeai supabase

# Create .env file with your API keys
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
echo "SUPABASE_URL=your_supabase_url_here" >> .env
echo "SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key_here" >> .env

# Start the backend
python3 run.py
```

### 2. Frontend Setup

```bash
cd src/frontend

# Install dependencies
npm install

# Create .env.local file
echo "NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here" > .env.local
echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here" >> .env.local
echo "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here" >> .env.local
echo "CLERK_SECRET_KEY=your_clerk_secret_key_here" >> .env.local

# Start the frontend
npm run dev
```

### 3. Database Setup (Optional)

1. Create a Supabase project at https://supabase.com
2. Run the SQL schema from `database/schema.sql` in your Supabase SQL editor
3. Get your project URL and keys from Settings > API
4. Add them to your environment files

## 🔧 Troubleshooting

### Backend Won't Start

**Error: `ModuleNotFoundError: No module named 'fastapi'`**
```bash
pip install fastapi uvicorn python-dotenv requests pydantic
```

**Error: `Supabase client not available`**
- This is expected if you haven't set up Supabase yet
- The backend will work without database features
- Install with: `pip install supabase`

**Error: `Gemini API not available`**
- Add your Gemini API key to the `.env` file
- Install with: `pip install google-generativeai`

### Frontend Won't Start

**Error: `Module not found`**
```bash
npm install
```

**Error: `Supabase client not available`**
- Add your Supabase credentials to `.env.local`
- Install with: `npm install @supabase/supabase-js @supabase/ssr`

## 🎯 Features

### Without Database (Basic Mode)
- ✅ Generate cybersecurity questions from ZAP data
- ✅ Interactive quiz interface
- ✅ Vulnerability study guides
- ✅ Question navigation and hints

### With Database (Full Mode)
- ✅ User authentication with Clerk
- ✅ Save quiz attempts and progress
- ✅ Leaderboard and rankings
- ✅ Public scan exploration
- ✅ XP and badge system

## 📝 Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
```

## 🎮 Usage

1. **Start Backend**: `python3 run.py` (runs on http://localhost:8000)
2. **Start Frontend**: `npm run dev` (runs on http://localhost:3000)
3. **Generate Questions**: Paste ZAP scan data and generate questions
4. **Take Quiz**: Study the guide, then answer questions
5. **View Progress**: Check leaderboard and explore other scans

## 🆘 Need Help?

- Check the health endpoint: http://localhost:8000/health
- View API docs: http://localhost:8000/docs
- Check browser console for frontend errors
- Check backend logs for server errors
