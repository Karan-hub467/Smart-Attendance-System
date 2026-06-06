# Smart Attendance System

## Overview

Smart Attendance System is an AI-powered attendance management application that uses facial recognition technology to automatically identify individuals and mark attendance in real time. The system eliminates manual attendance processes, improves accuracy, and stores attendance records securely.

## Features

* Face detection using OpenCV
* Face recognition and identification
* Real-time attendance marking
* Student record management
* Attendance history tracking
* MySQL database integration
* User-friendly interface

## Technologies Used

* Python
* OpenCV
* MySQL

## Installation

### Prerequisites

* Python 3.10+
* MySQL Server
* pip

### Setup Steps

#### Clone Repository

```bash
git clone <repository-url>
cd Smart-Attendance-System
```

#### Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Database

Create a MySQL database:

```sql
CREATE DATABASE attendance_system;
```

Update database credentials inside the project configuration file.

#### Run Application

```bash
python main.py
```

## Project Structure

```text
Smart-Attendance-System/
│
├── dataset/
├── trainer/
├── attendance/
├── images/
├── database/
├── main.py
├── requirements.txt
└── README.md
```

## Usage

1. Register a user's face.
2. Train the recognition model.
3. Start the attendance system.
4. Recognized users will be marked present automatically.
5. Attendance records are stored in the database.

## Future Enhancements

* Web dashboard
* Cloud database integration
* Attendance reports export
* Mobile application support

