USE school_votes;

INSERT INTO app_settings (setting_key, setting_value)
VALUES
  ('school_motto', 'Integrity and Leadership')
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value);

-- Create admin users through:
-- flask --app app.py create-admin
