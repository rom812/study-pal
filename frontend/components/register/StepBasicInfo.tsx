import { RegisterData } from '@/lib/api';

interface StepBasicInfoProps {
    formData: Partial<RegisterData>;
    setFormData: (data: Partial<RegisterData>) => void;
}

export function StepBasicInfo({ formData, setFormData }: StepBasicInfoProps) {
    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-semibold mb-6">Basic Information</h2>
            <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                    User ID <span className="text-red-400">*</span>
                </label>
                <input
                    type="text"
                    value={formData.user_id || ''}
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
                    value={formData.name || ''}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Your full name"
                    className="w-full px-4 py-3 bg-[#0a0a0a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div>
        </div>
    );
}
