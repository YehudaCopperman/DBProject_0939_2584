{\rtf1\ansi\ansicpg1252\cocoartf2821
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;\red249\green249\blue249;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0\c87059;\cssrgb\c98039\c98039\c98039;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11220\viewh8100\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs28 \AppleTypeServices\AppleTypeServicesF65539 \cf2 \cb3 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 CREATE TABLE person\
(\
  pId INT NOT NULL,\
  DateOfB DATE NOT NULL,\
  firstName VARCHAR(20) NOT NULL,\
  lastName VARCHAR(20) NOT NULL,\
  email VARCHAR(20) NOT NULL,\
  address VARCHAR(20) NOT NULL,\
  phone NUMERIC(10,0) NOT NULL,\
  PRIMARY KEY (pId)\
);\
\
CREATE TABLE worker\
(\
  job VARCHAR(20) NOT NULL,\
  contract VARCHAR(500) NOT NULL,\
  dateOfEployment DATE NOT NULL,\
  pId INT NOT NULL,\
  PRIMARY KEY (pId),\
  FOREIGN KEY (pId) REFERENCES person(pId)\
);\
\
CREATE TABLE hourly\
(\
  salaryPH NUMERIC(6,2) NOT NULL,\
  bonus NUMERIC(10,2) NOT NULL,\
  overTimeRate VARCHAR(5,2) NOT NULL,\
  pId INT NOT NULL,\
  PRIMARY KEY (pId),\
  FOREIGN KEY (pId) REFERENCES worker(pId)\
);\
\
CREATE TABLE monthly\
(\
  vecationDays NUMERIC(3,1) NOT NULL,\
  salaryPM NUMERIC(9,2) NOT NULL,\
  benefits_package VARCHAR(500) NOT NULL,\
  pId INT NOT NULL,\
  PRIMARY KEY (pId),\
  FOREIGN KEY (pId) REFERENCES worker(pId)\
);\
\
CREATE TABLE freelance\
(\
  pId INT NOT NULL,\
  PRIMARY KEY (pId),\
  FOREIGN KEY (pId) REFERENCES person(pId)\
);\
\
CREATE TABLE timeSpan\
(\
  date DATE NOT NULL,\
  startTime VARCHAR(8) NOT NULL,\
  finishTime VARCHAR(8) NOT NULL,\
  PRIMARY KEY (date)\
);\
\
CREATE TABLE services\
(\
  serviceName VARCHAR(20) NOT NULL,\
  equipmentRequired VARCHAR(20) NOT NULL,\
  PRIMARY KEY (serviceName)\
);}