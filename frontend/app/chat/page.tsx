'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient, ChatResponse } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentAvatar?: string;
  agentName?: string;
}

const AGENT_NAMES: Record<string, string> = {
  '📚': 'Tutor',
  '📅': 'Scheduler',
  '🔍': 'Analyzer',
  '💪': 'Motivator',
  '🧭': 'Router',
  '🤖': 'System',
};

export default function ChatPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const userId = searchParams.get('userId');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!userId) {
      router.push('/');
    }
  }, [userId, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || !userId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response: ChatResponse = await apiClient.chat(userId, input);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        agentAvatar: response.agent_avatar,
        agentName: response.agent_name,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || 'Failed to send message'}`,
        agentAvatar: '🤖',
        agentName: 'System',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !userId) return;

    if (file.type !== 'application/pdf') {
      alert('Please upload a PDF file');
      return;
    }

    setUploading(true);
    try {
      const result = await apiClient.uploadFile(userId, file);
      const successMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `✅ ${result.message}\n📊 Total chunks: ${result.chunks}`,
        agentAvatar: '📚',
        agentName: 'Tutor',
      };
      setMessages((prev) => [...prev, successMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error uploading file: ${error.response?.data?.detail || 'Upload failed'}`,
        agentAvatar: '🤖',
        agentName: 'System',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const currentAgent = messages.length > 0 && messages[messages.length - 1].role === 'assistant'
    ? messages[messages.length - 1].agentAvatar
    : null;

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0a0a0a]">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#1a1a1a]/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Study Pal
            </h1>
            {currentAgent && (
              <div className="flex items-center gap-2 px-3 py-1 bg-[#0a0a0a] border border-gray-700 rounded-lg">
                <span className="text-2xl">{currentAgent}</span>
                <span className="text-sm text-gray-400">
                  {AGENT_NAMES[currentAgent] || 'AI'}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="px-4 py-2 border border-gray-700 hover:border-gray-600 rounded-lg text-sm text-gray-300 hover:text-white transition-all disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : '📄 Upload PDF'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 border border-gray-700 hover:border-gray-600 rounded-lg text-sm text-gray-300 hover:text-white transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto max-w-6xl w-full mx-auto px-4 py-8">
        {messages.length === 0 && (
          <div className="text-center mt-20">
            <div className="text-6xl mb-4">🎓</div>
            <h2 className="text-2xl font-semibold mb-2 text-gray-300">Welcome to Study Pal!</h2>
            <p className="text-gray-500">Ask me anything about your studies, or upload a PDF to get started.</p>
          </div>
        )}

        <div className="space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl">
                    {message.agentAvatar || '🤖'}
                  </div>
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-6 py-4 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                    : 'bg-[#1a1a1a] border border-gray-800 text-gray-100'
                }`}
              >
                <div className="whitespace-pre-wrap break-words">{message.content}</div>
                {message.role === 'assistant' && message.agentName && (
                  <div className="mt-2 text-xs text-gray-500">
                    {message.agentName}
                  </div>
                )}
              </div>
              {message.role === 'user' && (
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-2xl">
                    👤
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl">
                  🤖
                </div>
              </div>
              <div className="bg-[#1a1a1a] border border-gray-800 rounded-2xl px-6 py-4">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <footer className="border-t border-gray-800 bg-[#1a1a1a]/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <form onSubmit={handleSend} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question or request help..."
              disabled={loading}
              className="flex-1 px-6 py-4 bg-[#0a0a0a] border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl font-medium text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              Send
            </button>
          </form>
        </div>
      </footer>
    </div>
  );
}



