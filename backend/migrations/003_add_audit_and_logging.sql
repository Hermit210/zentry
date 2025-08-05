-- Add audit logging and system monitoring tables
-- This migration creates tables for tracking system events and audit logs

-- System health monitoring table
CREATE TABLE IF NOT EXISTS system_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'warning', 'critical', 'unknown')),
    message TEXT,
    metrics JSONB,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table for tracking important system events
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- VM state transitions table for detailed tracking
CREATE TABLE IF NOT EXISTS vm_state_transitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vm_id UUID NOT NULL REFERENCES vms(id) ON DELETE CASCADE,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    reason TEXT,
    triggered_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Database connection pool metrics
CREATE TABLE IF NOT EXISTS connection_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    active_connections INTEGER NOT NULL,
    idle_connections INTEGER NOT NULL,
    total_connections INTEGER NOT NULL,
    max_connections INTEGER NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit and monitoring tables
CREATE INDEX IF NOT EXISTS idx_system_health_component ON system_health(component);
CREATE INDEX IF NOT EXISTS idx_system_health_checked_at ON system_health(checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vm_state_transitions_vm_id ON vm_state_transitions(vm_id);
CREATE INDEX IF NOT EXISTS idx_vm_state_transitions_created_at ON vm_state_transitions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_connection_metrics_recorded_at ON connection_metrics(recorded_at DESC);

-- Function to log VM state transitions
CREATE OR REPLACE FUNCTION log_vm_state_transition()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if status actually changed
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO vm_state_transitions (vm_id, from_status, to_status, reason)
        VALUES (NEW.id, OLD.status, NEW.status, 'Status updated');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for VM state transitions
CREATE TRIGGER log_vm_state_transition_trigger
    AFTER UPDATE ON vms
    FOR EACH ROW
    EXECUTE FUNCTION log_vm_state_transition();

-- Function to clean up old audit logs (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Also clean up old system health records
    DELETE FROM system_health 
    WHERE checked_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * (retention_days / 2);
    
    -- Clean up old connection metrics (keep only 30 days)
    DELETE FROM connection_metrics 
    WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Clean up old VM metrics (keep only 60 days)
    DELETE FROM vm_metrics 
    WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL '60 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to record system health
CREATE OR REPLACE FUNCTION record_system_health(
    p_component VARCHAR(50),
    p_status VARCHAR(20),
    p_message TEXT DEFAULT NULL,
    p_metrics JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    health_id UUID;
BEGIN
    INSERT INTO system_health (component, status, message, metrics)
    VALUES (p_component, p_status, p_message, p_metrics)
    RETURNING id INTO health_id;
    
    RETURN health_id;
END;
$$ LANGUAGE plpgsql;