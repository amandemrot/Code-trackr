import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Plus, LogOut, Trophy, TrendingUp, Target } from 'lucide-react';
import { toast } from 'sonner';
import '../styles/Dashboard.css';

function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [problems, setProblems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const fetchData = async () => {
    try {
      const [problemsRes, statsRes] = await Promise.all([
        axios.get(`${API}/problems`),
        axios.get(`${API}/stats`)
      ]);
      
      setProblems(problemsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedData = async () => {
    setSeeding(true);
    try {
      await axios.post(`${API}/seed-data`);
      toast.success('Sample data added!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to seed data');
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  const chartColors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'];
  const chartData = stats?.topic_wise.slice(0, 6) || [];

  return (
    <div className="dashboard-container" data-testid="dashboard-page">
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <h2 data-testid="dashboard-title">CodeTrackr</h2>
          <span className="username" data-testid="username-display">@{user.username}</span>
        </div>
        <div className="nav-actions">
          <Button 
            onClick={() => navigate('/add')} 
            data-testid="add-problem-nav-button"
            className="btn-add"
          >
            <Plus size={18} /> Add Problem
          </Button>
          <Button 
            onClick={onLogout} 
            data-testid="logout-button"
            variant="outline" 
            className="btn-logout"
          >
            <LogOut size={18} /> Logout
          </Button>
        </div>
      </nav>

      <div className="dashboard-content">
        {problems.length === 0 ? (
          <Card className="empty-state">
            <CardContent className="empty-content">
              <Target size={64} className="empty-icon" />
              <h3>No problems tracked yet</h3>
              <p>Start by adding your first solved problem or load sample data</p>
              <div className="empty-actions">
                <Button 
                  onClick={() => navigate('/add')} 
                  data-testid="add-first-problem-button"
                  size="lg"
                >
                  <Plus size={18} /> Add Problem
                </Button>
                <Button 
                  onClick={handleSeedData} 
                  data-testid="seed-data-button"
                  variant="outline" 
                  size="lg" 
                  disabled={seeding}
                >
                  {seeding ? 'Loading...' : 'Load Sample Data'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="stats-grid">
              <Card className="stat-card">
                <CardHeader className="stat-header">
                  <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                    <Trophy size={24} />
                  </div>
                  <CardTitle className="stat-label">Total Solved</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="stat-value" data-testid="total-solved">{stats?.total_solved || 0}</div>
                </CardContent>
              </Card>

              <Card className="stat-card">
                <CardHeader className="stat-header">
                  <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                    <TrendingUp size={24} />
                  </div>
                  <CardTitle className="stat-label">Current Streak</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="stat-value" data-testid="current-streak">{stats?.current_streak || 0} days</div>
                </CardContent>
              </Card>

              <Card className="stat-card">
                <CardHeader className="stat-header">
                  <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                    <Target size={24} />
                  </div>
                  <CardTitle className="stat-label">Topics Covered</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="stat-value" data-testid="topics-covered">{stats?.topic_wise.length || 0}</div>
                </CardContent>
              </Card>
            </div>

            <div className="charts-section">
              <Card className="chart-card">
                <CardHeader>
                  <CardTitle>Topic-wise Progress</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="topic" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip 
                        contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                        formatter={(value, name) => [value, name === 'count' ? 'Problems' : name]}
                      />
                      <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="topics-card">
                <CardHeader>
                  <CardTitle>Completion Percentage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="topics-list">
                    {chartData.map((topic, index) => (
                      <div key={topic.topic} className="topic-item" data-testid={`topic-${topic.topic}`}>
                        <div className="topic-info">
                          <div 
                            className="topic-color" 
                            style={{ background: chartColors[index % chartColors.length] }}
                          />
                          <span className="topic-name">{topic.topic}</span>
                        </div>
                        <div className="topic-stats">
                          <span className="topic-count">{topic.count} problems</span>
                          <span className="topic-percentage" data-testid={`topic-percentage-${topic.topic}`}>
                            {topic.percentage}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="problems-card">
              <CardHeader>
                <CardTitle>Recent Problems</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="problems-table">
                  <div className="table-header">
                    <div className="col-title">Problem</div>
                    <div className="col-platform">Platform</div>
                    <div className="col-difficulty">Difficulty</div>
                    <div className="col-topics">Topics</div>
                    <div className="col-date">Date</div>
                  </div>
                  {problems.slice(0, 10).map((problem) => (
                    <div key={problem.id} className="table-row" data-testid={`problem-${problem.id}`}>
                      <div className="col-title">{problem.title}</div>
                      <div className="col-platform">
                        <span className="platform-badge">{problem.platform}</span>
                      </div>
                      <div className="col-difficulty">
                        <span className={`difficulty-badge difficulty-${problem.difficulty.toLowerCase()}`}>
                          {problem.difficulty}
                        </span>
                      </div>
                      <div className="col-topics">
                        {problem.topics.slice(0, 2).map((topic) => (
                          <span key={topic} className="topic-badge">{topic}</span>
                        ))}
                        {problem.topics.length > 2 && (
                          <span className="topic-badge">+{problem.topics.length - 2}</span>
                        )}
                      </div>
                      <div className="col-date">{problem.date_completed}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

export default Dashboard;