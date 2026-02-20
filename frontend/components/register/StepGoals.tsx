import { RegisterData } from '@/lib/api';

interface StepGoalsProps {
    formData: Partial<RegisterData>;
    setFormData: (data: Partial<RegisterData>) => void;
    goalInput: string;
    setGoalInput: (value: string) => void;
    addGoal: () => void;
    removeGoal: (index: number) => void;
    PAIN_POINTS: string[];
    selectedTraits: string[];
    handleTraitSelect: (trait: string) => void;
}

export function StepGoals({
    formData,
    setFormData,
    goalInput,
    setGoalInput,
    addGoal,
    removeGoal,
    PAIN_POINTS,
    selectedTraits,
    handleTraitSelect,
}: StepGoalsProps) {
    return (
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
                            className={`p-3 text-sm border rounded-lg transition-all ${selectedTraits.includes(trait)
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
    );
}
