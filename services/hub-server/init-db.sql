-- Database initialization script for Fin-Hub
-- Creates necessary extensions and initial data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSON extension
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for better performance
-- These will be created by SQLAlchemy migrations, but we can add additional ones here if needed

-- Insert initial data or configurations if needed
-- This script runs only once during container initialization

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE fin_hub TO fin_hub;
GRANT ALL ON SCHEMA public TO fin_hub;