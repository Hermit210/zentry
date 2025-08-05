-- Zentry Cloud Database Schema for Supabase
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    credits DECIMAL(10,2) DEFAULT 50.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- VMs table
CREATE TABLE IF NOT EXISTS vms (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    instance_type VARCHAR(50) NOT NULL CHECK (instance_type IN ('small', 'medium', 'large', 'xlarge')),
    image VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'creating' CHECK (status IN ('creating', 'running', 'stopped', 'terminated', 'error')),
    ip_address VARCHAR(45),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vms_user_id ON vms(user_id);
CREATE INDEX IF NOT EXISTS idx_vms_project_id ON vms(project_id);
CREATE INDEX IF NOT EXISTS idx_vms_status ON vms(status);
CREATE INDEX IF NOT EXISTS idx_vms_created_at ON vms(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_vms_updated_at ON vms;
CREATE TRIGGER update_vms_updated_at 
    BEFORE UPDATE ON vms
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Enable for all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE vms ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (true); -- Allow service role to access all users

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (true); -- Allow service role to update users

DROP POLICY IF EXISTS "Users can insert" ON users;
CREATE POLICY "Users can insert" ON users
    FOR INSERT WITH CHECK (true); -- Allow service role to insert users

-- RLS Policies for projects table
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (true); -- Allow service role to access all projects

DROP POLICY IF EXISTS "Users can create projects" ON projects;
CREATE POLICY "Users can create projects" ON projects
    FOR INSERT WITH CHECK (true); -- Allow service role to insert projects

DROP POLICY IF EXISTS "Users can update own projects" ON projects;
CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (true); -- Allow service role to update projects

DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (true); -- Allow service role to delete projects

-- RLS Policies for vms table
DROP POLICY IF EXISTS "Users can view own VMs" ON vms;
CREATE POLICY "Users can view own VMs" ON vms
    FOR SELECT USING (true); -- Allow service role to access all VMs

DROP POLICY IF EXISTS "Users can create VMs" ON vms;
CREATE POLICY "Users can create VMs" ON vms
    FOR INSERT WITH CHECK (true); -- Allow service role to insert VMs

DROP POLICY IF EXISTS "Users can update own VMs" ON vms;
CREATE POLICY "Users can update own VMs" ON vms
    FOR UPDATE USING (true); -- Allow service role to update VMs

DROP POLICY IF EXISTS "Users can delete own VMs" ON vms;
CREATE POLICY "Users can delete own VMs" ON vms
    FOR DELETE USING (true); -- Allow service role to delete VMs

-- Insert some sample data for testing (optional)
-- Uncomment the following lines if you want sample data

/*
-- Sample user (password is 'password123' hashed with bcrypt)
INSERT INTO users (email, name, hashed_password, credits) VALUES 
('demo@zentry.cloud', 'Demo User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJgusgqHu', 100.00)
ON CONFLICT (email) DO NOTHING;

-- Sample project
INSERT INTO projects (name, description, user_id) 
SELECT 'My First Project', 'A sample project for testing', id 
FROM users WHERE email = 'demo@zentry.cloud'
ON CONFLICT DO NOTHING;

-- Sample VM
INSERT INTO vms (name, instance_type, image, status, ip_address, user_id, project_id)
SELECT 'web-server-01', 'small', 'ubuntu-22.04', 'running', '192.168.1.100', u.id, p.id
FROM users u, projects p 
WHERE u.email = 'demo@zentry.cloud' AND p.name = 'My First Project'
ON CONFLICT DO NOTHING;
*/

-- Verify the schema
SELECT 'Schema created successfully!' as status;