-- CodeClinic Database Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (linked to Clerk)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clerk_user_id TEXT UNIQUE NOT NULL,
  email TEXT,
  username TEXT,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Websites/Scans table (public, not user-specific)
CREATE TABLE website_scans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  website_url TEXT NOT NULL,
  scan_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  zap_data TEXT NOT NULL,
  created_by UUID REFERENCES users(id),
  is_public BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Questions table (linked to website scans)
CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  website_scan_id UUID REFERENCES website_scans(id) ON DELETE CASCADE,
  vuln_type TEXT NOT NULL,
  title TEXT NOT NULL,
  short_explain TEXT,
  exercise_type TEXT NOT NULL CHECK (exercise_type IN ('mcq', 'fix_config', 'sandbox')),
  exercise_prompt TEXT NOT NULL,
  choices JSONB,
  answer_key JSONB NOT NULL,
  hints JSONB,
  difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
  xp INTEGER NOT NULL,
  badge TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vulnerability guides table (linked to website scans)
CREATE TABLE vulnerability_guides (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  website_scan_id UUID REFERENCES website_scans(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
  category TEXT NOT NULL,
  description TEXT NOT NULL,
  how_it_arises JSONB,
  exploitation_methods JSONB,
  real_world_examples JSONB,
  prevention_methods JSONB,
  code_examples JSONB,
  quiz_answers JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User quiz attempts (for leaderboard)
CREATE TABLE quiz_attempts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  website_scan_id UUID REFERENCES website_scans(id) ON DELETE CASCADE,
  total_questions INTEGER NOT NULL,
  correct_answers INTEGER NOT NULL,
  total_xp INTEGER NOT NULL,
  badges_earned JSONB,
  time_taken INTEGER,
  completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual question responses (for detailed analytics)
CREATE TABLE question_responses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  quiz_attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE CASCADE,
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  user_answer JSONB,
  is_correct BOOLEAN NOT NULL,
  xp_earned INTEGER NOT NULL,
  time_taken INTEGER,
  answered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_quiz_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX idx_quiz_attempts_scan_id ON quiz_attempts(website_scan_id);
CREATE INDEX idx_questions_scan_id ON questions(website_scan_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_exercise_type ON questions(exercise_type);
CREATE INDEX idx_website_scans_public ON website_scans(is_public) WHERE is_public = true;
CREATE INDEX idx_website_scans_created_by ON website_scans(created_by);
CREATE INDEX idx_vulnerability_guides_scan_id ON vulnerability_guides(website_scan_id);
CREATE INDEX idx_question_responses_attempt_id ON question_responses(quiz_attempt_id);

-- Row Level Security (RLS) Policies

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vulnerability_guides ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_responses ENABLE ROW LEVEL SECURITY;

-- Users can only see and modify their own data
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid()::text = clerk_user_id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid()::text = clerk_user_id);

CREATE POLICY "Users can insert own profile" ON users
  FOR INSERT WITH CHECK (auth.uid()::text = clerk_user_id);

-- Website scans are public for reading, but users can only modify their own
CREATE POLICY "Anyone can view public scans" ON website_scans
  FOR SELECT USING (is_public = true);

CREATE POLICY "Users can view own scans" ON website_scans
  FOR SELECT USING (auth.uid()::text = (SELECT clerk_user_id FROM users WHERE id = created_by));

CREATE POLICY "Users can create scans" ON website_scans
  FOR INSERT WITH CHECK (auth.uid()::text = (SELECT clerk_user_id FROM users WHERE id = created_by));

-- Questions are public if the scan is public
CREATE POLICY "Anyone can view questions from public scans" ON questions
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM website_scans 
      WHERE id = questions.website_scan_id 
      AND is_public = true
    )
  );

-- Vulnerability guides are public if the scan is public
CREATE POLICY "Anyone can view guides from public scans" ON vulnerability_guides
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM website_scans 
      WHERE id = vulnerability_guides.website_scan_id 
      AND is_public = true
    )
  );

-- Quiz attempts are private to users
CREATE POLICY "Users can view own quiz attempts" ON quiz_attempts
  FOR SELECT USING (auth.uid()::text = (SELECT clerk_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can create own quiz attempts" ON quiz_attempts
  FOR INSERT WITH CHECK (auth.uid()::text = (SELECT clerk_user_id FROM users WHERE id = user_id));

-- Question responses are private to users
CREATE POLICY "Users can view own question responses" ON question_responses
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM quiz_attempts qa
      JOIN users u ON qa.user_id = u.id
      WHERE qa.id = question_responses.quiz_attempt_id
      AND u.clerk_user_id = auth.uid()::text
    )
  );

CREATE POLICY "Users can create own question responses" ON question_responses
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM quiz_attempts qa
      JOIN users u ON qa.user_id = u.id
      WHERE qa.id = question_responses.quiz_attempt_id
      AND u.clerk_user_id = auth.uid()::text
    )
  );

-- Functions for leaderboard
CREATE OR REPLACE FUNCTION get_leaderboard(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
  user_id UUID,
  username TEXT,
  full_name TEXT,
  total_xp BIGINT,
  total_attempts BIGINT,
  correct_answers BIGINT,
  badges_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    u.id,
    u.username,
    u.full_name,
    COALESCE(SUM(qa.total_xp), 0) as total_xp,
    COUNT(qa.id) as total_attempts,
    COALESCE(SUM(qa.correct_answers), 0) as correct_answers,
    COALESCE(SUM(jsonb_array_length(qa.badges_earned)), 0) as badges_count
  FROM users u
  LEFT JOIN quiz_attempts qa ON u.id = qa.user_id
  GROUP BY u.id, u.username, u.full_name
  ORDER BY total_xp DESC, correct_answers DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get public scans with filters
CREATE OR REPLACE FUNCTION get_public_scans(
  difficulty_filter TEXT DEFAULT NULL,
  exercise_type_filter TEXT DEFAULT NULL,
  limit_count INTEGER DEFAULT 20,
  offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
  scan_id UUID,
  website_url TEXT,
  scan_date TIMESTAMP WITH TIME ZONE,
  created_by_username TEXT,
  created_by_full_name TEXT,
  question_count BIGINT,
  difficulties TEXT[],
  exercise_types TEXT[]
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ws.id,
    ws.website_url,
    ws.scan_date,
    COALESCE(u.username, 'Anonymous') as username,
    COALESCE(u.full_name, 'Anonymous User') as full_name,
    COUNT(q.id) as question_count,
    ARRAY_AGG(DISTINCT q.difficulty) FILTER (WHERE q.difficulty IS NOT NULL) as difficulties,
    ARRAY_AGG(DISTINCT q.exercise_type) FILTER (WHERE q.exercise_type IS NOT NULL) as exercise_types
  FROM website_scans ws
  LEFT JOIN users u ON ws.created_by = u.id
  LEFT JOIN questions q ON ws.id = q.website_scan_id
  WHERE ws.is_public = true
    AND (difficulty_filter IS NULL OR EXISTS (
      SELECT 1 FROM questions q2 
      WHERE q2.website_scan_id = ws.id 
      AND q2.difficulty = difficulty_filter
    ))
    AND (exercise_type_filter IS NULL OR EXISTS (
      SELECT 1 FROM questions q3 
      WHERE q3.website_scan_id = ws.id 
      AND q3.exercise_type = exercise_type_filter
    ))
  GROUP BY ws.id, ws.website_url, ws.scan_date, u.username, u.full_name
  ORDER BY ws.scan_date DESC
  LIMIT limit_count OFFSET offset_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
