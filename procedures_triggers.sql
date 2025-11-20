SET NAMES utf8mb4 COLLATE utf8mb4_general_ci;
SET collation_connection = 'utf8mb4_general_ci';

DROP TRIGGER IF EXISTS after_trip_created;
DROP TRIGGER IF EXISTS after_trip_completed;
DROP PROCEDURE IF EXISTS AssignDriver;
DROP PROCEDURE IF EXISTS FormTripFromBookings;
DROP FUNCTION IF EXISTS GetTripRevenue;
DROP FUNCTION IF EXISTS GetTotalEarnings;
DROP FUNCTION IF EXISTS GetPassengerTotalSpent;
DROP VIEW IF EXISTS TopTrips;

-- 1) trigger to set TotalFare when Trip inserted (simple rate 10 per km)
DELIMITER $$
CREATE TRIGGER after_trip_created
BEFORE INSERT ON Trips
FOR EACH ROW
BEGIN
  SET NEW.TotalFare = ROUND(NEW.Distance * 10, 2);
  SET NEW.SeatsFilled = 0;
END$$
DELIMITER ;


-- 2) Procedure: AssignDriver (random active driver whose vehicle can hold required capacity) - updates a Trip to set driver and vehicle
DELIMITER $$
CREATE PROCEDURE AssignDriver(IN p_trip INT, IN p_capacity INT)
BEGIN
  DECLARE pick_driver INT;
  DECLARE pick_vehicle INT;

  -- Pick a random active driver whose vehicle can hold p_capacity passengers
  SELECT D.DriverID, V.VehicleID
  INTO pick_driver, pick_vehicle
  FROM Drivers D
  JOIN Vehicles V ON D.DriverID = V.DriverID
  WHERE D.IsActive = TRUE AND V.Capacity >= p_capacity
  ORDER BY RAND()
  LIMIT 1;

  UPDATE Trips
  SET DriverID = pick_driver,
      VehicleID = pick_vehicle,
      Status = 'Open'
  WHERE TripID = p_trip;
END$$
DELIMITER ;


-- 3) Procedure: FormTripFromBookings - creates a Trip from matching Bookings
DELIMITER $$

CREATE PROCEDURE FormTripFromBookings(
  IN p_source VARCHAR(150),
  IN p_destination VARCHAR(150),
  IN p_distance DECIMAL(6,2),
  IN p_capacity INT
)
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE b_id INT;

  DECLARE cur_bookings CURSOR FOR
    SELECT BookingID
    FROM Bookings
    WHERE
      Source COLLATE utf8mb4_general_ci = p_source COLLATE utf8mb4_general_ci
      AND Destination COLLATE utf8mb4_general_ci = p_destination COLLATE utf8mb4_general_ci
      AND Status = 'Requested'
    ORDER BY RequestedAt
    LIMIT p_capacity;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  -- Create new trip
  INSERT INTO Trips (Source, Destination, Distance, Capacity)
  VALUES (p_source, p_destination, p_distance, p_capacity);
  SET @new_trip_id = LAST_INSERT_ID();

  -- Assign driver and vehicle
  CALL AssignDriver(@new_trip_id, p_capacity);

  -- Attach bookings
  OPEN cur_bookings;
  read_loop: LOOP
    FETCH cur_bookings INTO b_id;
    IF done = 1 THEN LEAVE read_loop; END IF;

    UPDATE Bookings
      SET TripID = @new_trip_id,
          Status = 'Confirmed'
      WHERE BookingID = b_id;

    UPDATE Trips
      SET SeatsFilled = SeatsFilled + 1
      WHERE TripID = @new_trip_id;
  END LOOP;
  CLOSE cur_bookings;

  -- Compute payment shares
  SELECT SeatsFilled INTO @count FROM Trips WHERE TripID = @new_trip_id;
  IF @count > 0 THEN
    SELECT TotalFare INTO @tf FROM Trips WHERE TripID = @new_trip_id;
    SET @share = ROUND(@tf / @count, 2);

    INSERT INTO Payments (BookingID, Amount, PaymentMethod, Status)
    SELECT BookingID, @share, 'Cash', 'Pending'
    FROM Bookings WHERE TripID = @new_trip_id;
  END IF;
END$$

DELIMITER ;


-- 4) trigger to update Payments when Trip is completed
DELIMITER $$
CREATE TRIGGER after_trip_completed
AFTER UPDATE ON Trips
FOR EACH ROW
BEGIN
  IF NEW.Status = 'Completed' THEN
    UPDATE Payments P
    JOIN Bookings B ON P.BookingID = B.BookingID
    SET P.Status = 'Success'
    WHERE B.TripID = NEW.TripID;
  END IF;
END$$
DELIMITER ;


-- 5) View: TopTrips - top 5 trips by seats filled
CREATE VIEW TopTrips AS
SELECT TripID, Source, Destination, SeatsFilled, TotalFare
FROM Trips
ORDER BY SeatsFilled DESC
LIMIT 5;


-- 6) Functions to get earnings/spent
DELIMITER $$
CREATE FUNCTION GetPassengerTotalSpent(p_user INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE total DECIMAL(10,2);
  SELECT IFNULL(SUM(P.Amount), 0)
  INTO total
  FROM Payments P
  JOIN Bookings B ON P.BookingID = B.BookingID
  JOIN Trips T ON B.TripID = T.TripID
  WHERE B.UserID = p_user
    AND P.Status = 'Success'
    AND T.Status = 'Completed';
  RETURN total;
END$$
DELIMITER ;


-- 7) Function to get driver's total earnings
DELIMITER $$
CREATE FUNCTION GetTotalEarnings(p_driver INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE earnings DECIMAL(10,2);
  SELECT IFNULL(SUM(T.TotalFare), 0)
  INTO earnings
  FROM Trips T
  WHERE T.DriverID = p_driver
    AND T.Status = 'Completed';
  RETURN earnings;
END$$
DELIMITER ;


-- 8) Function to get trip revenue
DELIMITER $$
CREATE FUNCTION GetTripRevenue(p_trip INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE revenue DECIMAL(10,2);
  SELECT IFNULL(SUM(Amount), 0)
  INTO revenue
  FROM Payments
  WHERE BookingID IN (
    SELECT BookingID FROM Bookings WHERE TripID = p_trip
  )
  AND Status = 'Success';
  RETURN revenue;
END$$
DELIMITER ;
