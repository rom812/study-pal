export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    agentAvatar?: string;
    agentName?: string;
}

export const AGENT_NAMES = {
    tutor: "Tutor",
    scheduler: "Scheduler",
    analyzer: "Analyzer",
    motivator: "Motivator",
    unknown: "System",
};
