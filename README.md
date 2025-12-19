# 🎾 Tennis Court Booking System

> A comprehensive web application for booking tennis courts, built with Django.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [Team](#-team)
- [License](#-license)

## 🌟 Overview

Tennis Court Booking System is a full-featured web application that allows users to browse, book, and manage tennis court reservations. The system supports both regular users and administrators with different access levels and functionalities.

## ✨ Features

### 👤 User Features
- **User Authentication**: Register, login, and logout functionality
- **Browse Courts**: View all available tennis courts with details
- **Book Courts**: Select available time slots and book courts
- **Manage Bookings**: View, edit, and cancel personal bookings
- **Wallet System**: Top-up balance and make payments
- **Transaction History**: Track all deposits and payments
- **Review & Rating**: Rate and review tennis courts
- **Report Issues**: Report court damages or maintenance needs
- **Profile Management**: Update personal information and profile photo
- **Password Reset**: Request password reset through admin approval

### 👨‍💼 Admin Features
- **Court Management**: Add, edit, and delete tennis courts
- **View All Bookings**: Monitor all user bookings
- **User Management**: View and manage all registered users
- **Report Management**: Handle court damage reports, mark courts as repairing/available
- **Revenue Dashboard**: Track all payments and system revenue
- **Password Reset Approval**: Approve user password reset requests
- **PDF Report Generation**: Download reports in PDF format

### 🔔 System Features
- **Dynamic Toast Notifications**: Beautiful animated notifications for all actions
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Availability**: Court availability updates in real-time
- **Automatic Time Slot Generation**: Generate play time slots based on court hours

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| **Django 5.0** | Backend Framework |
| **SQLite** | Database |
| **Bootstrap 5** | Frontend Framework |
| **Font Awesome** | Icons |
| **ReportLab** | PDF Generation |
| **Owl Carousel** | Image Carousels |
| **jQuery** | JavaScript Library |

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Tennis-Court.git
   cd Tennis-Court
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open browser and go to: `http://127.0.0.1:8000/home/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## 📖 Usage

### For Users
1. Register a new account or login
2. Browse available tennis courts
3. Select a court and choose available time slot
4. Top-up your wallet balance
5. Complete the booking payment
6. Manage your bookings from "My Bookings"

### For Admins
1. Login with admin credentials
2. Add new tennis courts from "Add Tennis Court"
3. Monitor all bookings from "All The Bookings"
4. Handle reports from "All The Reports"
5. View revenue from "Report All Payments"

## 📁 Project Structure

```
Tennis-Court/
├── home/                       # Main application
│   ├── migrations/             # Database migrations
│   ├── static/app/             # Static files (CSS, JS, images)
│   ├── templates/apps/         # HTML templates
│   ├── templatetags/           # Custom template filters
│   ├── admin.py                # Admin configurations
│   ├── forms.py                # Django forms
│   ├── models.py               # Database models
│   ├── urls.py                 # URL routing
│   └── views.py                # View functions
├── tennis/                     # Project settings
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL configuration
│   └── wsgi.py                 # WSGI configuration
├── media/                      # Uploaded files
├── staticfiles/                # Collected static files
├── db.sqlite3                  # SQLite database
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/home/` | GET | Home page |
| `/property_list/` | GET | List all tennis courts |
| `/detail/?id=<court_id>` | GET | Court details |
| `/rent_court/<court_id>/` | POST | Book a court |
| `/checkout/` | GET/POST | Payment checkout |
| `/booking/` | GET | User's bookings |
| `/profile/` | GET | User profile |
| `/top_up/` | GET/POST | Top-up wallet |
| `/login_register_user/` | GET/POST | User authentication |
| `/login_register_admin/` | GET/POST | Admin authentication |

### Admin Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/add_tennis/` | GET/POST | Add new court |
| `/reports/` | GET/POST | Manage reports |
| `/bookings/` | GET | All user bookings |
| `/manage/` | GET/POST | Manage users |
| `/report_all_payments/` | GET | Revenue dashboard |

## 📸 Screenshots

### Home Page
The landing page showcasing featured tennis courts and booking options.

### Court Listing
Browse all available courts with filtering options.

### Booking Flow
Easy 3-step booking process: Select → Confirm → Pay

### Admin Dashboard
Comprehensive admin panel for managing the system.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 👥 Team

**Group 1 - Superman**

| Name | Role | Contact |
|------|------|---------|
| Nguyễn Quốc Phú | Lead Developer | [Facebook](https://web.facebook.com/Phu22122004/) |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **Email**: guofu2004@gmail.com
- **Phone**: (+84) 966 572 874
- **Address**: 298 đường Cầu Diễn - Minh Khai - Bắc Từ Liêm - Hà Nội

---

<p align="center">Made with ❤️ by Group 1 - Superman</p>