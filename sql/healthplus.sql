-- Connect to the healthplus database
\c healthplus_db;

-- Total patients
SELECT COUNT(*) AS total_patients
FROM patients;

-- Patients by city
SELECT city, COUNT(*) AS patient_count
FROM healthplus.patients
GROUP BY city
ORDER BY patient_count DESC;

-- Average age
SELECT AVG(age) AS average_age
FROM healthplus.patients;

-- Doctors by specialty
SELECT specialty, COUNT(*) AS doctor_count
FROM healthplus.doctors
GROUP BY specialty
ORDER BY doctor_count DESC;

-- Doctors by branch
SELECT branch, COUNT(*) AS doctor_count
FROM healthplus.doctors
GROUP BY branch
ORDER BY doctor_count DESC;

-- Total appointments
SELECT COUNT(*) AS total_appointments
FROM healthplus.appointments;

-- Appointment status
SELECT appointment_status, COUNT(*) AS appointment_count
FROM healthplus.appointments
GROUP BY appointment_status
ORDER BY appointment_count DESC;

-- Most common reason for visit
SELECT reason_for_visit, COUNT(*) AS visit_count
FROM healthplus.appointments
WHERE reason_for_visit != 'Unknown'
GROUP BY reason_for_visit
ORDER BY visit_count DESC
LIMIT 1;

-- Revenue collected
SELECT SUM(amount_paid) AS total_revenue
FROM healthplus.billing;

-- Revenue by payment method
SELECT payment_method, SUM(amount_charged) AS revenue
FROM healthplus.billing
GROUP BY payment_method
ORDER BY revenue DESC;