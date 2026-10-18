-- =====================================================================
-- BITETECH TECHNOLOGIES — HIGH SECURITY WAMP SERVER MYSQL SETUP SCRIPT
-- Compatible with WAMP Server (MySQL 5.7, 8.0, 8.4+, MariaDB 10+)
-- Implements Principle of Least Privilege & Audit Logging Schema
-- =====================================================================

-- Step 1: Create Database
CREATE DATABASE IF NOT EXISTS `bitetech_db` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `bitetech_db`;

-- Step 2: Dedicated Least-Privilege Application User
-- CRITICAL SECURITY RULE: Never connect as 'root' from the web application!
CREATE USER IF NOT EXISTS 'bitetech_app'@'localhost' IDENTIFIED BY 'ChangeThisToAStrongAppPassword2026!';
GRANT SELECT, INSERT, UPDATE, DELETE ON `bitetech_db`.* TO 'bitetech_app'@'localhost';
FLUSH PRIVILEGES;

-- Step 3: Create Users Table (Role-based: admin, customer, student)
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(64) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(100) NULL,
    `phone` VARCHAR(30) NULL,
    `role` VARCHAR(30) NOT NULL DEFAULT 'customer',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `failed_logins` INT NOT NULL DEFAULT 0,
    `locked_until` DATETIME NULL,
    `last_login` DATETIME NULL,
    `mfa_secret` VARCHAR(64) NULL,
    `mfa_enabled` BOOLEAN NOT NULL DEFAULT FALSE,
    `token_version` INT NOT NULL DEFAULT 1,
    `password_changed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_username` (`username`),
    INDEX `idx_user_email` (`email`),
    INDEX `idx_user_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Backward compatibility view for legacy admin tools
CREATE OR REPLACE VIEW `admin_users` AS SELECT * FROM `users` WHERE `role` = 'admin';

-- Step 4: Create Password Reset Tokens Table
CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `token_hash` VARCHAR(128) NOT NULL UNIQUE,
    `expires_at` DATETIME NOT NULL,
    `used` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_prt_token` (`token_hash`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 5: Create Project Categories Table
CREATE TABLE IF NOT EXISTS `project_categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `slug` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_cat_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 6: Create Projects Table (Mini Starts ₹599, Major Starts ₹1,000)
CREATE TABLE IF NOT EXISTS `projects` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `slug` VARCHAR(200) NOT NULL UNIQUE,
    `category_id` INT NULL,
    `project_type` VARCHAR(50) NOT NULL DEFAULT 'Mini',
    `short_description` VARCHAR(350) NOT NULL,
    `full_description` LONGTEXT NOT NULL,
    `problem_statement` TEXT NULL,
    `features` TEXT NULL,
    `deliverables` TEXT NULL,
    `tech_stack` VARCHAR(255) NOT NULL DEFAULT 'Python, Flask, MySQL',
    `starting_price` INT NOT NULL DEFAULT 599,
    `price_range` VARCHAR(100) NOT NULL DEFAULT 'From ₹599',
    `source_code_included` BOOLEAN NOT NULL DEFAULT TRUE,
    `availability_status` VARCHAR(50) NOT NULL DEFAULT 'Available',
    `is_demo` BOOLEAN NOT NULL DEFAULT TRUE,
    `is_published` BOOLEAN NOT NULL DEFAULT TRUE,
    `is_featured` BOOLEAN NOT NULL DEFAULT FALSE,
    `image_url` VARCHAR(500) NULL,
    `demo_link` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_project_slug` (`slug`),
    INDEX `idx_project_type` (`project_type`),
    INDEX `idx_project_published` (`is_published`),
    FOREIGN KEY (`category_id`) REFERENCES `project_categories`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 7: Create Website & Software Services Table (Shop ₹5,000, Hosting ₹7,000)
CREATE TABLE IF NOT EXISTS `services` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `slug` VARCHAR(200) NOT NULL UNIQUE,
    `starting_price` VARCHAR(100) NOT NULL DEFAULT '₹5,000',
    `price_integer` INT NOT NULL DEFAULT 5000,
    `timeline` VARCHAR(100) NOT NULL DEFAULT '7-14 Days',
    `short_description` VARCHAR(350) NOT NULL,
    `full_description` LONGTEXT NOT NULL,
    `features` TEXT NULL,
    `deliverables` TEXT NULL,
    `project_requirements` TEXT NULL,
    `hosting_duration` VARCHAR(100) NULL DEFAULT '1 Year Included',
    `domain_included` VARCHAR(100) NULL DEFAULT '.com or .in Included',
    `renewal_cost` VARCHAR(100) NULL DEFAULT '₹2,500/year',
    `additional_charges` TEXT NULL,
    `is_published` BOOLEAN NOT NULL DEFAULT TRUE,
    `is_featured` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_service_slug` (`slug`),
    INDEX `idx_service_published` (`is_published`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 8: Create Online Courses Table (All Official Fees ₹299 - ₹1,499)
CREATE TABLE IF NOT EXISTS `courses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `slug` VARCHAR(200) NOT NULL UNIQUE,
    `level` VARCHAR(50) NOT NULL DEFAULT 'Beginner',
    `duration` VARCHAR(100) NOT NULL DEFAULT '4 Weeks',
    `price` VARCHAR(100) NOT NULL DEFAULT '₹899',
    `fee_integer` INT NOT NULL DEFAULT 899,
    `delivery_mode` VARCHAR(100) NOT NULL DEFAULT 'Online Live Mentoring',
    `class_schedule` VARCHAR(150) NOT NULL DEFAULT 'Weekend Batches (Sat-Sun)',
    `teaching_format` VARCHAR(150) NOT NULL DEFAULT 'Live Interactive Sessions + Doubt Support',
    `status` VARCHAR(50) NOT NULL DEFAULT 'Open for Admissions',
    `short_description` VARCHAR(350) NOT NULL,
    `syllabus` LONGTEXT NOT NULL,
    `outcomes` TEXT NULL,
    `prerequisites` VARCHAR(255) NULL,
    `badge_text` VARCHAR(50) NULL,
    `is_published` BOOLEAN NOT NULL DEFAULT TRUE,
    `is_featured` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_course_slug` (`slug`),
    INDEX `idx_course_published` (`is_published`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 9: Create Portfolio Items Table
CREATE TABLE IF NOT EXISTS `portfolio_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `category` VARCHAR(100) NOT NULL,
    `description` TEXT NOT NULL,
    `client_type` VARCHAR(150) NOT NULL DEFAULT 'Academic / Engineering Reference',
    `features` TEXT NULL,
    `technologies` VARCHAR(255) NOT NULL,
    `image_url` VARCHAR(500) NULL,
    `live_url` VARCHAR(500) NULL,
    `is_published` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_portfolio_published` (`is_published`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 10: Create Project Enquiries Table (With Customer Account Association)
CREATE TABLE IF NOT EXISTS `project_enquiries` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `project_id` INT NULL,
    `client_name` VARCHAR(120) NOT NULL,
    `client_email` VARCHAR(120) NOT NULL,
    `client_phone` VARCHAR(30) NOT NULL,
    `project_type` VARCHAR(100) NULL,
    `budget_range` VARCHAR(100) NOT NULL DEFAULT '₹599 - ₹1,000',
    `requirements` TEXT NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'New',
    `admin_notes` TEXT NULL,
    `company_response` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_pe_status` (`status`),
    INDEX `idx_pe_user` (`user_id`),
    INDEX `idx_pe_created` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 11: Create Service Quotation Enquiries Table
CREATE TABLE IF NOT EXISTS `service_enquiries` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `service_id` INT NULL,
    `client_name` VARCHAR(120) NOT NULL,
    `client_email` VARCHAR(120) NOT NULL,
    `client_phone` VARCHAR(30) NOT NULL,
    `project_title` VARCHAR(200) NOT NULL,
    `budget_range` VARCHAR(100) NOT NULL DEFAULT '₹5,000 - ₹7,000',
    `timeline` VARCHAR(100) NULL,
    `project_requirements` TEXT NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'New',
    `admin_notes` TEXT NULL,
    `company_response` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_se_status` (`status`),
    INDEX `idx_se_user` (`user_id`),
    INDEX `idx_se_created` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`service_id`) REFERENCES `services`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 12: Create Course Enquiries Table
CREATE TABLE IF NOT EXISTS `course_enquiries` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `course_id` INT NULL,
    `student_name` VARCHAR(120) NOT NULL,
    `student_email` VARCHAR(120) NOT NULL,
    `student_phone` VARCHAR(30) NOT NULL,
    `preferred_batch` VARCHAR(100) NOT NULL DEFAULT 'Weekend Batches (Sat-Sun)',
    `learning_mode` VARCHAR(100) NOT NULL DEFAULT 'Online Live Mentoring (Zoom/Meet)',
    `message` TEXT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'New',
    `admin_notes` TEXT NULL,
    `company_response` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_ce_status` (`status`),
    INDEX `idx_ce_user` (`user_id`),
    INDEX `idx_ce_created` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`course_id`) REFERENCES `courses`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 13: Create Project Orders Table
