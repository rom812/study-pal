'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, RegisterData } from '@/lib/api';

const PERSONAS = {
  "Richard Feynman": "Nobel physicist known for simplifying complex ideas with curiosity and humor",
  "Marie Curie": "Pioneer scientist who persevered through obstacles with dedication",
  "Steve Jobs": "Visionary innovator who pushed boundaries and thought differently",
  "Carl Sagan": "Cosmic educator who made science accessible and inspiring",
  "Kobe Bryant": "Elite athlete who embodied relentless work ethic and mental toughness",
  "David Goggins": "Ultra-endurance athlete focused on mental resilience and overcoming limits",
  "Eleanor Roosevelt": "Advocate for growth through facing fears and taking action",
  "Elon Musk": "Entrepreneur tackling ambitious goals through first principles thinking",
  "Jocko Willink": "Navy SEAL emphasizing discipline, ownership, and consistent execution",
  "Isaac Newton": "Mathematical genius who persisted in solving fundamental problems",
  "Niels Bohr": "Quantum physicist who embraced paradox and deep questioning",
  "Travis Kalanick": "Startup founder known for aggressive execution and risk-taking",
};

const PAIN_POINTS = [
  "procrastination",
  "perfectionism",
  "burnout",
  "test anxiety",
  "time management",
  "motivation issues",
  "imposter syndrome",
  "information overload",
  "distractions",
  "lack of focus",
];

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState<Partial<RegisterData>>({
    user_id: '',
    name: '',
    primary_persona: '',
    preferred_personas: [],
    academic_field: '',
    study_topics: [],
    goals: [],
    traits: [],
  });

  const [customPersona, setCustomPersona] = useState('');
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([]);
  const [selectedTraits, setSelectedTraits] = useState<string[]>([]);
  const [topicInput, setTopicInput] = useState('');
  const [goalInput, setGoalInput] = useState('');

  const handlePersonaSelect = (persona: string) => {
    if (selectedPersonas.includes(persona)) {
      setSelectedPersonas(selectedPersonas.filter(p => p !== persona));
    } else {
      setSelectedPersonas([...selectedPersonas, persona]);
    }
  };

  const handleTraitSelect = (trait: string) => {
    if (selectedTraits.includes(trait)) {
      setSelectedTraits(selectedTraits.filter(t => t !== trait));
    } else {
      setSelectedTraits([...selectedTraits, trait]);
    }
  };

  const addTopic = () => {
    if (topicInput.trim() && formData.study_topics!.length < 10) {
      setFormData({
        ...formData,
        study_topics: [...(formData.study_topics || []), topicInput.trim()],
      });
      setTopicInput('');
    }
  };

  const removeTopic = (index: number) => {
    setFormData({
      ...formData,
      study_topics: formData.study_topics!.filter((_, i) => i !== index),
    });
  };

  const addGoal = () => {
    if (goalInput.trim() && formData.goals!.length < 10) {
      setFormData({
        ...formData,
        goals: [...(formData.goals || []), goalInput.trim()],
      });
      setGoalInput('');
    }
  };

  const removeGoal = (index: number) => {
    setFormData({
      ...formData,
      goals: formData.goals!.filter((_, i) => i !== index),
    });
  };

  const handleNext = () => {
    if (step === 1 && (!formData.user_id || !formData.name)) {
      setError('Please fill in all required fields');
      return;
    }
    if (step === 2 && selectedPersonas.length === 0 && !customPersona) {
      setError('Please select or create at least one persona');
      return;
    }
    setError('');
    setStep(step + 1);
  };

  const handleBack = () => {
    setError('');
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      const finalPersonas = customPersona
        ? [customPersona, ...selectedPersonas]
        : selectedPersonas;

      const registerData: RegisterData = {
        user_id: formData.user_id!,
        name: formData.name!,
        primary_persona: finalPersonas[0] || 'motivational coach',
        preferred_personas: finalPersonas,
        academic_field: formData.academic_field || undefined,
        study_topics: formData.study_topics || [],
        goals: formData.goals || [],
        traits: selectedTraits,
      };

      await apiClient.register(registerData);
      router.push(`/chat?userId=${formData.user_id}`);
    } catch (err: any) {
      const isNetworkError =
        err.code === 'ECONNREFUSED' ||
        err.code === 'ETIMEDOUT' ||
        err.code === 'ERR_NETWORK' ||
        err.message?.includes('timeout');
      setError(
        isNetworkError
          ? 'Backend not reachable. Make sure the API is running (./start_dev.sh).'
          : err.response?.data?.detail || 'Registration failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0a0a0a] py-12 px-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Create Your Account
          </h1>
          <p className="text-gray-400">Step {step} of 4</p>
        </div>

        <div className="bg-[#1a1a1a] border border-gray-800 rounded-2xl p-8 shadow-2xl">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between mb-2">
              {[1, 2, 3, 4].map((s) => (
                <div
                  key={s}
                  className={`h-2 flex-1 mx-1 rounded-full ${
                    s <= step ? 'bg-blue-600' : 'bg-gray-700'
                  }`}
                />
              ))}
            </div>
          </div>

          {error && (
            <div className="mb-6 p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Basic Information</h2>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  User ID <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.user_id}
                  onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                  placeholder="Choose a unique user ID"
                  className="w-full px-4 py-3 bg-[#0a0a0a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Your full name"
                  className="w-full px-4 py-3 bg-[#0a0a0a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {/* Step 2: Persona */}
          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Choose Your Motivational Guide</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                {Object.entries(PERSONAS).map(([persona, desc]) => (
                  <button
                    key={persona}
                    onClick={() => handlePersonaSelect(persona)}
                    className={`p-4 text-left border rounded-lg transition-all ${
                      selectedPersonas.includes(persona)
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="font-medium text-white mb-1">{persona}</div>
                    <div className="text-sm text-gray-400">{desc}</div>
                  </button>
                ))}
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Or create custom persona
                </label>
                <input
                  type="text"
                  value={customPersona}
                  onChange={(e) => setCustomPersona(e.target.value)}
                  placeholder="e.g., Marcus Aurelius, Bruce Lee"
                  className="w-full px-4 py-3 bg-[#0a0a0a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {/* Step 3: Academic Info */}
          {step === 3 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Academic Information</h2>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Academic Field
                </label>
                <input
                  type="text"
                  value={formData.academic_field}
                  onChange={(e) => setFormData({ ...formData, academic_field: e.target.value })}
                  placeholder="e.g., Computer Science, Mathematics"
                  className="w-full px-4 py-3 bg-[#0a0a0a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Study Topics
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={topicInput}
                    onChange={(e) => setTopicInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTopic())}
                    placeholder="Add a topic"
                    className="flex-1 px-4 py-2 bg-[#0a0a0a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    onClick={addTopic}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.study_topics?.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-500/20 border border-blue-500 rounded-full text-sm text-blue-300 flex items-center gap-2"
                    >
                      {topic}
                      <button
                        onClick={() => removeTopic(idx)}
                        className="text-blue-400 hover:text-blue-300"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Goals & Challenges */}
          {step === 4 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-6">Goals & Challenges</h2>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Learning Goals
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={goalInput}
                    onChange={(e) => setGoalInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addGoal())}
                    placeholder="e.g., Pass calculus exam, Master Python"
                    className="flex-1 px-4 py-2 bg-[#0a0a0a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    onClick={addGoal}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2 mb-6">
                  {formData.goals?.map((goal, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-purple-500/20 border border-purple-500 rounded-full text-sm text-purple-300 flex items-center gap-2"
                    >
                      {goal}
                      <button
                        onClick={() => removeGoal(idx)}
                        className="text-purple-400 hover:text-purple-300"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Challenges You Face
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {PAIN_POINTS.map((trait) => (
                    <button
                      key={trait}
                      onClick={() => handleTraitSelect(trait)}
                      className={`p-3 text-sm border rounded-lg transition-all ${
                        selectedTraits.includes(trait)
                          ? 'border-purple-500 bg-purple-500/10 text-purple-300'
                          : 'border-gray-700 hover:border-gray-600 text-gray-300'
                      }`}
                    >
                      {trait}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            <button
              onClick={handleBack}
              disabled={step === 1}
              className="px-6 py-3 border border-gray-700 hover:border-gray-600 rounded-lg text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>
            {step < 4 ? (
              <button
                onClick={handleNext}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg text-white"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg text-white disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Account'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}



