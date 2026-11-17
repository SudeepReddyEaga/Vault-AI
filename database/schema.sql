-- =========================================================================
-- AMAZON-GRADE E-COMMERCE & RURAL ENTERPRISE RELATIONAL DATABASE SCHEMA
-- Compatible with PostgreSQL 13+
-- =========================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Base Users Table (Core Identity & RBAC)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('customer', 'seller', 'admin')),
    status VARCHAR(50) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION')),
    is_email_verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Customer Profiles (Amazon Consumer & Rural Beneficiary)
CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(25) NOT NULL,
    avatar_url TEXT,
    kyc_status VARCHAR(50) DEFAULT 'VERIFIED_AADHAAR',
    aadhaar_last_four VARCHAR(4),
    
    -- Geographic & Gram Panchayat Catchment (for 5-10km feasibility)
    village VARCHAR(100) NOT NULL,
    gram_panchayat VARCHAR(100),
    block VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    shipping_address JSONB NOT NULL,
    
    -- Enterprise Concessional Financials (Module 2)
    available_margin_capital NUMERIC(12, 2) DEFAULT 100000.00,
    margin_percentage NUMERIC(5, 2) DEFAULT 10.00,
    target_business_category VARCHAR(100) DEFAULT 'Dairy',
    feasible_project_cost NUMERIC(12, 2) DEFAULT 1000000.00,
    eligible_concessional_scheme VARCHAR(100) DEFAULT 'Term Loan Scheme',
    eligible_loan_amount NUMERIC(12, 2) DEFAULT 900000.00,
    concessional_interest_rate_pa NUMERIC(5, 2) DEFAULT 8.00,
    tenure_years INT DEFAULT 7,
    moratorium_months INT DEFAULT 6,
    quarterly_emi NUMERIC(12, 2) DEFAULT 40500.00,
    dscr_health_score INT DEFAULT 88,
    
    -- Amazon Prime / Rural Subsidy Membership
    customer_tier VARCHAR(50) DEFAULT 'PRIME_RURAL_BENEFICIARY',
    subsidy_card_number VARCHAR(100),
    digital_wallet_balance NUMERIC(12, 2) DEFAULT 0.00,
    preferred_language VARCHAR(10) DEFAULT 'en',
    browsing_interests JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Seller Profiles (Amazon Seller Central Merchant & Machinery Supplier)
CREATE TABLE IF NOT EXISTS seller_profiles (
    seller_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant_store_name VARCHAR(255) NOT NULL,
    legal_company_name VARCHAR(255) NOT NULL,
    seller_tier VARCHAR(50) DEFAULT 'PLATINUM_RURAL_HUB',
    merchant_badge VARCHAR(100) DEFAULT 'Amazon Fulfilled (FBA) & SCA Certified',
    
    -- Compliance, GSTIN & SCA Licensing
    compliance_tax JSONB NOT NULL,
    
    -- Logistics, Warehousing & Fulfillment
    fulfillment_logistics JSONB NOT NULL,
    
    -- Merchant Performance Metrics
    merchant_performance JSONB NOT NULL,
    
    -- Financial Settlements & Bank Details
    financial_settlement JSONB NOT NULL,
    
    top_product_asins JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Products / ASIN Inventory Catalog
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    asin VARCHAR(20) UNIQUE NOT NULL,
    seller_id INT NOT NULL REFERENCES seller_profiles(seller_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    cost_price NUMERIC(12, 2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 50,
    sku VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    images JSONB DEFAULT '[]'::jsonb,
    sales_count INT DEFAULT 0,
    average_rating NUMERIC(3, 2) DEFAULT 4.8,
    is_top_selling BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Orders & Concessional Purchases
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    order_reference VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    seller_id INT NOT NULL REFERENCES seller_profiles(seller_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL DEFAULT 1,
    unit_price NUMERIC(12, 2) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    payment_method VARCHAR(100) DEFAULT 'SCA_CONCESSIONAL_CREDIT_90',
    order_status VARCHAR(50) DEFAULT 'CONFIRMED' CHECK (order_status IN ('PENDING', 'CONFIRMED', 'DISPATCHED', 'DELIVERED', 'CANCELLED')),
    shipping_tracking_number VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Amazon-Scale Performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_customers_village_block ON customer_profiles(village, block, district);
CREATE INDEX IF NOT EXISTS idx_sellers_store_name ON seller_profiles(merchant_store_name);
CREATE INDEX IF NOT EXISTS idx_products_asin ON products(asin);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_is_top_selling ON products(is_top_selling);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_seller ON orders(seller_id);
