'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient, ChatResponse } from '@/lib/api';
import { Message } from '@/types';
import { ChatHeader } from '@/components/chat/ChatHeader';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';

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

  // Warm up chatbot when chat page loads (reduces first-message wait)
  useEffect(() => {
    if (userId) {
      apiClient.warmup(userId).catch(() => { });
    }
  }, [userId]);

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
      const isTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout');
      const isNetwork =
        error.code === 'ECONNREFUSED' ||
        error.code === 'ETIMEDOUT' ||
        error.code === 'ERR_NETWORK';
      let content = error.response?.data?.detail || 'Failed to send message';
      if (isTimeout) content = 'Request timed out. The first message can take 30–60s while the AI loads. Please try again.';
      else if (isNetwork) content = 'Cannot reach backend. Make sure the API is running (./scripts/start_dev.sh).';
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${content}`,
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
    ? messages[messages.length - 1].agentAvatar || null
    : null;

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0a0a0a]">
      <ChatHeader
        currentAgent={currentAgent}
        uploading={uploading}
        fileInputRef={fileInputRef}
        handleFileUpload={handleFileUpload}
      />

      <MessageList
        messages={messages}
        loading={loading}
        messagesEndRef={messagesEndRef}
      />

      <ChatInput
        input={input}
        setInput={setInput}
        loading={loading}
        handleSend={handleSend}
      />
    </div>
  );
}
