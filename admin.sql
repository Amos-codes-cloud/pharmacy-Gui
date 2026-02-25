USE pharmacy;

INSERT INTO users (username, password, role)
VALUES
  ('admin', 'admin123', 'manager'),
  ('staff1', '1234', 'staff')
ON DUPLICATE KEY UPDATE
  password = VALUES(password),
  role = VALUES(role);