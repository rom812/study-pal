import { FormEvent } from 'react';

interface ChatInputProps {
    input: string;
    setInput: (value: string) => void;
    loading: boolean;
    handleSend: (e: FormEvent) => void;
}

export function ChatInput({ input, setInput, loading, handleSend }: ChatInputProps) {
    return (
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
    );
}
