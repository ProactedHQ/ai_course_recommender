import { usePromptHistory as useHistoryContext } from '../context/PromptHistoryContext';

export function usePromptHistory() {
    return useHistoryContext();
}
