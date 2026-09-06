import React, { useState, useEffect } from 'react';
import { SatelliteScene, VLMQueryResponse } from '../../types/satellite';
import { apiClient } from '../../services/apiClient';

interface VLMInteractionPanelProps {
  scene: SatelliteScene | null;
}

const QUICK_QUESTIONS = [
  'Describe the visible land cover.',
  'What vegetation is visible?',
  'Are water bodies present?',
  'What are the main visual features?',
];

export const VLMInteractionPanel: React.FC<VLMInteractionPanelProps> = ({ scene }) => {
  const [question, setQuestion] = useState('');
  const [includeNdviContext, setIncludeNdviContext] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [vlmResponse, setVlmResponse] = useState<VLMQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastSceneId, setLastSceneId] = useState<string | null>(null);

  // Clear stale responses when selected scene changes
  useEffect(() => {
    if (scene?.id !== lastSceneId) {
      setLastSceneId(scene?.id || null);
      setVlmResponse(null);
      setError(null);
    }
  }, [scene?.id, lastSceneId]);

  const handleSubmit = async (overrideQuestion?: string) => {
    const activeQuestion = (overrideQuestion || question).trim();
    if (!scene || !activeQuestion || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await apiClient.askVLM(scene.id, activeQuestion, includeNdviContext);
      setVlmResponse(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setVlmResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickQuestion = (q: string) => {
    setQuestion(q);
    handleSubmit(q);
  };

  const handleClear = () => {
    setQuestion('');
    setVlmResponse(null);
    setError(null);
  };

  const getConfidenceBadgeColor = (level: 'high' | 'medium' | 'low') => {
    switch (level) {
      case 'high':
        return 'var(--accent-emerald)';
      case 'medium':
        return 'var(--accent-amber)';
      case 'low':
        return 'var(--accent-rose)';
      default:
        return 'var(--text-muted)';
    }
  };

  return (
    <div className="vlm-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '16px' }}>
      {/* Header Banner */}
      <div
        style={{
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: scene ? 'var(--accent-cyan)' : 'var(--text-muted)',
              }}
            />
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              Multimodal Visual Assistant
            </h4>
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
            Grounded vision-language scene interpretation powered by Gemini
          </p>
        </div>

        {scene && (
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--bg-card)',
              color: 'var(--accent-cyan)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            {scene.mission} (10m)
          </span>
        )}
      </div>

      {!scene ? (
        <div className="empty-state" style={{ padding: '32px 16px', textAlign: 'center' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Select a satellite scene from search results to ask natural-language questions.
          </p>
        </div>
      ) : (
        <>
          {/* Question Input Section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label
              htmlFor="vlm-question-input"
              style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-secondary)' }}
            >
              Ask about scene features, land use, vegetation, or water bodies:
            </label>

            <div style={{ position: 'relative' }}>
              <textarea
                id="vlm-question-input"
                rows={3}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                disabled={isLoading}
                placeholder="e.g. What visible features indicate agricultural vs urban activity?"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  backgroundColor: 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '12px',
                  fontFamily: 'var(--font-sans)',
                  resize: 'vertical',
                  outline: 'none',
                }}
              />
            </div>

            {/* Controls Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2px' }}>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                <input
                  type="checkbox"
                  checked={includeNdviContext}
                  onChange={(e) => setIncludeNdviContext(e.target.checked)}
                  disabled={isLoading}
                  style={{ accentColor: 'var(--accent-emerald)' }}
                />
                Include NDVI biophysical context
              </label>

              <div style={{ display: 'flex', gap: '8px' }}>
                {vlmResponse && (
                  <button
                    type="button"
                    onClick={handleClear}
                    disabled={isLoading}
                    style={{
                      background: 'none',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-muted)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '4px 10px',
                      fontSize: '11px',
                      cursor: 'pointer',
                    }}
                  >
                    Clear
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => handleSubmit()}
                  disabled={isLoading || !question.trim()}
                  style={{
                    backgroundColor: isLoading || !question.trim() ? 'var(--border-muted)' : 'var(--accent-cyan)',
                    color: isLoading || !question.trim() ? 'var(--text-muted)' : 'var(--text-inverse)',
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    padding: '6px 14px',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: isLoading || !question.trim() ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {isLoading ? 'Synthesizing...' : 'Ask Assistant'}
                </button>
              </div>
            </div>

            {/* Quick Questions Chips */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 500 }}>
                Suggested inquiries:
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {QUICK_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleQuickQuestion(q)}
                    disabled={isLoading}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)',
                      borderRadius: '12px',
                      padding: '3px 10px',
                      fontSize: '10px',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      textAlign: 'left',
                      transition: 'border-color 0.15s ease, color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                        e.currentTarget.style.color = 'var(--text-primary)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-subtle)';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Loading Indicator */}
          {isLoading && (
            <div
              style={{
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '24px 16px',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <div
                className="status-dot cyan"
                style={{
                  width: '12px',
                  height: '12px',
                  animation: 'pulse 1.5s infinite',
                }}
              />
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Multimodal Reasoning in Progress...
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '340px' }}>
                Extracting visual RGB granule, injecting 10m GSD metadata, and querying Gemini VLM.
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && !isLoading && (
            <div
              style={{
                backgroundColor: 'rgba(244, 63, 94, 0.08)',
                border: '1px solid var(--accent-rose)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-rose)', fontWeight: 600, fontSize: '11px' }}>
                <span>✕</span>
                <span>VLM Assistant Error</span>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-primary)', margin: 0, lineHeight: 1.4 }}>
                {error}
              </p>
              {error.includes('GEMINI_API_KEY') && (
                <div
                  style={{
                    marginTop: '4px',
                    fontSize: '10px',
                    color: 'var(--accent-amber)',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    padding: '6px 8px',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  Tip: Supply your Gemini API key in the backend <code>.env</code> file or Render dashboard environment settings as <code>GEMINI_API_KEY</code>.
                </div>
              )}
            </div>
          )}

          {/* VLM Result Card */}
          {vlmResponse && !isLoading && (
            <div
              className="vlm-result-card"
              style={{
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-muted)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              {/* Question Header & Confidence Badge */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '12px',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '10px',
                }}
              >
                <div>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Inquiry
                  </span>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                    &ldquo;{vlmResponse.question}&rdquo;
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    backgroundColor: 'var(--bg-surface)',
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    whiteSpace: 'nowrap',
                  }}
                  title={`Confidence rating based on visual feature resolution: ${(vlmResponse.confidence_score * 100).toFixed(1)}%`}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      backgroundColor: getConfidenceBadgeColor(vlmResponse.confidence_level),
                    }}
                  />
                  <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {(vlmResponse.confidence_score * 100).toFixed(0)}%
                  </span>
                  <span
                    style={{
                      fontSize: '9px',
                      textTransform: 'uppercase',
                      color: getConfidenceBadgeColor(vlmResponse.confidence_level),
                      fontWeight: 600,
                    }}
                  >
                    {vlmResponse.confidence_level}
                  </span>
                </div>
              </div>

              {/* Synthesized Answer Narrative */}
              <div>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Analytical Findings
                </span>
                <p style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: 1.5, marginTop: '4px' }}>
                  {vlmResponse.answer}
                </p>
              </div>

              {/* Grounded Evidence List */}
              {vlmResponse.evidence && vlmResponse.evidence.length > 0 && (
                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Grounded Visual Evidence ({vlmResponse.evidence.length})
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                    {vlmResponse.evidence.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: 'var(--bg-surface)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '8px 10px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '2px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                            {item.feature}
                          </span>
                          <span
                            style={{
                              fontSize: '9px',
                              fontFamily: 'var(--font-mono)',
                              textTransform: 'uppercase',
                              color: getConfidenceBadgeColor(item.confidence),
                            }}
                          >
                            {item.confidence}
                          </span>
                        </div>
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {item.observation}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Limitations & Caveats */}
              {vlmResponse.limitations && vlmResponse.limitations.length > 0 && (
                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Scientific Caveats & Limitations
                  </span>
                  <ul style={{ margin: '4px 0 0 16px', padding: 0, fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                    {vlmResponse.limitations.map((lim, idx) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Telemetry & Model Metadata Footer */}
              <div
                style={{
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '10px',
                  color: 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                <span>Model: {vlmResponse.model_used}</span>
                <span>Latency: {vlmResponse.latency_ms.toLocaleString()} ms</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
