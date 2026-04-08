CREATE DATABASE IF NOT EXISTS school_votes
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE school_votes;

CREATE TABLE IF NOT EXISTS admins (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  full_name VARCHAR(160) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  last_login_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS elections (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(180) NOT NULL,
  description TEXT NULL,
  start_at DATETIME NULL,
  end_at DATETIME NULL,
  status ENUM('DRAFT', 'OPEN', 'PAUSED', 'CLOSED') NOT NULL DEFAULT 'DRAFT',
  results_visible TINYINT(1) NOT NULL DEFAULT 0,
  created_by BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_elections_created_by FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE RESTRICT,
  INDEX idx_elections_status (status),
  INDEX idx_elections_created_at (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS positions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  election_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(160) NOT NULL,
  display_order INT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_positions_election FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
  UNIQUE KEY uq_positions_election_name (election_id, name),
  INDEX idx_positions_election_order (election_id, display_order)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS candidates (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  election_id BIGINT UNSIGNED NOT NULL,
  position_id BIGINT UNSIGNED NOT NULL,
  full_name VARCHAR(180) NOT NULL,
  class_name VARCHAR(80) NOT NULL,
  gender VARCHAR(30) NULL,
  bio TEXT NULL,
  photo_path VARCHAR(255) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_candidates_election FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
  CONSTRAINT fk_candidates_position FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
  INDEX idx_candidates_election_position (election_id, position_id),
  INDEX idx_candidates_name (full_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS voters (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  election_id BIGINT UNSIGNED NOT NULL,
  student_id VARCHAR(80) NOT NULL,
  full_name VARCHAR(180) NOT NULL,
  class_name VARCHAR(80) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_voters_election FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
  UNIQUE KEY uq_voters_election_student (election_id, student_id),
  INDEX idx_voters_election_active (election_id, is_active),
  INDEX idx_voters_student_id (student_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS voter_credentials (
  voter_id BIGINT UNSIGNED PRIMARY KEY,
  pin_hash VARCHAR(255) NULL,
  pin_required TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_credentials_voter FOREIGN KEY (voter_id) REFERENCES voters(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ballots (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  election_id BIGINT UNSIGNED NOT NULL,
  voter_id BIGINT UNSIGNED NOT NULL,
  client_ip VARCHAR(64) NULL,
  user_agent VARCHAR(255) NULL,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ballots_election FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
  CONSTRAINT fk_ballots_voter FOREIGN KEY (voter_id) REFERENCES voters(id) ON DELETE CASCADE,
  UNIQUE KEY uq_ballot_per_voter (election_id, voter_id),
  INDEX idx_ballots_submitted_at (submitted_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ballot_items (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ballot_id BIGINT UNSIGNED NOT NULL,
  position_id BIGINT UNSIGNED NOT NULL,
  candidate_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ballot_items_ballot FOREIGN KEY (ballot_id) REFERENCES ballots(id) ON DELETE CASCADE,
  CONSTRAINT fk_ballot_items_position FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE RESTRICT,
  CONSTRAINT fk_ballot_items_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE RESTRICT,
  UNIQUE KEY uq_position_once_per_ballot (ballot_id, position_id),
  INDEX idx_ballot_items_candidate (candidate_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  admin_id BIGINT UNSIGNED NULL,
  action VARCHAR(80) NOT NULL,
  entity_type VARCHAR(80) NOT NULL,
  entity_id BIGINT UNSIGNED NULL,
  details TEXT NULL,
  ip_address VARCHAR(64) NULL,
  user_agent VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_logs_admin FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL,
  INDEX idx_audit_action (action),
  INDEX idx_audit_entity (entity_type, entity_id),
  INDEX idx_audit_created_at (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS app_settings (
  setting_key VARCHAR(120) PRIMARY KEY,
  setting_value TEXT NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO app_settings (setting_key, setting_value)
VALUES
  ('school_name', 'School Prefectorial Election'),
  ('privacy_note', 'Ballots are linked to voter records only to enforce one-student-one-vote.')
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value);

