-- MedEase Database Setup
-- Run this file once on any new server to set up everything
-- Command: mysql -u root -p < database/setup.sql

CREATE DATABASE IF NOT EXISTS medease_db;
USE medease_db;

-- ── TABLES ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_name VARCHAR(100),
    generic_name VARCHAR(100),
    composition VARCHAR(200),
    price_brand DECIMAL(8,2),
    price_generic DECIMAL(8,2)
);

CREATE TABLE IF NOT EXISTS normal_ranges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_name VARCHAR(100),
    min_val DECIMAL(10,2),
    max_val DECIMAL(10,2),
    unit VARCHAR(20),
    source VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── MEDICINES DATA ───────────────────────────────────

INSERT INTO medicines (brand_name, generic_name, composition, price_brand, price_generic) VALUES
('Crocin', 'Paracetamol 500mg', 'Paracetamol', 30.00, 2.50),
('Dolo 650', 'Paracetamol 650mg', 'Paracetamol', 35.00, 3.00),
('Combiflam', 'Ibuprofen+Paracetamol', 'Ibuprofen, Paracetamol', 35.00, 4.00),
('Augmentin 625', 'Amoxicillin+Clavulanate 625mg', 'Amoxicillin, Clavulanic Acid', 180.00, 45.00),
('Metformin 500', 'Metformin 500mg', 'Metformin HCl', 25.00, 3.50),
('Ecosprin 75', 'Aspirin 75mg', 'Aspirin', 20.00, 1.50),
('Atorva 40', 'Atorvastatin 40mg', 'Atorvastatin', 120.00, 15.00),
('Pan 40', 'Pantoprazole 40mg', 'Pantoprazole', 55.00, 5.00),
('Azithral 500', 'Azithromycin 500mg', 'Azithromycin', 90.00, 12.00),
('Allegra 120', 'Fexofenadine 120mg', 'Fexofenadine', 75.00, 8.00),
('Metoprolol 25', 'Metoprolol 25mg', 'Metoprolol Tartrate', 40.00, 5.00),
('Cetrizine', 'Cetirizine 10mg', 'Cetirizine HCl', 25.00, 1.50),
('Shelcal 500', 'Calcium+Vit D3', 'Calcium Carbonate, Vitamin D3', 85.00, 10.00),
('Limcee', 'Vitamin C 500mg', 'Ascorbic Acid', 30.00, 2.00),
('Zincovit', 'Multivitamin+Zinc', 'Vitamins, Minerals, Zinc', 95.00, 12.00);

-- ── NORMAL RANGES DATA ───────────────────────────────

INSERT INTO normal_ranges (test_name, min_val, max_val, unit, source) VALUES
('Haemoglobin', 12.0, 17.0, 'g/dL', 'ICMR 2023'),
('Fasting Glucose', 70, 100, 'mg/dL', 'ADA Guidelines'),
('Creatinine', 0.6, 1.2, 'mg/dL', 'ICMR 2023'),
('Platelets', 150000, 400000, '/µL', 'ICMR 2023'),
('WBC', 4000, 11000, '/µL', 'ICMR 2023'),
('Sodium', 136, 145, 'mEq/L', 'ICMR 2023'),
('Potassium', 3.5, 5.0, 'mEq/L', 'ICMR 2023'),
('HbA1c', 0, 5.6, '%', 'ADA Guidelines'),
('TSH', 0.4, 4.0, 'mIU/L', 'ICMR 2023'),
('Cholesterol', 0, 200, 'mg/dL', 'ACC Guidelines');

-- ── MEDICAL RECORDS TABLES ───────────────────────────

CREATE TABLE IF NOT EXISTS folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    folder_id INT NULL,
    report_type VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    original_text TEXT NULL,
    original_pdf_path VARCHAR(255) NULL,
    analysis_result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL
);