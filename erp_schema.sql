-- ERP Bengkel PostgreSQL Database Schema
-- Generated from Django models
-- Created: 2025-11-06

-- Drop all tables in correct order (to avoid foreign key constraints)
DROP TABLE IF EXISTS payment CASCADE;
DROP TABLE IF EXISTS journal_entry_line CASCADE;
DROP TABLE IF EXISTS journal_entry CASCADE;
DROP TABLE IF EXISTS transaction CASCADE;
DROP TABLE IF EXISTS budget_line CASCADE;
DROP TABLE IF EXISTS budget CASCADE;
DROP TABLE IF EXISTS tax_rate CASCADE;
DROP TABLE IF EXISTS financial_period CASCADE;
DROP TABLE IF EXISTS account CASCADE;
DROP TABLE IF EXISTS product_pricing CASCADE;
DROP TABLE IF EXISTS sales_order_item CASCADE;
DROP TABLE IF EXISTS invoice CASCADE;
DROP TABLE IF EXISTS sales_order CASCADE;
DROP TABLE IF EXISTS customer CASCADE;
DROP TABLE IF EXISTS goods_receipt_line_item CASCADE;
DROP TABLE IF EXISTS goods_receipt CASCADE;
DROP TABLE IF EXISTS purchase_order_line_item CASCADE;
DROP TABLE IF EXISTS purchase_order CASCADE;
DROP TABLE IF EXISTS vendor CASCADE;
DROP TABLE IF EXISTS production_progress CASCADE;
DROP TABLE IF EXISTS material_consumption CASCADE;
DROP TABLE IF EXISTS work_order CASCADE;
DROP TABLE IF EXISTS bom_item CASCADE;
DROP TABLE IF EXISTS bill_of_materials CASCADE;
DROP TABLE IF EXISTS production_order CASCADE;
DROP TABLE IF EXISTS stock_alert CASCADE;
DROP TABLE IF EXISTS inventory_transaction CASCADE;
DROP TABLE IF EXISTS finished_product CASCADE;
DROP TABLE IF EXISTS product_category CASCADE;
DROP TABLE IF EXISTS raw_material CASCADE;
DROP TABLE IF EXISTS material_category CASCADE;
DROP TABLE IF EXISTS warehouse CASCADE;
DROP TABLE IF EXISTS user_profile CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Django auth_user table (simplified version)
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_staff BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Accounts Module
CREATE TABLE user_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'warehouse_staff' CHECK (role IN ('admin', 'production_manager', 'purchase_manager', 'sales_manager', 'finance_manager', 'warehouse_staff')),
    phone VARCHAR(15),
    department VARCHAR(100),
    employee_id VARCHAR(20) UNIQUE
);

