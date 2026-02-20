import { RefObject } from 'react';
import { AGENT_NAMES } from '@/types';
import { useRouter } from 'next/navigation';

interface ChatHeaderProps {
    currentAgent: string | null;
    uploading: boolean;
    fileInputRef: RefObject<HTMLInputElement>;
    handleFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function ChatHeader({
    currentAgent,
    uploading,
    fileInputRef,
    handleFileUpload,
}: ChatHeaderProps) {
    const router = useRouter();

    return (
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
    );
}
