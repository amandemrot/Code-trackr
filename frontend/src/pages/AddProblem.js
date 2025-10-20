import { useState } from 'react';
import axios from 'axios';
import { API } from '../App';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';
import '../styles/AddProblem.css';

const TOPICS = [
  'Arrays', 'Strings', 'Linked List', 'Trees', 'Graphs', 'DP', 'Greedy', 
  'Backtracking', 'Binary Search', 'Two Pointers', 'Sliding Window', 'Stack', 
  'Queue', 'Heap', 'Hash Table', 'Math', 'Bit Manipulation', 'Sorting', 'DFS', 'BFS'
];

function AddProblem({ user, onLogout }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    platform: 'LeetCode',
    difficulty: 'Easy',
    date_completed: new Date().toISOString().split('T')[0]
  });
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleTopicToggle = (topic) => {
    setSelectedTopics(prev => 
      prev.includes(topic) 
        ? prev.filter(t => t !== topic)
        : [...prev, topic]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (selectedTopics.length === 0) {
      toast.error('Please select at least one topic');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/problems`, {
        ...formData,
        topics: selectedTopics
      });
      
      toast.success('Problem added successfully!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add problem');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-problem-container" data-testid="add-problem-page">
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <h2>CodeTrackr</h2>
          <span className="username">@{user.username}</span>
        </div>
        <div className="nav-actions">
          <Button 
            onClick={() => navigate('/')} 
            data-testid="back-to-dashboard-button"
            variant="outline"
          >
            <ArrowLeft size={18} /> Back to Dashboard
          </Button>
        </div>
      </nav>

      <div className="add-problem-content">
        <Card className="add-problem-card">
          <CardHeader>
            <CardTitle data-testid="add-problem-title">Add New Problem</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="problem-form">
              <div className="form-row">
                <div className="form-group full-width">
                  <Label htmlFor="title">Problem Title</Label>
                  <Input
                    id="title"
                    data-testid="problem-title-input"
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    placeholder="e.g., Two Sum"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <Label htmlFor="platform">Platform</Label>
                  <Select 
                    value={formData.platform} 
                    onValueChange={(value) => setFormData({ ...formData, platform: value })}
                  >
                    <SelectTrigger data-testid="platform-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="LeetCode">LeetCode</SelectItem>
                      <SelectItem value="Codeforces">Codeforces</SelectItem>
                      <SelectItem value="HackerRank">HackerRank</SelectItem>
                      <SelectItem value="CodeChef">CodeChef</SelectItem>
                      <SelectItem value="AtCoder">AtCoder</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="form-group">
                  <Label htmlFor="difficulty">Difficulty</Label>
                  <Select 
                    value={formData.difficulty} 
                    onValueChange={(value) => setFormData({ ...formData, difficulty: value })}
                  >
                    <SelectTrigger data-testid="difficulty-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Easy">Easy</SelectItem>
                      <SelectItem value="Medium">Medium</SelectItem>
                      <SelectItem value="Hard">Hard</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="form-group">
                  <Label htmlFor="date">Date Completed</Label>
                  <Input
                    id="date"
                    data-testid="date-input"
                    type="date"
                    value={formData.date_completed}
                    onChange={(e) => setFormData({ ...formData, date_completed: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <Label>Topics (Select one or more)</Label>
                <div className="topics-grid" data-testid="topics-grid">
                  {TOPICS.map((topic) => (
                    <button
                      key={topic}
                      type="button"
                      data-testid={`topic-${topic}`}
                      onClick={() => handleTopicToggle(topic)}
                      className={`topic-chip ${selectedTopics.includes(topic) ? 'selected' : ''}`}
                    >
                      {topic}
                    </button>
                  ))}
                </div>
                {selectedTopics.length > 0 && (
                  <div className="selected-topics" data-testid="selected-topics">
                    Selected: {selectedTopics.join(', ')}
                  </div>
                )}
              </div>

              <div className="form-actions">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => navigate('/')}
                  data-testid="cancel-button"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  data-testid="submit-problem-button"
                  disabled={loading}
                >
                  {loading ? 'Adding...' : 'Add Problem'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default AddProblem;