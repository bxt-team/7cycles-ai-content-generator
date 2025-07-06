import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './InstagramPostsInterface.css';

interface InstagramPost {
  id: string;
  post_text: string;
  hashtags: string[];
  call_to_action: string;
  engagement_strategies: string[];
  optimal_posting_time: string;
  period_name: string;
  period_color: string;
  affirmation: string;
  style: string;
  created_at: string;
  source?: string;
}

interface Affirmation {
  id: string;
  text: string;
  theme: string;
  focus: string;
  created_at: string;
  period_type: string;
  period_name?: string;
  period_color?: string;
  period_info: any;
}

interface GenerateResponse {
  success: boolean;
  post: InstagramPost;
  source: string;
  message: string;
}

interface PostsResponse {
  success: boolean;
  posts: InstagramPost[];
  count: number;
  period_name?: string;
}

const InstagramPostsInterface: React.FC = () => {
  const [posts, setPosts] = useState<InstagramPost[]>([]);
  const [affirmations, setAffirmations] = useState<Affirmation[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingAffirmations, setLoadingAffirmations] = useState(false);
  const [affirmation, setAffirmation] = useState<string>('');
  const [selectedAffirmation, setSelectedAffirmation] = useState<string>('');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [selectedStyle, setSelectedStyle] = useState<string>('inspirational');
  const [filterPeriod, setFilterPeriod] = useState<string>('');
  const [expandedPost, setExpandedPost] = useState<string | null>(null);
  const [inputMode, setInputMode] = useState<'manual' | 'existing'>('existing');
  const [creatingVisual, setCreatingVisual] = useState<string | null>(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const periods = ['Image', 'Veränderung', 'Energie', 'Kreativität', 'Erfolg', 'Entspannung', 'Umsicht'];
  const styles = [
    { value: 'inspirational', label: 'Inspirational' },
    { value: 'motivational', label: 'Motivational' },
    { value: 'empowering', label: 'Empowering' },
    { value: 'artistic', label: 'Artistic' },
    { value: 'professional', label: 'Professional' },
    { value: 'spiritual', label: 'Spiritual' }
  ];

  useEffect(() => {
    loadPosts();
    loadAffirmations();
  }, []);

  const loadPosts = async (periodFilter?: string) => {
    try {
      const url = periodFilter 
        ? `${API_BASE_URL}/instagram-posts?period_name=${periodFilter}`
        : `${API_BASE_URL}/instagram-posts`;
      
      const response = await axios.get<PostsResponse>(url);
      if (response.data.success) {
        setPosts(response.data.posts);
      }
    } catch (error) {
      console.error('Error loading Instagram posts:', error);
    }
  };

  const loadAffirmations = async () => {
    setLoadingAffirmations(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/affirmations`);
      if (response.data.success) {
        setAffirmations(response.data.affirmations);
      }
    } catch (error) {
      console.error('Error loading affirmations:', error);
    } finally {
      setLoadingAffirmations(false);
    }
  };

  const handleAffirmationSelect = (affirmationId: string) => {
    const selected = affirmations.find(aff => aff.id === affirmationId);
    if (selected) {
      setSelectedAffirmation(affirmationId);
      setAffirmation(selected.text);
      setSelectedPeriod(selected.period_name || selected.theme);
    }
  };

  const handleInputModeChange = (mode: 'manual' | 'existing') => {
    setInputMode(mode);
    // Reset form when switching modes
    setAffirmation('');
    setSelectedAffirmation('');
    setSelectedPeriod('');
    setSelectedStyle('inspirational');
  };

  const getAffirmationPeriodColor = (affirmation: Affirmation) => {
    if (affirmation.period_color) {
      return affirmation.period_color;
    }
    
    const cyclesColors: { [key: string]: string } = {
      'Image': '#DAA520',
      'Veränderung': '#2196F3', 
      'Energie': '#F44336',
      'Kreativität': '#FFD700',
      'Erfolg': '#CC0066',
      'Entspannung': '#4CAF50',
      'Umsicht': '#9C27B0'
    };
    
    return cyclesColors[affirmation.period_name || affirmation.theme] || '#a0a0a0';
  };

  const handleGeneratePost = async () => {
    const currentAffirmation = inputMode === 'existing' && selectedAffirmation 
      ? affirmations.find(aff => aff.id === selectedAffirmation)?.text || affirmation
      : affirmation;
      
    if (!currentAffirmation.trim() || !selectedPeriod) return;

    setLoading(true);
    try {
      const response = await axios.post<GenerateResponse>(`${API_BASE_URL}/generate-instagram-post`, {
        affirmation: currentAffirmation.trim(),
        period_name: selectedPeriod,
        style: selectedStyle
      });

      if (response.data.success) {
        setPosts(prev => [response.data.post, ...prev]);
        
        // Reset form
        setAffirmation('');
        setSelectedAffirmation('');
        setSelectedPeriod('');
        setSelectedStyle('inspirational');
        
        // Show success message
        alert(response.data.message);
      }
    } catch (error: any) {
      console.error('Error generating Instagram post:', error);
      const errorMessage = error.response?.data?.detail || 'Ein Fehler ist beim Generieren des Posts aufgetreten.';
      alert(`Fehler: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (period: string) => {
    setFilterPeriod(period);
    loadPosts(period || undefined);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('de-DE');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Text in die Zwischenablage kopiert!');
    });
  };

  const copyFullPost = (post: InstagramPost) => {
    const fullPost = `${post.post_text}\n\n${post.hashtags.join(' ')}\n\n${post.call_to_action}`;
    copyToClipboard(fullPost);
  };

  const createVisualPost = async (post: InstagramPost) => {
    setCreatingVisual(post.id);
    try {
      const response = await axios.post(`${API_BASE_URL}/create-visual-from-instagram-post`, {
        instagram_post_id: post.id,
        instagram_post: post,
        image_style: 'minimal'
      });

      if (response.data.success) {
        alert('✅ Visueller Post erfolgreich erstellt!');
        // Optional: Navigate to visual posts interface
        window.open('/visual-posts', '_blank');
      }
    } catch (error: any) {
      console.error('Error creating visual post:', error);
      const errorMessage = error.response?.data?.detail || 'Fehler beim Erstellen des visuellen Posts';
      alert(`❌ ${errorMessage}`);
    } finally {
      setCreatingVisual(null);
    }
  };

  const toggleExpanded = (postId: string) => {
    setExpandedPost(expandedPost === postId ? null : postId);
  };

  return (
    <div className="instagram-posts-interface">
      <div className="instagram-header">
        <h2>📱 Instagram Post Generator mit Hashtag Research</h2>
        <p>Erstelle ansprechende Instagram Posts mit Affirmationen, relevanten Hashtags und Call-to-Actions für Follower-Wachstum</p>
      </div>

      <div className="generator-section">
        <h3>✨ Neuen Instagram Post generieren</h3>
        
        {/* Input Mode Selector */}
        <div className="input-mode-selector">
          <label>Affirmation wählen:</label>
          <div className="mode-buttons">
            <button
              className={`mode-button ${inputMode === 'existing' ? 'active' : ''}`}
              onClick={() => handleInputModeChange('existing')}
              disabled={loading}
            >
              📋 Aus bestehenden Affirmationen
            </button>
            <button
              className={`mode-button ${inputMode === 'manual' ? 'active' : ''}`}
              onClick={() => handleInputModeChange('manual')}
              disabled={loading}
            >
              ✏️ Manuell eingeben
            </button>
          </div>
        </div>

        <div className="generator-form">
          {inputMode === 'existing' ? (
            /* Existing Affirmations Selection */
            <div className="existing-affirmations-section">
              <div className="form-group">
                <label>Wähle eine bestehende Affirmation ({affirmations.length} verfügbar):</label>
                {loadingAffirmations ? (
                  <div className="loading-affirmations">🔄 Lade Affirmationen...</div>
                ) : affirmations.length === 0 ? (
                  <div className="no-affirmations-message">
                    📝 Noch keine Affirmationen vorhanden. 
                    <span 
                      className="create-first-link"
                      onClick={() => window.location.href = '/affirmations'}
                    >
                      Erstelle zuerst eine Affirmation
                    </span>
                  </div>
                ) : (
                  <div className="affirmations-grid">
                    {affirmations.map((aff) => (
                      <div 
                        key={aff.id} 
                        className={`affirmation-card ${selectedAffirmation === aff.id ? 'selected' : ''}`}
                        onClick={() => handleAffirmationSelect(aff.id)}
                      >
                        <div className="affirmation-header">
                          <span 
                            className="period-badge"
                            style={{ backgroundColor: getAffirmationPeriodColor(aff) }}
                          >
                            {aff.period_name || aff.theme}
                          </span>
                          <span className="focus-text">{aff.focus}</span>
                        </div>
                        <div className="affirmation-text">{aff.text}</div>
                        <div className="affirmation-date">
                          {formatTimestamp(aff.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {selectedAffirmation && (
                <div className="selected-affirmation-preview">
                  <strong>Ausgewählte Affirmation:</strong>
                  <div className="preview-content">{affirmation}</div>
                  <div className="preview-period">Periode: {selectedPeriod}</div>
                </div>
              )}
            </div>
          ) : (
            /* Manual Input */
            <div className="form-group">
              <label>Affirmation:</label>
              <textarea
                value={affirmation}
                onChange={(e) => setAffirmation(e.target.value)}
                placeholder="Gib deine Affirmation ein, z.B. 'Ich bin voller Energie und Lebenskraft'"
                disabled={loading}
                rows={3}
              />
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>7 Cycles Periode:</label>
              <select 
                value={selectedPeriod} 
                onChange={(e) => setSelectedPeriod(e.target.value)}
                disabled={loading || (inputMode === 'existing' && !!selectedAffirmation)}
              >
                <option value="">Wähle eine Periode</option>
                {periods.map(period => (
                  <option key={period} value={period}>
                    {period}
                  </option>
                ))}
              </select>
              {inputMode === 'existing' && selectedAffirmation && (
                <small className="field-note">Periode wird automatisch aus der Affirmation übernommen</small>
              )}
            </div>

            <div className="form-group">
              <label>Stil:</label>
              <select 
                value={selectedStyle} 
                onChange={(e) => setSelectedStyle(e.target.value)}
                disabled={loading}
              >
                {styles.map(style => (
                  <option key={style.value} value={style.value}>
                    {style.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={handleGeneratePost}
            disabled={loading || !affirmation.trim() || !selectedPeriod}
            className="generate-button"
          >
            {loading ? '🔄 Generiere Post...' : '🚀 Instagram Post generieren'}
          </button>
        </div>
      </div>

      <div className="posts-display">
        <div className="display-header">
          <h3>📋 Deine Instagram Posts ({posts.length})</h3>
          <div className="filter-section">
            <label>Nach Periode filtern:</label>
            <select 
              value={filterPeriod} 
              onChange={(e) => handleFilterChange(e.target.value)}
            >
              <option value="">Alle Perioden</option>
              {periods.map(period => (
                <option key={period} value={period}>
                  {period}
                </option>
              ))}
            </select>
          </div>
        </div>

        {posts.length === 0 ? (
          <div className="no-posts">
            <p>📝 Noch keine Instagram Posts generiert.</p>
            <p>Erstelle deinen ersten Post mit einer Affirmation und 7 Cycles Periode!</p>
          </div>
        ) : (
          <div className="posts-grid">
            {posts.map((post) => (
              <div key={post.id} className="post-card">
                <div className="post-header">
                  <div className="post-meta">
                    <span 
                      className="period-tag"
                      style={{ backgroundColor: post.period_color }}
                    >
                      {post.period_name}
                    </span>
                    <span className="style-tag">{post.style}</span>
                    <button
                      className="copy-button"
                      onClick={() => copyFullPost(post)}
                      title="Kompletten Post kopieren"
                    >
                      📋
                    </button>
                    <button
                      className="visual-post-button"
                      onClick={() => createVisualPost(post)}
                      title="Visuellen Post erstellen"
                      disabled={creatingVisual === post.id}
                    >
                      {creatingVisual === post.id ? '🔄' : '🎨'}
                    </button>
                  </div>
                  <div className="post-time">
                    🕐 {post.optimal_posting_time}
                  </div>
                </div>

                <div className="post-content">
                  <div className="affirmation-source">
                    <strong>💫 Affirmation:</strong> {post.affirmation}
                  </div>

                  <div className="post-text">
                    <strong>📝 Post Text:</strong>
                    <div className="text-content">
                      {post.post_text}
                    </div>
                    <button
                      className="copy-text-button"
                      onClick={() => copyToClipboard(post.post_text)}
                    >
                      Text kopieren
                    </button>
                  </div>

                  <div className="hashtags-section">
                    <strong>🏷️ Hashtags ({post.hashtags.length}):</strong>
                    <div className="hashtags-container">
                      {expandedPost === post.id ? (
                        <div className="hashtags-full">
                          {post.hashtags.join(' ')}
                        </div>
                      ) : (
                        <div className="hashtags-preview">
                          {post.hashtags.slice(0, 10).join(' ')}
                          {post.hashtags.length > 10 && '...'}
                        </div>
                      )}
                      <div className="hashtags-actions">
                        <button
                          className="toggle-hashtags"
                          onClick={() => toggleExpanded(post.id)}
                        >
                          {expandedPost === post.id ? 'Weniger' : `Alle ${post.hashtags.length} zeigen`}
                        </button>
                        <button
                          className="copy-hashtags-button"
                          onClick={() => copyToClipboard(post.hashtags.join(' '))}
                        >
                          Hashtags kopieren
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="call-to-action">
                    <strong>📞 Call-to-Action:</strong>
                    <div className="cta-content">{post.call_to_action}</div>
                    <button
                      className="copy-cta-button"
                      onClick={() => copyToClipboard(post.call_to_action)}
                    >
                      CTA kopieren
                    </button>
                  </div>

                  {expandedPost === post.id && (
                    <div className="engagement-strategies">
                      <strong>📈 Engagement-Strategien:</strong>
                      <ul>
                        {post.engagement_strategies.map((strategy, index) => (
                          <li key={index}>{strategy}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="post-footer">
                    <span className="timestamp">
                      Erstellt: {formatTimestamp(post.created_at)}
                    </span>
                    <span className="source">
                      {post.source === 'existing' ? '♻️ Wiederverwendet' : '✨ Neu generiert'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default InstagramPostsInterface;