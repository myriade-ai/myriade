CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL
);
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- Clients Table
INSERT INTO clients (name, email, phone, address) VALUES 
('John Doe', 'john.doe@example.com', '123-456-7890', '123 Elm Street, Springfield'),
('Jane Smith', 'jane.smith@example.com', '098-765-4321', '456 Oak Avenue, Rivertown'),
('Alice Johnson', 'alice.johnson@example.com', '555-444-3333', '789 Maple Lane, Hilltop'),
('Bob Brown', 'bob.brown@example.com', '222-333-4444', '101 Pine Road, Greenfield'),
('Charlie Green', 'charlie.green@example.com', '666-777-8888', '202 Birch Blvd, Lakeside'),
('Debbie White', 'debbie.white@example.com', '999-000-1111', '303 Cedar St, Cloudcity');

-- Products Table
INSERT INTO products (name, price) VALUES 
('Laptop', 1200.00),
('Smartphone', 800.00),
('Headphones', 150.00),
('Keyboard', 50.00),
('Mouse', 30.00),
('Monitor', 250.00);

-- Orders Table
-- Assuming clients and products have IDs that start at 1 and increase sequentially.
INSERT INTO orders (client_id, product_id, quantity) VALUES 
(1, 1, 1), -- John Doe bought 1 Laptop
(1, 2, 1), -- John Doe bought 1 Smartphone
(2, 3, 2), -- Jane Smith bought 2 Headphones
(3, 4, 1), -- Alice Johnson bought 1 Keyboard
(4, 5, 1), -- Bob Brown bought 1 Mouse
(5, 6, 2), -- Charlie Green bought 2 Monitors
(6, 1, 1); -- Debbie White bought 1 Laptop