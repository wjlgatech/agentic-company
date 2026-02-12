/**
 * SmartChatbox: Single chatbox with inline refinement capabilities.
 *
 * This component provides a unified chat interface that handles:
 * 1. Regular conversation
 * 2. Inline clarification cards (clickable options)
 * 3. Draft previews with accept/refine actions
 * 4. Progressive refinement without leaving the chat
 *
 * Key UX Principles:
 * - ONE input box for everything
 * - Inline cards feel like conversation, not forms
 * - Clicking an option sends it as a message
 * - Draft previews are expandable/collapsible
 * - Accept/refine buttons are prominent but not intrusive
 */

import React, { useState, useRef, useEffect } from 'react';

// =============================================================================
// INLINE CARD COMPONENTS
// =============================================================================

/**
 * Quick option button that appears inline in chat
 */
const QuickOption = ({ label, value, description, onClick, selected }) => (
  <button
    onClick={() => onClick(value, label)}
    className={`
      inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium
      transition-all duration-150 mr-2 mb-2
      ${selected
        ? 'bg-blue-600 text-white'
        : 'bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-gray-900'
      }
    `}
    title={description}
  >
    {label}
  </button>
);

/**
 * Clarification card that appears inline in assistant messages
 */
const ClarificationCard = ({ card, onOptionClick, onFreeformSubmit }) => {
  const [freeformValue, setFreeformValue] = useState('');

  return (
    <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
      <p className="text-sm font-medium text-gray-700 mb-2">
        {card.question}
      </p>
      <div className="flex flex-wrap">
        {card.options.map((option, idx) => (
          <QuickOption
            key={idx}
            label={option.label}
            value={option.value}
            description={option.description}
            onClick={onOptionClick}
          />
        ))}
      </div>
      {card.allowFreeform && (
        <div className="mt-2 flex gap-2">
          <input
            type="text"
            value={freeformValue}
            onChange={(e) => setFreeformValue(e.target.value)}
            placeholder="Or type your own..."
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && freeformValue.trim()) {
                onFreeformSubmit(freeformValue);
                setFreeformValue('');
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

/**
 * Draft preview card with accept/refine actions
 */
const DraftPreview = ({ draft, onAccept, onRefine }) => {
  const [expanded, setExpanded] = useState(true);

  const confidenceColor = draft.confidence >= 0.8 ? 'text-green-600' :
                          draft.confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className="mt-3 border border-blue-200 rounded-lg overflow-hidden">
      {/* Header - always visible */}
      <div
        className="flex items-center justify-between px-4 py-2 bg-blue-50 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <span className="text-blue-600">📋</span>
          <span className="font-medium text-gray-900">Draft Ready</span>
          <span className={`text-sm ${confidenceColor}`}>
            ({Math.round(draft.confidence * 100)}% confident)
          </span>
        </div>
        <span className="text-gray-400">{expanded ? '▼' : '▶'}</span>
      </div>

      {/* Expandable content */}
      {expanded && (
        <div className="px-4 py-3 bg-white">
          <p className="text-sm text-gray-600 mb-2">
            <strong>Summary:</strong> {draft.summary}
          </p>

          <div className="text-sm text-gray-600 mb-3">
            <strong>Approach:</strong>
            <ol className="list-decimal list-inside mt-1 space-y-1">
              {draft.approach.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>

          <p className="text-sm text-gray-600 mb-4">
            <strong>Output:</strong> {draft.outputType}
          </p>

          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={onAccept}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              ✓ Looks good, proceed
            </button>
            <button
              onClick={onRefine}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Refine
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// MESSAGE COMPONENTS
// =============================================================================

/**
 * User message bubble
 */
const UserMessage = ({ content }) => (
  <div className="flex justify-end mb-4">
    <div className="max-w-[80%] px-4 py-2 bg-blue-600 text-white rounded-2xl rounded-br-md">
      {content}
    </div>
  </div>
);

/**
 * Assistant message with optional cards and draft
 */
const AssistantMessage = ({ content, cards, draft, onOptionClick, onAccept, onRefine }) => (
  <div className="flex justify-start mb-4">
    <div className="max-w-[85%]">
      <div className="px-4 py-2 bg-gray-100 text-gray-900 rounded-2xl rounded-bl-md">
        {/* Render markdown-like content */}
        <div className="prose prose-sm max-w-none">
          {content.split('\n').map((line, idx) => {
            if (line.startsWith('**') && line.endsWith('**')) {
              return <p key={idx} className="font-bold">{line.slice(2, -2)}</p>;
            }
            if (line.startsWith('•')) {
              return <p key={idx} className="ml-4">{line}</p>;
            }
            if (line.startsWith('---')) {
              return <hr key={idx} className="my-2" />;
            }
            return line ? <p key={idx}>{line}</p> : <br key={idx} />;
          })}
        </div>
      </div>

      {/* Inline clarification cards */}
      {cards && cards.length > 0 && cards.map((card, idx) => (
        <ClarificationCard
          key={idx}
          card={card}
          onOptionClick={onOptionClick}
          onFreeformSubmit={onOptionClick}
        />
      ))}

      {/* Draft preview */}
      {draft && (
        <DraftPreview
          draft={draft}
          onAccept={onAccept}
          onRefine={onRefine}
        />
      )}
    </div>
  </div>
);

// =============================================================================
// MAIN CHATBOX COMPONENT
// =============================================================================

const SmartChatbox = ({
  onFinalPromptReady,  // Callback when refinement is complete
  placeholder = "Ask me anything...",
  apiEndpoint = "/api/refinement",
}) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionState, setSessionState] = useState('initial');
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Start session on mount
  useEffect(() => {
    startSession();
  }, []);

  const startSession = async () => {
    try {
      const response = await fetch(`${apiEndpoint}/session/start`, {
        method: 'POST',
      });
      const data = await response.json();
      setSessionId(data.session_id);
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || !sessionId) return;

    setIsLoading(true);

    // Optimistically add user message
    const userMessage = { role: 'user', content: messageText };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await fetch(`${apiEndpoint}/session/${sessionId}/input`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText }),
      });
      const data = await response.json();

      // Update with server response
      setMessages(data.messages);
      setSessionState(data.state);

      // If complete, call the callback with final prompt
      if (data.final_prompt && onFinalPromptReady) {
        onFinalPromptReady(data.final_prompt);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOptionClick = (value, label) => {
    // Send the selected option as a message
    sendMessage(label);
  };

  const handleAccept = () => {
    sendMessage('Yes, proceed');
  };

  const handleRefine = () => {
    sendMessage('I want to refine this');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <h2 className="font-semibold">Smart Assistant</h2>
        <p className="text-xs text-blue-100">
          {sessionState === 'draft_ready' ? '✨ Draft ready for review' :
           sessionState === 'complete' ? '✅ Complete' :
           'Ask me anything...'}
        </p>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">👋 Hi there!</p>
            <p className="text-sm">Tell me what you need help with.</p>
            <p className="text-xs text-gray-400 mt-2">
              I'll ask a few quick questions to make sure I understand.
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          msg.role === 'user' ? (
            <UserMessage key={idx} content={msg.content} />
          ) : (
            <AssistantMessage
              key={idx}
              content={msg.content}
              cards={msg.cards}
              draft={msg.draft}
              onOptionClick={handleOptionClick}
              onAccept={handleAccept}
              onRefine={handleRefine}
            />
          )
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="px-4 py-2 bg-gray-100 rounded-2xl">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={placeholder}
            disabled={isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-full font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};

export default SmartChatbox;

// =============================================================================
// USAGE EXAMPLE
// =============================================================================

/*
import SmartChatbox from './components/SmartChatbox';

function App() {
  const handleFinalPrompt = (prompt) => {
    console.log('Refinement complete! Final prompt:', prompt);
    // Now you can use the prompt to generate the actual response
  };

  return (
    <div className="h-screen p-4 bg-gray-100">
      <div className="max-w-2xl mx-auto h-full">
        <SmartChatbox
          onFinalPromptReady={handleFinalPrompt}
          placeholder="What can I help you with?"
        />
      </div>
    </div>
  );
}
*/