-- Inventory Module
CREATE TABLE warehouse (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE material_category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE raw_material (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES material_category(id) ON DELETE CASCADE,
    unit VARCHAR(10) CHECK (unit IN ('kg', 'm', 'pcs', 'roll', 'sheet')),
    description TEXT,
    minimum_stock DECIMAL(10,2) DEFAULT 0,
    current_stock DECIMAL(10,2) DEFAULT 0,
    unit_price DECIMAL(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE product_category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE finished_product (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES product_category(id) ON DELETE CASCADE,
    size VARCHAR(10) CHECK (size IN ('35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45')),
    color VARCHAR(20) CHECK (color IN ('black', 'white', 'brown', 'blue', 'red', 'green', 'yellow', 'gray', 'navy', 'beige', 'sands')),
    description TEXT,
    current_stock INTEGER DEFAULT 0,
    minimum_stock INTEGER DEFAULT 0,
    unit_price DECIMAL(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory_transaction (
    id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(3) CHECK (transaction_type IN ('IN', 'OUT', 'ADJ')),
    material_type VARCHAR(10) CHECK (material_type IN ('raw', 'finished')),
    material_id INTEGER NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) DEFAULT 0,
    total_value DECIMAL(12,2) DEFAULT 0,
    reference_number VARCHAR(50),
    notes TEXT,
    warehouse_id INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    created_by INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE stock_alert (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(20) CHECK (alert_type IN ('low_stock', 'out_of_stock', 'over_stock')),
    material_type VARCHAR(10) CHECK (material_type IN ('raw', 'finished')),
    material_id INTEGER NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    current_stock DECIMAL(10,2) NOT NULL,
    threshold DECIMAL(10,2) NOT NULL,
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Manufacturing Module
CREATE TABLE production_order (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(20) UNIQUE NOT NULL,
    product_id INTEGER NOT NULL REFERENCES finished_product(id) ON DELETE CASCADE,
    quantity DECIMAL(10,2) NOT NULL,
    planned_start_date DATE NOT NULL,
    planned_end_date DATE NOT NULL,
    actual_start_date DATE,
    actual_end_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending_approval', 'approved', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    created_by INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    approved_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE bill_of_materials (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE NOT NULL REFERENCES finished_product(id) ON DELETE CASCADE,
    version VARCHAR(10) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    total_cost DECIMAL(12,2) DEFAULT 0,
    labor_cost DECIMAL(10,2) DEFAULT 0,
    overhead_cost DECIMAL(10,2) DEFAULT 0,
    created_by INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE bom_item (
    id SERIAL PRIMARY KEY,
    bom_id INTEGER NOT NULL REFERENCES bill_of_materials(id) ON DELETE CASCADE,
    material_id INTEGER NOT NULL REFERENCES raw_material(id) ON DELETE CASCADE,
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2) NOT NULL,
    allocated_stages JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE work_order (
    id SERIAL PRIMARY KEY,
    wo_number VARCHAR(20) UNIQUE NOT NULL,
    production_order_id INTEGER NOT NULL REFERENCES production_order(id) ON DELETE CASCADE,
    stage VARCHAR(20) CHECK (stage IN ('gurat', 'assembly', 'press', 'finishing')),
    quantity DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'on_hold', 'cancelled')),
    planned_start_date DATE NOT NULL,
    planned_end_date DATE NOT NULL,
    actual_start_date DATE,
    actual_end_date DATE,
    assigned_to INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    supervisor INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE material_consumption (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER NOT NULL REFERENCES work_order(id) ON DELETE CASCADE,
    material_id INTEGER NOT NULL REFERENCES raw_material(id) ON DELETE CASCADE,
    planned_quantity DECIMAL(10,2) NOT NULL,
    actual_quantity DECIMAL(10,2) NOT NULL,
    consumption_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recorded_by INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE production_progress (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER NOT NULL REFERENCES work_order(id) ON DELETE CASCADE,
    progress_percentage DECIMAL(5,2) NOT NULL CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    quantity_completed DECIMAL(10,2) NOT NULL,
    progress_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recorded_by INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Module
CREATE TABLE vendor (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(254),
    phone VARCHAR(20),
    address TEXT,
    payment_terms VARCHAR(100),
    credit_limit DECIMAL(12,2) DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    on_time_deliveries INTEGER DEFAULT 0,
    quality_rating DECIMAL(3,2) DEFAULT 0 CHECK (quality_rating >= 0 AND quality_rating <= 5),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE purchase_order (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(20) UNIQUE NOT NULL,
    vendor_id INTEGER NOT NULL REFERENCES vendor(id) ON DELETE CASCADE,
    order_date DATE DEFAULT CURRENT_DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending_approval', 'approved', 'ordered', 'partially_received', 'received', 'cancelled')),
    total_amount DECIMAL(12,2) DEFAULT 0,
    created_by INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    approved_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE purchase_order_line_item (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_order(id) ON DELETE CASCADE,
    material_name VARCHAR(200) NOT NULL,
    description TEXT,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    received_quantity DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE goods_receipt (
    id SERIAL PRIMARY KEY,
    gr_number VARCHAR(20) UNIQUE NOT NULL,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_order(id) ON DELETE CASCADE,
    receipt_date DATE DEFAULT CURRENT_DATE,
    received_by INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    total_received_value DECIMAL(12,2) DEFAULT 0,
    quality_check_passed BOOLEAN DEFAULT TRUE,
    quality_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE goods_receipt_line_item (
    id SERIAL PRIMARY KEY,
    goods_receipt_id INTEGER NOT NULL REFERENCES goods_receipt(id) ON DELETE CASCADE,
    purchase_order_item_id INTEGER NOT NULL REFERENCES purchase_order_line_item(id) ON DELETE CASCADE,
    received_quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    quality_status VARCHAR(20) DEFAULT 'accepted' CHECK (quality_status IN ('accepted', 'rejected', 'pending')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Module
CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    customer_type VARCHAR(20) DEFAULT 'retail' CHECK (customer_type IN ('retail', 'wholesale', 'distributor', 'online')),
    credit_limit DECIMAL(12,2) DEFAULT 0,
    payment_terms VARCHAR(50) DEFAULT 'cod' CHECK (payment_terms IN ('cod', 'net_15', 'net_30', 'net_60', 'net_90')),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE sales_order (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    order_date DATE DEFAULT CURRENT_DATE,
    required_date DATE NOT NULL,
    ship_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')),
    subtotal DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    shipping_cost DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0,
    shipping_address TEXT,
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(100),
    notes TEXT,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE sales_order_item (
    id SERIAL PRIMARY KEY,
    sales_order_id INTEGER NOT NULL REFERENCES sales_order(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES finished_product(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    line_total DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE invoice (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    sales_order_id INTEGER UNIQUE NOT NULL REFERENCES sales_order(id) ON DELETE CASCADE,
    invoice_date DATE DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) NOT NULL,
    discount_amount DECIMAL(12,2) NOT NULL,
    shipping_cost DECIMAL(12,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'unpaid' CHECK (payment_status IN ('unpaid', 'partial', 'paid', 'overdue')),
    amount_paid DECIMAL(12,2) DEFAULT 0,
    payment_date DATE,
    payment_method VARCHAR(20) CHECK (payment_method IN ('cash', 'bank_transfer', 'credit_card', 'check')),
    notes TEXT,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE payment (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoice(id) ON DELETE CASCADE,
    payment_date DATE DEFAULT CURRENT_DATE,
    amount DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('cash', 'bank_transfer', 'credit_card', 'check')),
    reference_number VARCHAR(100),
    notes TEXT,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE product_pricing (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE NOT NULL REFERENCES finished_product(id) ON DELETE CASCADE,
    base_price DECIMAL(10,2) NOT NULL,
    wholesale_price DECIMAL(10,2) NOT NULL,
    retail_price DECIMAL(10,2) NOT NULL,
    discount_eligible BOOLEAN DEFAULT TRUE,
    max_discount_percent DECIMAL(5,2) DEFAULT 20,
    seasonal_price DECIMAL(10,2),
    seasonal_start_date DATE,
    seasonal_end_date DATE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
);

-- Finance Module
CREATE TABLE account (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    parent_account_id INTEGER REFERENCES account(id) ON DELETE SET NULL,
    balance DECIMAL(15,2) DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE transaction (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    description VARCHAR(500) NOT NULL,
    reference_number VARCHAR(100),
    account_id INTEGER NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('debit', 'credit')),
    amount DECIMAL(12,2) NOT NULL,
    sales_order_id INTEGER REFERENCES sales_order(id) ON DELETE SET NULL,
    purchase_order_id INTEGER REFERENCES purchase_order(id) ON DELETE SET NULL,
    invoice_id INTEGER REFERENCES invoice(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE journal_entry (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    description TEXT NOT NULL,
    reference_number VARCHAR(100) UNIQUE NOT NULL,
    is_posted BOOLEAN DEFAULT FALSE,
    posted_date TIMESTAMP WITH TIME ZONE,
    sales_order_id INTEGER REFERENCES sales_order(id) ON DELETE SET NULL,
    purchase_order_id INTEGER REFERENCES purchase_order(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE journal_entry_line (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL REFERENCES journal_entry(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('debit', 'credit')),
    amount DECIMAL(12,2) NOT NULL,
    description VARCHAR(200)
);

CREATE TABLE budget (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'active', 'closed')),
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE budget_line (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES budget(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    budgeted_amount DECIMAL(12,2) NOT NULL,
    actual_amount DECIMAL(12,2) DEFAULT 0,
    period DATE
);

CREATE TABLE tax_rate (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    rate DECIMAL(5,2) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    applicable_to_sales BOOLEAN DEFAULT TRUE,
    applicable_to_purchases BOOLEAN DEFAULT TRUE,
    effective_from DATE DEFAULT CURRENT_DATE,
    effective_to DATE,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE financial_period (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_date TIMESTAMP WITH TIME ZONE,
    closed_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_raw_material_code ON raw_material(code);
CREATE INDEX idx_raw_material_category ON raw_material(category_id);
CREATE INDEX idx_finished_product_code ON finished_product(code);
CREATE INDEX idx_finished_product_category ON finished_product(category_id);
CREATE INDEX idx_production_order_product ON production_order(product_id);
CREATE INDEX idx_production_order_status ON production_order(status);
CREATE INDEX idx_work_order_production ON work_order(production_order_id);
CREATE INDEX idx_work_order_stage ON work_order(stage);
CREATE INDEX idx_bom_item_material ON bom_item(material_id);
CREATE INDEX idx_purchase_order_vendor ON purchase_order(vendor_id);
CREATE INDEX idx_purchase_order_status ON purchase_order(status);
CREATE INDEX idx_sales_order_customer ON sales_order(customer_id);
CREATE INDEX idx_sales_order_status ON sales_order(status);
CREATE INDEX idx_invoice_sales_order ON invoice(sales_order_id);
CREATE INDEX idx_transaction_account ON transaction(account_id);
CREATE INDEX idx_transaction_date ON transaction(date);
CREATE INDEX idx_journal_entry_date ON journal_entry(date);
CREATE INDEX idx_inventory_transaction_material ON inventory_transaction(material_id);
CREATE INDEX idx_inventory_transaction_date ON inventory_transaction(created_at);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_warehouse_updated_at BEFORE UPDATE ON warehouse FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_raw_material_updated_at BEFORE UPDATE ON raw_material FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_finished_product_updated_at BEFORE UPDATE ON finished_product FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_production_order_updated_at BEFORE UPDATE ON production_order FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bill_of_materials_updated_at BEFORE UPDATE ON bill_of_materials FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_work_order_updated_at BEFORE UPDATE ON work_order FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_purchase_order_updated_at BEFORE UPDATE ON purchase_order FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_purchase_order_line_item_updated_at BEFORE UPDATE ON purchase_order_line_item FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_goods_receipt_updated_at BEFORE UPDATE ON goods_receipt FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customer_updated_at BEFORE UPDATE ON customer FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sales_order_updated_at BEFORE UPDATE ON sales_order FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_transaction_updated_at BEFORE UPDATE ON transaction FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_journal_entry_updated_at BEFORE UPDATE ON journal_entry FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_budget_updated_at BEFORE UPDATE ON budget FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vendor_updated_at BEFORE UPDATE ON vendor FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default data
INSERT INTO auth_user (username, email, first_name, last_name, is_staff, is_superuser) VALUES 
('admin', 'admin@erp-bengkel.com', 'System', 'Administrator', TRUE, TRUE);

-- Create default admin user profile
INSERT INTO user_profile (user_id, role, employee_id) VALUES 
(1, 'admin', 'EMP001');

-- Create default warehouse
INSERT INTO warehouse (name, location, description) VALUES 
('Main Warehouse', 'Jakarta, Indonesia', 'Primary storage facility');

-- Create default material categories
INSERT INTO material_category (name, description) VALUES 
('Leather', 'Various types of leather for shoe production'),
('Sole', 'Shoe soles and related materials'),
('Thread', 'Sewing threads and related items'),
('Adhesive', 'Glues and adhesives for assembly'),
('Packaging', 'Packaging materials');

-- Create default product categories
INSERT INTO product_category (name, description) VALUES 
('Men Shoes', 'Footwear for men'),
('Women Shoes', 'Footwear for women'),
('Sports Shoes', 'Athletic and sports footwear'),
('Casual Shoes', 'Everyday casual footwear');

-- Create default chart of accounts
INSERT INTO account (code, name, account_type, description) VALUES 
('1000', 'Cash', 'asset', 'Cash on hand and in bank'),
('1100', 'Accounts Receivable', 'asset', 'Money owed by customers'),
('1200', 'Inventory', 'asset', 'Raw materials and finished goods'),
('2000', 'Accounts Payable', 'liability', 'Money owed to vendors'),
('3000', 'Owner Equity', 'equity', 'Owner investment and retained earnings'),
('4000', 'Sales Revenue', 'revenue', 'Revenue from sales'),
('5000', 'Cost of Goods Sold', 'expense', 'Direct costs of production'),
('6000', 'Operating Expenses', 'expense', 'General operating expenses');

-- Create default financial periods
INSERT INTO financial_period (name, start_date, end_date) VALUES 
('January 2024', '2024-01-01', '2024-01-31'),
('February 2024', '2024-02-01', '2024-02-29'),
('March 2024', '2024-03-01', '2024-03-31');

-- Create default tax rates
INSERT INTO tax_rate (name, code, rate, description) VALUES 
('VAT', 'VAT', 11.00, 'Value Added Tax'),
('Sales Tax', 'ST', 10.00, 'Sales Tax on products');

-- Comments for documentation
COMMENT ON TABLE user_profile IS 'Extended user information with roles and employee details';
COMMENT ON TABLE warehouse IS 'Storage locations for inventory';
COMMENT ON TABLE material_category IS 'Categories for raw materials';
COMMENT ON TABLE raw_material IS 'Raw materials used in production';
COMMENT ON TABLE product_category IS 'Categories for finished products';
COMMENT ON TABLE finished_product IS 'Completed shoes ready for sale';
COMMENT ON TABLE inventory_transaction IS 'Stock movement tracking';
COMMENT ON TABLE stock_alert IS 'Low stock and inventory alerts';
COMMENT ON TABLE production_order IS 'Production orders for manufacturing';
COMMENT ON TABLE bill_of_materials IS 'BOM defining materials needed for products';
COMMENT ON TABLE bom_item IS 'Individual items in a BOM';
COMMENT ON TABLE work_order IS 'Work orders for production stages';
COMMENT ON TABLE material_consumption IS 'Tracking material usage in production';
COMMENT ON TABLE production_progress IS 'Progress tracking for work orders';
COMMENT ON TABLE vendor IS 'Supplier information';
COMMENT ON TABLE purchase_order IS 'Purchase orders for materials';
COMMENT ON TABLE purchase_order_line_item IS 'Items in purchase orders';
COMMENT ON TABLE goods_receipt IS 'Receiving goods from vendors';
COMMENT ON TABLE goods_receipt_line_item IS 'Individual items received';
COMMENT ON TABLE customer IS 'Customer information';
COMMENT ON TABLE sales_order IS 'Customer orders';
COMMENT ON TABLE sales_order_item IS 'Items in customer orders';
COMMENT ON TABLE invoice IS 'Customer billing';
COMMENT ON TABLE payment IS 'Payment records';
COMMENT ON TABLE product_pricing IS 'Pricing management for products';
COMMENT ON TABLE account IS 'Chart of accounts';
COMMENT ON TABLE transaction IS 'Individual financial transactions';
COMMENT ON TABLE journal_entry IS 'Double-entry journal entries';
COMMENT ON TABLE journal_entry_line IS 'Lines in journal entries';
COMMENT ON TABLE budget IS 'Budget planning';
COMMENT ON TABLE budget_line IS 'Budget line items';
COMMENT ON TABLE tax_rate IS 'Tax configuration';
COMMENT ON TABLE financial_period IS 'Accounting periods';

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO erp_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO erp_user;
