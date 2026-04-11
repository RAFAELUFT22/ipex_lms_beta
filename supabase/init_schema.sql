-- 1. Create Tables

-- PROFILES
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users NOT NULL PRIMARY KEY,
  whatsapp TEXT UNIQUE,
  name TEXT,
  full_name TEXT,
  cpf TEXT,
  localidade TEXT,
  city TEXT,
  role TEXT DEFAULT 'student',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- COURSES
CREATE TABLE IF NOT EXISTS public.courses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ENROLLMENTS
CREATE TABLE IF NOT EXISTS public.enrollments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  student_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  course_id UUID REFERENCES public.courses(id) ON DELETE CASCADE NOT NULL,
  status TEXT DEFAULT 'active', -- active, completed, dropped
  progress_percent INTEGER DEFAULT 0,
  certificate_hash TEXT,
  last_activity TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  UNIQUE(student_id, course_id)
);

-- LEARNING LOGS (Audit & DLQ)
CREATE TABLE IF NOT EXISTS public.learning_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  student_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  type TEXT NOT NULL, -- whatsapp_msg, quiz_done, etc.
  payload JSONB DEFAULT '{}'::jsonb,
  status TEXT NOT NULL, -- pending, success, error
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_logs ENABLE ROW LEVEL SECURITY;

-- 3. Define Policies

-- Profiles: Users can see and update their own profile
CREATE POLICY "Users can see own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Allow anon to read profiles" ON public.profiles
  FOR SELECT TO anon USING (true);

-- Courses: All authenticated users can read courses
CREATE POLICY "Authenticated users can read courses" ON public.courses
  FOR SELECT TO authenticated USING (true);

-- Enrollments: Users can see their own enrollments
CREATE POLICY "Users can see own enrollments" ON public.enrollments
  FOR SELECT USING (auth.uid() = student_id);

-- Learning Logs: Users can see their own logs
CREATE POLICY "Users can see own logs" ON public.learning_logs
  FOR SELECT USING (auth.uid() = student_id);

-- 4. Set up Realtime
-- Enable Realtime for enrollments to push updates to the dashboard
ALTER PUBLICATION supabase_realtime ADD TABLE public.enrollments;
ALTER PUBLICATION supabase_realtime ADD TABLE public.learning_logs;

-- 5. Trigger for new user profile
-- Automatically create a profile entry when a new user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, name)
  VALUES (new.id, new.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
