CREATE TABLE person
(
  pId INT NOT NULL,
  DateOfB DATE NOT NULL,
  firstName VARCHAR(20) NOT NULL,
  lastName VARCHAR(20) NOT NULL,
  email VARCHAR(20) NOT NULL,
  address VARCHAR(20) NOT NULL,
  phone NUMERIC(10,0) NOT NULL,
  PRIMARY KEY (pId)
);

CREATE TABLE worker
(
  job VARCHAR(20) NOT NULL,
  contract VARCHAR(500) NOT NULL,
  dateOfEployment DATE NOT NULL,
  pId INT NOT NULL,
  PRIMARY KEY (pId),
  FOREIGN KEY (pId) REFERENCES person(pId)
);

CREATE TABLE hourly
(
  salaryPH NUMERIC(6,2) NOT NULL,
  bonus NUMERIC(10,2) NOT NULL,
  overTimeRate NUMERIC(5,2) NOT NULL,
  pId INT NOT NULL,
  PRIMARY KEY (pId),
  FOREIGN KEY (pId) REFERENCES worker(pId)
);

CREATE TABLE monthly
(
  vacationdays NUMERIC(3,1) NOT NULL,
  salaryPM NUMERIC(9,2) NOT NULL,
  benefits_package VARCHAR(500) NOT NULL,
  pId INT NOT NULL,
  PRIMARY KEY (pId),
  FOREIGN KEY (pId) REFERENCES worker(pId)
);

CREATE TABLE freelance
(
  pId INT NOT NULL,
  PRIMARY KEY (pId),
  FOREIGN KEY (pId) REFERENCES person(pId)
);



CREATE TABLE services
(
  serviceName VARCHAR(20) NOT NULL,
  equipmentRequired VARCHAR(20) NOT NULL,
  PRIMARY KEY (serviceName)
);

CREATE TABLE serves
(
  servicedateB DATE NOT NULL,
  serviceDateE DATE NOT NULL,
  contract VARCHAR(20) NOT NULL,
  price INT NOT NULL,
  serviceName VARCHAR(20) NOT NULL,
  pId INT NOT NULL,
  PRIMARY KEY (serviceName, pId),
  FOREIGN KEY (serviceName) REFERENCES services(serviceName),
  FOREIGN KEY (pId) REFERENCES freelance(pId)
);

CREATE TABLE shift
(
  pId INT NOT NULL,
  date DATE NOT NULL,
  PRIMARY KEY (pId, date),
  FOREIGN KEY (pId) REFERENCES hourly(pId),


  clock_in TIME NOT NULL,
  clock_out TIME NOT NULL
  );


  
