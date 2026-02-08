-- Migration 007: User Preferences for Cross-Device State Sync
-- Created: 2025-11-08
-- Purpose: Store user UI preferences and session context for cross-device persistence

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Session context
    active_session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
    
    -- Draft messages per session (JSONB for flexibility)
    -- Format: { "session-123": "draft text", "session-456": "another draft" }
    draft_messages JSONB DEFAULT '{}',
    
    -- Active tab per session
    -- Format: { "session-123": "chat", "session-456": "objects" }
    active_tabs JSONB DEFAULT '{}',
    
    -- UI preferences
    -- Format: { "theme": "light", "viewMode": "grid", "sidebarCollapsed": false }
    ui_preferences JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_active_session ON user_preferences(active_session_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_updated ON user_preferences(updated_at);

-- GIN index for JSONB queries (in case we need to search drafts/prefs)
CREATE INDEX IF NOT EXISTS idx_user_preferences_draft_messages ON user_preferences USING GIN (draft_messages);
CREATE INDEX IF NOT EXISTS idx_user_preferences_ui_prefs ON user_preferences USING GIN (ui_preferences);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_user_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_preferences_updated_at();

-- Comments for documentation
COMMENT ON TABLE user_preferences IS 'Stores user UI preferences and session context for cross-device state synchronization';
COMMENT ON COLUMN user_preferences.active_session_id IS 'Last active session ID for restoring user context';
COMMENT ON COLUMN user_preferences.draft_messages IS 'Unsent draft messages per session (JSONB)';
COMMENT ON COLUMN user_preferences.active_tabs IS 'Active tab selection per session (JSONB)';
COMMENT ON COLUMN user_preferences.ui_preferences IS 'User UI preferences like theme, view mode, sidebar state (JSONB)';
