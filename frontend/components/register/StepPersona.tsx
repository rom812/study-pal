interface StepPersonaProps {
    selectedPersonas: string[];
    handlePersonaSelect: (persona: string) => void;
    customPersona: string;
    setCustomPersona: (persona: string) => void;
    PERSONAS: Record<string, string>;
}

export function StepPersona({
    selectedPersonas,
    handlePersonaSelect,
    customPersona,
    setCustomPersona,
    PERSONAS,
}: StepPersonaProps) {
    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-semibold mb-6">Choose Your Motivational Guide</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                {Object.entries(PERSONAS).map(([persona, desc]) => (
                    <button
                        key={persona}
                        onClick={() => handlePersonaSelect(persona)}
                        className={`p-4 text-left border rounded-lg transition-all ${selectedPersonas.includes(persona)
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
    );
}
