import { Message } from '@/types';
import { MessageBubble } from './MessageBubble';
import { RefObject } from 'react';

interface MessageListProps {
    messages: Message[];
    loading: boolean;
    messagesEndRef: RefObject<HTMLDivElement>;
}

export function MessageList({ messages, loading, messagesEndRef }: MessageListProps) {
    return (
        <div className="flex-1 overflow-y-auto max-w-6xl w-full mx-auto px-4 py-8">
            {messages.length === 0 && (
                <div className="text-center mt-20">
                    <div className="text-6xl mb-4">🎓</div>
                    <h2 className="text-2xl font-semibold mb-2 text-gray-300">Welcome to Study Pal!</h2>
                    <p className="text-gray-500">
                        Ask me anything about your studies, or upload a PDF to get started.
                    </p>
                </div>
            )}

            <div className="space-y-6">
                {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                ))}

                {loading && (
                    <div className="flex gap-4 justify-start">
                        <div className="flex-shrink-0">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl">
                                🤖
                            </div>
                        </div>
                        <div className="bg-[#1a1a1a] border border-gray-800 rounded-2xl px-6 py-4">
                            <div className="flex gap-2">
                                <div
                                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                    style={{ animationDelay: '0ms' }}
                                ></div>
                                <div
                                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                    style={{ animationDelay: '150ms' }}
                                ></div>
                                <div
                                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                    style={{ animationDelay: '300ms' }}
                                ></div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            <div ref={messagesEndRef} />
        </div>
    );
}