CREATE TABLE IF NOT EXISTS `project_orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_reference` VARCHAR(64) NOT NULL UNIQUE,
    `user_id` INT NOT NULL,
    `project_id` INT NULL,
    `project_title` VARCHAR(200) NOT NULL,
    `amount` INT NOT NULL,
    `payment_status` VARCHAR(30) NOT NULL DEFAULT 'Pending',
    `order_status` VARCHAR(30) NOT NULL DEFAULT 'Received',
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_po_ref` (`order_reference`),
    INDEX `idx_po_user` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 14: Create Contact Messages Table
CREATE TABLE IF NOT EXISTS `contact_messages` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(120) NOT NULL,
    `phone` VARCHAR(30) NOT NULL,
    `subject` VARCHAR(200) NOT NULL,
    `service` VARCHAR(100) NOT NULL DEFAULT 'Python Mini-Project Development',
    `budget` VARCHAR(100) NOT NULL DEFAULT '₹599 - ₹1,000',
    `message` TEXT NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'New',
    `admin_notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_cm_status` (`status`),
    INDEX `idx_cm_user` (`user_id`),
    INDEX `idx_cm_created` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 15: Create FAQs Table
CREATE TABLE IF NOT EXISTS `faqs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `question` VARCHAR(300) NOT NULL,
    `answer` TEXT NOT NULL,
    `category` VARCHAR(100) NOT NULL DEFAULT 'General',
    `display_order` INT NOT NULL DEFAULT 0,
    `is_published` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_faq_published` (`is_published`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 16: Create Site Settings Table
CREATE TABLE IF NOT EXISTS `site_settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(80) NOT NULL UNIQUE,
    `value` LONGTEXT NULL,
    `description` VARCHAR(255) NULL,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_setting_key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 17: Create Security Audit Logs Table
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `user_id` INT NULL,
    `username` VARCHAR(64) NULL,
    `action` VARCHAR(100) NOT NULL,
    `target_type` VARCHAR(50) NULL,
    `target_id` VARCHAR(50) NULL,
    `details` TEXT NULL,
    `ip_address` VARCHAR(45) NULL,
    `user_agent` VARCHAR(255) NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    INDEX `idx_audit_timestamp` (`timestamp`),
    INDEX `idx_audit_action` (`action`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Confirmation
SELECT 'Bitetech Technologies Complete High-Security MySQL schema successfully synchronized with least-privilege user bitetech_app.' AS `Status`;
