import api from './api';

export type CopilotMode = 'quick_summary' | 'deep_analysis' | 'governance_check' | 'troubleshooting';

export interface CopilotPageContext {
  page: string;
  prediction_id?: number;
  round_number?: number;
  dataset_id?: number;
  model_id?: number;
}

export interface CopilotChatRequest {
  message: string;
  mode: CopilotMode;
  page_context: CopilotPageContext;
}

export interface CopilotReferenceLink {
  label: string;
  url: string;
}

export interface CopilotChatResponse {
  answer: string;
  mode: string;
  role: string;
  context_used: Record<string, unknown>;
  links: CopilotReferenceLink[];
  recommendations: string[];
  guardrails: string[];
}

export class CopilotService {
  static async chat(payload: CopilotChatRequest): Promise<CopilotChatResponse> {
    const response = await api.post<CopilotChatResponse>('/api/copilot/chat', payload, {
      timeout: 20000,
    });
    return response.data;
  }
}
