import requests
import sys
import json
from datetime import datetime

class CodeTrackrAPITester:
    def __init__(self, base_url="https://code-trackr.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details if not success else "")
            
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        username = f"testuser_{timestamp}"
        password = "TestPass123!"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.username = username
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        if not hasattr(self, 'username'):
            self.log_test("User Login", False, "No username available from registration")
            return False
            
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"username": self.username, "password": "TestPass123!"}
        )
        
        if success and 'access_token' in response:
            # Update token from login
            self.token = response['access_token']
            return True
        return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, _ = self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={"username": "nonexistent", "password": "wrongpass"}
        )
        return success

    def test_duplicate_registration(self):
        """Test duplicate user registration"""
        if not hasattr(self, 'username'):
            self.log_test("Duplicate Registration", False, "No username available")
            return False
            
        success, _ = self.run_test(
            "Duplicate Registration",
            "POST",
            "auth/register",
            400,
            data={"username": self.username, "password": "TestPass123!"}
        )
        return success

    def test_protected_route_without_token(self):
        """Test accessing protected route without token"""
        # Temporarily remove token
        temp_token = self.token
        self.token = None
        
        success, _ = self.run_test(
            "Protected Route Without Token",
            "GET",
            "problems",
            401
        )
        
        # Restore token
        self.token = temp_token
        return success

    def test_get_empty_problems(self):
        """Test getting problems when none exist"""
        success, response = self.run_test(
            "Get Empty Problems List",
            "GET",
            "problems",
            200
        )
        
        if success and isinstance(response, list) and len(response) == 0:
            return True
        return False

    def test_get_empty_stats(self):
        """Test getting stats when no problems exist"""
        success, response = self.run_test(
            "Get Empty Stats",
            "GET",
            "stats",
            200
        )
        
        if success and response.get('total_solved') == 0:
            return True
        return False

    def test_create_problem(self):
        """Test creating a new problem"""
        problem_data = {
            "title": "Test Problem",
            "platform": "LeetCode",
            "difficulty": "Easy",
            "topics": ["Arrays", "Hash Table"],
            "date_completed": "2024-01-15"
        }
        
        success, response = self.run_test(
            "Create Problem",
            "POST",
            "problems",
            200,
            data=problem_data
        )
        
        if success and response.get('title') == "Test Problem":
            self.problem_id = response.get('id')
            return True
        return False

    def test_get_problems_after_creation(self):
        """Test getting problems after creating one"""
        success, response = self.run_test(
            "Get Problems After Creation",
            "GET",
            "problems",
            200
        )
        
        if success and isinstance(response, list) and len(response) == 1:
            return True
        return False

    def test_get_stats_after_creation(self):
        """Test getting stats after creating a problem"""
        success, response = self.run_test(
            "Get Stats After Creation",
            "GET",
            "stats",
            200
        )
        
        if success and response.get('total_solved') == 1:
            return True
        return False

    def test_seed_data(self):
        """Test seeding sample data"""
        success, response = self.run_test(
            "Seed Sample Data",
            "POST",
            "seed-data",
            200
        )
        
        if success and "Seeded" in response.get('message', ''):
            return True
        return False

    def test_get_problems_after_seeding(self):
        """Test getting problems after seeding"""
        success, response = self.run_test(
            "Get Problems After Seeding",
            "GET",
            "problems",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 1:
            return True
        return False

    def test_get_stats_after_seeding(self):
        """Test getting stats after seeding"""
        success, response = self.run_test(
            "Get Stats After Seeding",
            "GET",
            "stats",
            200
        )
        
        if success and response.get('total_solved', 0) > 1:
            return True
        return False

    def test_invalid_problem_creation(self):
        """Test creating problem with invalid data"""
        invalid_data = {
            "title": "",  # Empty title
            "platform": "LeetCode",
            "difficulty": "Easy",
            "topics": [],  # Empty topics
            "date_completed": "2024-01-15"
        }
        
        success, _ = self.run_test(
            "Invalid Problem Creation",
            "POST",
            "problems",
            422,  # Validation error
            data=invalid_data
        )
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting CodeTrackr API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)

        # Authentication tests
        if not self.test_user_registration():
            print("❌ Registration failed, stopping tests")
            return self.get_results()

        self.test_user_login()
        self.test_invalid_login()
        self.test_duplicate_registration()
        self.test_protected_route_without_token()

        # Problem management tests
        self.test_get_empty_problems()
        self.test_get_empty_stats()
        self.test_create_problem()
        self.test_get_problems_after_creation()
        self.test_get_stats_after_creation()
        self.test_invalid_problem_creation()

        # Seed data tests
        self.test_seed_data()
        self.test_get_problems_after_seeding()
        self.test_get_stats_after_seeding()

        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

def main():
    tester = CodeTrackrAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())