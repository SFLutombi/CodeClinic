import { createClient } from '@supabase/supabase-js'
import { createClientComponentClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// Client-side Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Component client for SSR
export const createClient = () => createClientComponentClient()

// Database types
export interface User {
  id: string
  clerk_user_id: string
  email?: string
  username?: string
  full_name?: string
  avatar_url?: string
  created_at: string
  updated_at: string
}

export interface WebsiteScan {
  id: string
  website_url: string
  scan_date: string
  zap_data: string
  created_by: string
  is_public: boolean
  created_at: string
}

export interface Question {
  id: string
  website_scan_id: string
  vuln_type: string
  title: string
  short_explain?: string
  exercise_type: 'mcq' | 'fix_config' | 'sandbox'
  exercise_prompt: string
  choices?: Array<{ id: string; text: string }>
  answer_key: string[]
  hints?: string[]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  xp: number
  badge?: string
  created_at: string
}

export interface VulnerabilityGuide {
  id: string
  website_scan_id: string
  name: string
  severity: 'Low' | 'Medium' | 'High' | 'Critical'
  category: string
  description: string
  how_it_arises: string[]
  exploitation_methods: string[]
  real_world_examples: string[]
  prevention_methods: string[]
  code_examples: {
    vulnerable: string
    secure: string
  }
  quiz_answers: {
    keyConcepts: string[]
    preventionMethods: string[]
    securityHeaders: string[]
    attackVectors: string[]
  }
  created_at: string
}

export interface QuizAttempt {
  id: string
  user_id: string
  website_scan_id: string
  total_questions: number
  correct_answers: number
  total_xp: number
  badges_earned: string[]
  time_taken?: number
  completed_at: string
}

export interface QuestionResponse {
  id: string
  quiz_attempt_id: string
  question_id: string
  user_answer: any
  is_correct: boolean
  xp_earned: number
  time_taken?: number
  answered_at: string
}

// Helper function to get or create user from Clerk
export async function getOrCreateUser(clerkUser: any): Promise<User | null> {
  try {
    // First, try to find existing user
    const { data: existingUser, error: fetchError } = await supabase
      .from('users')
      .select('*')
      .eq('clerk_user_id', clerkUser.id)
      .single()

    if (existingUser && !fetchError) {
      return existingUser
    }

    // Create new user if not found
    const { data: newUser, error: createError } = await supabase
      .from('users')
      .insert({
        clerk_user_id: clerkUser.id,
        email: clerkUser.emailAddresses?.[0]?.emailAddress,
        username: clerkUser.username,
        full_name: clerkUser.fullName,
        avatar_url: clerkUser.imageUrl
      })
      .select()
      .single()

    if (createError) {
      console.error('Error creating user:', createError)
      return null
    }

    return newUser
  } catch (error) {
    console.error('Error in getOrCreateUser:', error)
    return null
  }
}
