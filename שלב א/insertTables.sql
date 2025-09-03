-- person table (3 inserts)
INSERT INTO person(pId, DateOfB, firstName, lastName, email, address, phone)
VALUES 
(1, '1990-01-15', 'John',    'Smith',   'john.s@example.com',  '123MainSt', 1234567890),
(2, '1985-06-10', 'Sarah',   'Johnson', 'sarah.j@example.com', '456OakAve', 9876543210),
(3, '1992-03-27', 'Michael', 'Brown',   'mike.b@example.com',  '789PineRd', 5551234567);

-- worker table (3 inserts; referencing person pId=1,2,3)
INSERT INTO worker(job, contract, dateOfEployment, pId)
VALUES 
('Cashier',   'c:\some_path\some_contract.pdf', '2020-01-01', 1),
('Manager',   'c:\some_path\some_contract1.pdf',  '2019-05-10', 2),
('Developer', 'c:\some_path\some_contract3.pdf',      '2021-03-15', 3);

-- hourly table (3 inserts; referencing same pIds=1,2,3 in worker)
INSERT INTO hourly(salaryPH, bonus, overTimeRate, pId)
VALUES
(15.50,  500.00, '1.5', 1),
(20.00, 1000.00, '2.0', 2),
(30.00, 1500.00, '1.75',3);

-- monthly table (3 inserts; also referencing pIds=1,2,3 in worker)
INSERT INTO monthly(vecationDays, salaryPM, benefits_package, pId)
VALUES
(14.0, 3500.00, 'Health, Dental', 1),
(20.0, 5000.00, 'Health, Gym',    2),
(10.0, 4000.00, 'Basic Health',   3);

-- freelance table (3 inserts; referencing person pId=1,2,3)
INSERT INTO freelance(pId)
VALUES 
(1),
(2),
(3);

-- timeSpan table (3 inserts)
INSERT INTO timeSpan(date, startTime, finishTime)
VALUES 
('2023-01-01', '08:00:00', '16:00:00'),
('2023-01-02', '09:00:00', '17:30:00'),
('2023-01-03', '10:00:00', '18:15:00');

-- services table (3 inserts)
INSERT INTO services(serviceName, equipmentRequired)
VALUES
('Cleaning',   'CleaningKit'),
('Catering',   'Kitchenware'),
('IT Support', 'Laptop');

INSERT INTO serves(servicedateB, serviceDateE, contract, price, serviceName, pId)
VALUES
('2024-01-01', '2024-01-10', 'Basic',    1000, 'Cleaning',   1),
('2024-02-01', '2024-02-28', 'Contract1',2000, 'Catering',   2),
('2024-03-05', '2024-03-15', 'Urgent',   1500, 'IT Support', 3);


INSERT INTO shift(pId, date)
VALUES
(1, '2023-01-01'),
(2, '2023-01-02'),
(3, '2023-01-03');