# Student Mental Stress Detection System

A comprehensive web application that uses AI-powered facial analysis to detect and monitor student stress levels through laptop camera input.

## Features

### 🔐 Authentication System
- User registration and login
- Admin panel with secret code access (ADMIN2024)
- Role-based access control
- Secure password hashing

### 🧠 Stress Detection
- Real-time facial analysis using computer vision
- Machine learning-based stress level calculation
- Percentage-based stress scoring (0-100%)
- Instant feedback and recommendations

### 📊 Analytics & Monitoring
- Personal stress history tracking
- Admin dashboard for user management
- System-wide analytics and logs
- Trend analysis and reports

### 🎨 User Interface
- Modern, responsive design
- Real-time camera preview
- Interactive charts and visualizations
- Mobile-friendly interface

## Technology Stack

### Frontend
- **HTML5, CSS3, JavaScript**: Core web technologies
- **Responsive Design**: Mobile-first approach
- **Real-time Camera**: WebRTC API integration
- **Interactive UI**: Modern CSS animations and transitions

### Backend
- **Flask**: Python web framework
- **MongoDB**: NoSQL database
- **OpenCV**: Computer vision library
- **TensorFlow**: Machine learning framework

### Machine Learning
- **Facial Detection**: Haar Cascade classifiers
- **Stress Analysis**: Multi-feature facial analysis
  - Eye region analysis (fatigue detection)
  - Forehead tension assessment
  - Mouth region tension analysis
  - Color deviation analysis

## Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Web camera
- Modern web browser

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd student-stress-detection
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start MongoDB**
   ```bash
   # On Windows
   net start MongoDB
   
   # On macOS/Linux
   sudo systemctl start mongod
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`

## Usage Guide

### For Students

1. **Registration**
   - Visit the registration page
   - Enter username, email, and password
   - Leave admin code blank for regular user access

2. **Stress Detection**
   - Login to your account
   - Navigate to "Start Detection"
   - Allow camera permissions
   - Position your face in the guide
   - Click "Analyze Stress" for instant results

3. **View History**
   - Access your dashboard to view stress history
   - Track trends over time
   - Get personalized recommendations

### For Administrators

1. **Admin Registration**
   - Use secret code: `ADMIN2024` during registration
   - Access admin panel after login

2. **User Management**
   - View all registered users
   - Delete user accounts (except admins)
   - Monitor system statistics

3. **System Monitoring**
   - View all stress detection logs
   - Analyze system-wide usage patterns
   - Monitor user activity

## Stress Detection Algorithm

The system analyzes multiple facial features to determine stress levels:

### Analysis Components
1. **Eye Region Analysis**
   - Detects dark circles and eye openness
   - Measures brightness levels
   - Correlates with fatigue and stress

2. **Forehead Analysis**
   - Detects tension lines and wrinkles
   - Analyzes texture variance
   - Indicates mental strain

3. **Mouth Region Analysis**
   - Detects jaw tension
   - Analyzes edge detection patterns
   - Correlates with stress responses

4. **Color Analysis**
   - Measures skin color deviation
   - Detects paleness or flushing
   - Indicates physiological stress responses

### Stress Level Categories
- **0-30%**: Low Stress (Green) - Relaxed state
- **31-50%**: Mild Stress (Yellow) - Minor tension
- **51-70%**: Moderate Stress (Orange) - Noticeable stress
- **71-100%**: High Stress (Red) - Significant stress

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Stress Detection
- `POST /api/detect-stress` - Analyze stress from camera image
- `GET /api/stress-logs` - Retrieve user stress history

### Admin Functions
- `GET /api/users` - List all users (admin only)
- `DELETE /api/users/<id>` - Delete user (admin only)

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  username: String,
  email: String,
  password: String (hashed),
  role: String ('user' | 'admin'),
  created_at: Date
}
```

### Stress Logs Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  username: String,
  stress_level: Number (0-100),
  timestamp: Date
}
```

## Security Features

- Password hashing with Werkzeug
- Session management
- Role-based access control
- Input validation and sanitization
- CORS protection
- Secure admin access with secret codes

## Project Structure

```
student-stress-detection/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # HTML templates
│   ├── login.html       # Login/registration page
│   ├── dashboard.html   # User dashboard
│   ├── admin.html       # Admin panel
│   └── stress-detection.html # Detection interface
└── static/              # Static assets
    ├── css/
    │   └── style.css    # Main stylesheet
    └── js/
        ├── auth.js      # Authentication logic
        ├── dashboard.js # Dashboard functionality
        ├── admin.js     # Admin panel logic
        └── stress-detection.js # Detection interface
```

## Browser Compatibility

- Chrome 60+ (Recommended)
- Firefox 55+
- Safari 11+
- Edge 79+

## Performance Considerations

- Optimized image processing
- Efficient database queries
- Responsive design for all devices
- Minimal resource usage
- Real-time processing capabilities

## Troubleshooting

### Common Issues

1. **Camera not working**
   - Ensure browser permissions are granted
   - Check if camera is being used by other applications
   - Try refreshing the page

2. **MongoDB connection errors**
   - Verify MongoDB is running
   - Check connection string in app.py
   - Ensure database permissions

3. **Analysis errors**
   - Ensure good lighting conditions
   - Position face clearly in camera view
   - Check internet connection

### Support

For technical support or questions:
- Check the troubleshooting section
- Review browser console for errors
- Ensure all dependencies are properly installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

- Enhanced ML model accuracy
- Real-time stress monitoring
- Integration with wearable devices
- Advanced analytics dashboard
- Mobile app development
- Multi-language support

## Acknowledgments

- OpenCV community for computer vision tools
- TensorFlow team for machine learning framework
- Flask community for web framework
- MongoDB for database solutions