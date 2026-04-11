-- Seed Courses
INSERT INTO public.courses (slug, title, description, metadata) VALUES 
('gestao-financeira', 'Gestão Financeira para Empreendimentos', 'Aprenda a controlar caixa...', '{"chapters": []}'::jsonb),
('boas-praticas', 'Boas Práticas na Produção e Manipulação de Alimentos', 'Guia essencial...', '{"chapters": []}'::jsonb),
('organizacao-producao', 'Organização da Produção para o Mercado', 'Estruture seus processos...', '{"chapters": []}'::jsonb)
ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title;

-- Seed Sample Auth User
INSERT INTO auth.users (id, instance_id, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, aud, role)
VALUES (
    'd4a3e7b1-1234-4bc5-a678-90abcdef1234', 
    '00000000-0000-0000-0000-000000000000', 
    'rafael@teste.com', 
    'seed_password_hash', 
    now(), 
    '{"provider":"email","providers":["email"]}', 
    '{"full_name":"Rafael Teste"}', 
    'authenticated', 
    'authenticated'
)
ON CONFLICT (id) DO NOTHING;

-- Update Profile WhatsApp (Trigger handle_new_user should have created the row already)
UPDATE public.profiles 
SET whatsapp = '5563999999999' 
WHERE id = 'd4a3e7b1-1234-4bc5-a678-90abcdef1234';

-- Seed Sample Enrollment
INSERT INTO public.enrollments (student_id, course_id, status, progress_percent)
SELECT p.id, c.id, 'active', 25
FROM public.profiles p, public.courses c
WHERE p.id = 'd4a3e7b1-1234-4bc5-a678-90abcdef1234' AND c.slug = 'gestao-financeira'
ON CONFLICT (student_id, course_id) DO UPDATE SET progress_percent = 25;
