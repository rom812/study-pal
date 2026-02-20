import { RegisterData } from '@/lib/api';

interface StepAcademicProps {
    formData: Partial<RegisterData>;
    setFormData: (data: Partial<RegisterData>) => void;
    topicInput: string;
    setTopicInput: (value: string) => void;
    addTopic: () => void;
    removeTopic: (index: number) => void;
}

export function StepAcademic({
    formData,
    setFormData,
    topicInput,
    setTopicInput,
    addTopic,
    removeTopic,
}: StepAcademicProps) {
    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-semibold mb-6">Academic Information</h2>
            <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                    Academic Field
                </label>
                <input
                    type="text"
                    value={formData.academic_field || ''}
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
    );
}
