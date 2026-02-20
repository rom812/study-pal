import { Message } from '@/types';

interface MessageBubbleProps {
    message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
            {/* Assistant Avatar */}
            {!isUser && (
                <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl">
                        {message.agentAvatar || '🤖'}
                    </div>
                </div>
            )}

            {/* Message Content */}
            <div
                className={`max-w-[80%] rounded-2xl px-6 py-4 ${isUser
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                        : 'bg-[#1a1a1a] border border-gray-800 text-gray-100'
                    }`}
            >
                <div className="whitespace-pre-wrap break-words">{message.content}</div>
                {!isUser && message.agentName && (
                    <div className="mt-2 text-xs text-gray-500">
                        {message.agentName}
                    </div>
                )}
            </div>

            {/* User Avatar */}
            {isUser && (
                <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-2xl">
                        👤
                    </div>
                </div>
            )}
        </div>
    );
}
