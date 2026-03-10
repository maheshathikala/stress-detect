"""
tests/test_auth.py
Example security test file for authentication endpoints
"""

import pytest
import json
from flask import session

@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()

@pytest.fixture
def auth_headers():
    """Standard auth headers"""
    return {'Content-Type': 'application/json'}


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self, client, auth_headers):
        """Test successful login"""
        response = client.post('/login',
            data=json.dumps({
                'username': 'admin',
                'password': 'testpassword'
            }),
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json['success'] is True
    
    def test_login_invalid_credentials(self, client, auth_headers):
        """Test login with wrong password"""
        response = client.post('/login',
            data=json.dumps({
                'username': 'admin',
                'password': 'wrongpassword'
            }),
            headers=auth_headers
        )
        assert response.status_code == 401
        assert response.json['success'] is False
    
    def test_login_missing_fields(self, client, auth_headers):
        """Test login without username/password"""
        response = client.post('/login',
            data=json.dumps({'username': 'admin'}),
            headers=auth_headers
        )
        assert response.status_code == 401
    
    def test_register_success(self, client, auth_headers):
        """Test successful registration"""
        response = client.post('/register',
            data=json.dumps({
                'username': 'newuser',
                'password': 'Password123!',
                'email': 'user@example.com'
            }),
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json['success'] is True
    
    def test_register_weak_password(self, client, auth_headers):
        """Test registration with weak password"""
        response = client.post('/register',
            data=json.dumps({
                'username': 'newuser',
                'password': 'weak',  # Too short
                'email': 'user@example.com'
            }),
            headers=auth_headers
        )
        assert response.status_code == 400
        assert 'password' in response.json['message'].lower()
    
    def test_register_invalid_username(self, client, auth_headers):
        """Test registration with invalid username"""
        response = client.post('/register',
            data=json.dumps({
                'username': 'ab',  # Too short
                'password': 'Password123!',
                'email': 'user@example.com'
            }),
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_register_duplicate_username(self, client, auth_headers):
        """Test registration with existing username"""
        # First registration
        client.post('/register',
            data=json.dumps({
                'username': 'existinguser',
                'password': 'Password123!',
                'email': 'user@example.com'
            }),
            headers=auth_headers
        )
        
        # Try registering with same username
        response = client.post('/register',
            data=json.dumps({
                'username': 'existinguser',
                'password': 'Password456!',
                'email': 'other@example.com'
            }),
            headers=auth_headers
        )
        assert response.status_code == 400
        assert 'already exists' in response.json['message'].lower()


class TestSecurityHeaders:
    """Test security headers are present"""
    
    def test_security_headers(self, client):
        """Verify security headers on all responses"""
        response = client.get('/')
        
        # Check for security headers
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        
        if response.is_secure:  # Only in production
            assert 'Strict-Transport-Security' in response.headers


class TestRateLimiting:
    """Test rate limiting is working"""
    
    def test_login_rate_limit(self, client, auth_headers):
        """Test login rate limiting"""
        # Try logging in multiple times (limit is 10/hour)
        responses = []
        for i in range(15):
            response = client.post('/login',
                data=json.dumps({
                    'username': f'user{i}',
                    'password': 'pass'
                }),
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # After limit, should get 429 (Too Many Requests)
        assert 429 in responses

    def test_register_rate_limit(self, client, auth_headers):
        """Test registration rate limiting"""
        responses = []
        for i in range(8):  # Limit is 5/hour
            response = client.post('/register',
                data=json.dumps({
                    'username': f'user{i}',
                    'password': 'Password123!',
                    'email': f'user{i}@test.com'
                }),
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # Should hit rate limit
        assert 429 in responses


class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_csrf_token_required(self, client):
        """Test that CSRF token is checked"""
        # POST without CSRF token should fail
        response = client.post('/api/users',
            json={'username': 'test'},
            headers={'X-CSRFToken': ''}  # Invalid token
        )
        # Should either fail or require valid token
        assert response.status_code in [400, 401, 403]


class TestInputValidation:
    """Test input validation"""
    
    def test_sql_injection_attempt(self, client, auth_headers):
        """Test SQL injection prevention"""
        response = client.post('/login',
            data=json.dumps({
                'username': "'; DROP TABLE users; --",
                'password': 'anything'
            }),
            headers=auth_headers
        )
        # Should not cause error - handled gracefully
        assert response.status_code in [401, 400]
    
    def test_xss_attempt_in_username(self, client, auth_headers):
        """Test XSS prevention"""
        response = client.post('/register',
            data=json.dumps({
                'username': '<script>alert("xss")</script>',
                'password': 'Password123!',
                'email': 'test@test.com'
            }),
            headers=auth_headers
        )
        # Invalid username format
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
