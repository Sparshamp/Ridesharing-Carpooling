-- schema.sql
DROP DATABASE IF EXISTS ride_sharing;
CREATE DATABASE ride_sharing CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE ride_sharing;

-- Users: single table for all accounts (admin/driver/passenger)
CREATE TABLE Users (
  UserID INT AUTO_INCREMENT PRIMARY KEY,
  Name VARCHAR(100) NOT NULL,
  Email VARCHAR(150) NOT NULL UNIQUE,
  Phone VARCHAR(15) NOT NULL UNIQUE,
  PasswordHash VARCHAR(255) NOT NULL,
  Role ENUM('admin','driver','passenger') NOT NULL DEFAULT 'passenger',
  CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Drivers: driver-specific info, linked to Users.UserID
CREATE TABLE Drivers (
  DriverID INT AUTO_INCREMENT PRIMARY KEY,
  UserID INT NOT NULL UNIQUE,
  LicenseNo VARCHAR(50) NOT NULL UNIQUE,
  ExperienceYears INT DEFAULT 0 CHECK (ExperienceYears >= 0),
  IsActive BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Vehicles: belongs to a driver (DriverID)
CREATE TABLE Vehicles (
  VehicleID INT AUTO_INCREMENT PRIMARY KEY,
  DriverID INT NOT NULL,
  PlateNo VARCHAR(20) NOT NULL UNIQUE,
  Model VARCHAR(80),
  Capacity INT NOT NULL CHECK (Capacity > 0),
  FOREIGN KEY (DriverID) REFERENCES Drivers(DriverID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Bookings: passenger requests a ride (later this will be attached to trips)
CREATE TABLE Bookings (
  BookingID INT AUTO_INCREMENT PRIMARY KEY,
  UserID INT NOT NULL,
  Source VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  Destination VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT          NULL,
  Distance DECIMAL(6,2) NOT NULL CHECK (Distance > 0),
  TripID INT DEFAULT NULL, -- set when booking is confirmed into a Trip
  Status ENUM('Requested','Confirmed','Cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'Requested',
  RequestedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Trips: actual carpool trips created by grouping Bookings; driver assigned here
CREATE TABLE Trips (
  TripID INT AUTO_INCREMENT PRIMARY KEY,
  DriverID INT NULL,
  VehicleID INT NULL,
  Source VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  Destination VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
  NOT NULL,
  Distance DECIMAL(6,2) NOT NULL CHECK (Distance > 0),
  TotalFare DECIMAL(10,2) DEFAULT 0,
  Capacity INT NOT NULL, -- total seats available (including driver seat not counted)
  SeatsFilled INT DEFAULT 0, -- number of confirmed passengers
  Status ENUM('Open','Ongoing','Completed','Cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'Open',
  CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (DriverID) REFERENCES Drivers(DriverID) ON DELETE SET NULL ON UPDATE CASCADE,
  FOREIGN KEY (VehicleID) REFERENCES Vehicles(VehicleID) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Payments: one record per Booking (passenger pays their share)
CREATE TABLE Payments (
  PaymentID INT AUTO_INCREMENT PRIMARY KEY,
  BookingID INT NOT NULL,
  Amount DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
  PaymentMethod ENUM('Cash','UPI','Card') DEFAULT 'Cash',
  PaymentDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  Status ENUM('Pending','Success','Failed') DEFAULT 'Pending',
  FOREIGN KEY (BookingID) REFERENCES Bookings(BookingID) ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE KEY ux_booking_payment (BookingID)
);

