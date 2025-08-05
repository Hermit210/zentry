-- Enhanced indexing and constraints for better performance and data integrity
-- This migration adds additional indexes, constraints, and optimizations

-- Add composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_vms_user_status ON vms(user_id, status);
CREATE INDEX IF NOT EXISTS idx_vms_project_status ON vms(project_id, status);
CREATE INDEX IF NOT EXISTS idx_billing_records_user_date ON billing_records(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vm_metrics_vm_date ON vm_metrics(vm_id, recorded_at DESC);

-- Add partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_users_active ON users(id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_vms_running ON vms(id, user_id) WHERE status = 'running';

-- Add constraints for data integrity
ALTER TABLE users ADD CONSTRAINT chk_users_credits_positive CHECK (credits >= 0);
ALTER TABLE users ADD CONSTRAINT chk_users_total_spent_positive CHECK (total_spent >= 0);
ALTER TABLE vms ADD CONSTRAINT chk_vms_uptime_positive CHECK (uptime_hours >= 0);
ALTER TABLE vms ADD CONSTRAINT chk_vms_total_cost_positive CHECK (total_cost >= 0);
ALTER TABLE vms ADD CONSTRAINT chk_vms_cost_per_hour_positive CHECK (cost_per_hour > 0);

-- Add check constraints for billing records
ALTER TABLE billing_records ADD CONSTRAINT chk_billing_amount_not_zero CHECK (amount != 0);

-- Create function to automatically update VM costs
CREATE OR REPLACE FUNCTION update_vm_costs()
RETURNS TRIGGER AS $$
BEGIN
    -- Update cost per hour based on instance type
    NEW.cost_per_hour = CASE NEW.instance_type
        WHEN 'small' THEN 0.05
        WHEN 'medium' THEN 0.10
        WHEN 'large' THEN 0.20
        WHEN 'xlarge' THEN 0.40
        ELSE 0.05
    END;
    
    -- Calculate total cost based on uptime
    NEW.total_cost = NEW.uptime_hours * NEW.cost_per_hour;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for VM cost updates
CREATE TRIGGER update_vm_costs_trigger
    BEFORE INSERT OR UPDATE ON vms
    FOR EACH ROW
    EXECUTE FUNCTION update_vm_costs();

-- Create function to track user spending
CREATE OR REPLACE FUNCTION update_user_spending()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user's total spent when billing record is created
    IF TG_OP = 'INSERT' AND NEW.amount > 0 THEN
        UPDATE users 
        SET total_spent = total_spent + NEW.amount
        WHERE id = NEW.user_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for user spending updates
CREATE TRIGGER update_user_spending_trigger
    AFTER INSERT ON billing_records
    FOR EACH ROW
    EXECUTE FUNCTION update_user_spending();

-- Add materialized view for user statistics (optional, for performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS user_stats AS
SELECT 
    u.id,
    u.email,
    u.name,
    u.credits,
    u.total_spent,
    COUNT(DISTINCT p.id) as project_count,
    COUNT(DISTINCT v.id) as vm_count,
    COUNT(DISTINCT CASE WHEN v.status = 'running' THEN v.id END) as running_vm_count,
    COALESCE(SUM(v.uptime_hours), 0) as total_uptime_hours,
    COALESCE(SUM(v.total_cost), 0) as total_vm_costs
FROM users u
LEFT JOIN projects p ON u.id = p.user_id
LEFT JOIN vms v ON u.id = v.user_id
GROUP BY u.id, u.email, u.name, u.credits, u.total_spent;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_stats_id ON user_stats(id);

-- Create function to refresh user stats
CREATE OR REPLACE FUNCTION refresh_user_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_stats;
END;
$$ LANGUAGE plpgsql;