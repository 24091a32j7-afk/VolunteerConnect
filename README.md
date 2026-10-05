# VolunteerConnect – Volunteer Matching and Scheduling Platform

## Problem Statement

Organizations often find it difficult to identify suitable volunteers
based on their skills and availability. Volunteers also face difficulty
finding suitable volunteering opportunities.

## Solution

VolunteerConnect is a web-based platform that connects volunteers with
organizations. Organizations can create volunteering opportunities,
find suitable volunteers using skill-based matching, schedule volunteers,
and manage attendance.

## Features

- Volunteer Registration
- Organization Registration
- Role-Based Login
- Volunteer Dashboard
- Organization Dashboard
- Create Opportunities
- Smart Skill Matching
- Volunteer Scheduling
- Attendance Management
- Completed Events
- SQLite Database
- Password Hashing

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- Werkzeug

## Smart Matching

The system compares the required skills of an opportunity with the
skills of registered volunteers.

The matching percentage is calculated based on the number of matching
skills.

## Database

The application uses SQLite to store:

- Users
- Volunteers
- Organizations
- Opportunities
- Schedules
- Attendance

## How to Run

1. Install Python.
2. Install the required packages:

   pip install -r requirements.txt

3. Run the application:

   python app.py

4. Open the application in a browser:

   http://127.0.0.1:5000

## Project Flow

Organization
→ Create Opportunity
→ Enter Required Skills
→ Smart Matching
→ Select Volunteer
→ Schedule Volunteer
→ Mark Attendance
→ Completed Event

## AI Disclosure

AI was used during development for code assistance and debugging.

Percentage of AI used: 45%