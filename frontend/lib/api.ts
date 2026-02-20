import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s - first chat can be slow (LLM + ChromaDB init)
});

export interface RegisterData {
  user_id: string;
  name: string;
  primary_persona: string;
  preferred_personas: string[];
  academic_field?: string;
  study_topics: string[];
  goals: string[];
  traits: string[];
}

export interface ChatResponse {
  response: string;
  agent_avatar: string;
  agent_name: string;
}

export interface UserProfile {
  user_id: string;
  name: string;
  primary_persona: string;
  preferred_personas: string[];
  academic_field?: string;
  study_topics: string[];
  goals: string[];
  traits: string[];
}

export const apiClient = {
  // Check if user exists
  async checkUser(userId: string): Promise<boolean> {
    try {
      const response = await api.get(`/api/profile/${userId}`);
      return response.status === 200;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return false;
      }
      throw error;
    }
  },

  // Register new user
  async register(data: RegisterData): Promise<UserProfile> {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },

  // Get user profile
  async getProfile(userId: string): Promise<UserProfile> {
    const response = await api.get(`/api/profile/${userId}`);
    return response.data;
  },

  // Warm up chatbot (call when chat page loads to reduce first-message latency)
  async warmup(userId: string): Promise<void> {
    await api.get(`/api/warmup`, { params: { user_id: userId } });
  },

  // Send chat message
  async chat(userId: string, message: string): Promise<ChatResponse> {
    const response = await api.post('/api/chat', {
      user_id: userId,
      message: message,
    });
    return response.data;
  },

  // Upload PDF
  async uploadFile(userId: string, file: File): Promise<{ message: string; chunks: number }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    
    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};



