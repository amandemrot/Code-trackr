import { useState } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import '../styles/Login.css';

function Login({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const response = await axios.post(`${API}${endpoint}`, { username, password });
      
      toast.success(isLogin ? 'Welcome back!' : 'Account created successfully!');
      onLogin(response.data.access_token, response.data.user);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container" data-testid="login-page">
      <div className="login-content">
        <div className="login-header">
          <h1 className="app-title" data-testid="app-title">CodeTrackr</h1>
          <p className="app-subtitle">Track your coding journey, one problem at a time</p>
        </div>

        <Card className="login-card">
          <CardHeader>
            <CardTitle data-testid="auth-title">{isLogin ? 'Welcome Back' : 'Create Account'}</CardTitle>
            <CardDescription>
              {isLogin ? 'Login to continue tracking your progress' : 'Start tracking your coding problems today'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-group">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  data-testid="username-input"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder="Enter your username"
                />
              </div>
              
              <div className="form-group">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  data-testid="password-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Enter your password"
                />
              </div>

              <Button 
                type="submit" 
                data-testid="submit-button"
                className="submit-btn" 
                disabled={loading}
              >
                {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Sign Up')}
              </Button>

              <div className="toggle-auth">
                <button
                  type="button"
                  data-testid="toggle-auth-button"
                  onClick={() => setIsLogin(!isLogin)}
                  className="toggle-link"
                >
                  {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Login'}
                </button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Login;