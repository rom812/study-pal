'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, RegisterData } from '@/lib/api';
import { StepBasicInfo } from '@/components/register/StepBasicInfo';
import { StepPersona } from '@/components/register/StepPersona';
import { StepAcademic } from '@/components/register/StepAcademic';
import { StepGoals } from '@/components/register/StepGoals';

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
          ? 'Backend not reachable. Make sure the API is running (./scripts/start_dev.sh).'
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
                  className={`h-2 flex-1 mx-1 rounded-full ${s <= step ? 'bg-blue-600' : 'bg-gray-700'
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

          {/* Steps */}
          {step === 1 && (
            <StepBasicInfo formData={formData} setFormData={setFormData} />
          )}

          {step === 2 && (
            <StepPersona
              selectedPersonas={selectedPersonas}
              handlePersonaSelect={handlePersonaSelect}
              customPersona={customPersona}
              setCustomPersona={setCustomPersona}
              PERSONAS={PERSONAS}
            />
          )}

          {step === 3 && (
            <StepAcademic
              formData={formData}
              setFormData={setFormData}
              topicInput={topicInput}
              setTopicInput={setTopicInput}
              addTopic={addTopic}
              removeTopic={removeTopic}
            />
          )}

          {step === 4 && (
            <StepGoals
              formData={formData}
              setFormData={setFormData}
              goalInput={goalInput}
              setGoalInput={setGoalInput}
              addGoal={addGoal}
              removeGoal={removeGoal}
              PAIN_POINTS={PAIN_POINTS}
              selectedTraits={selectedTraits}
              handleTraitSelect={handleTraitSelect}
            />
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
