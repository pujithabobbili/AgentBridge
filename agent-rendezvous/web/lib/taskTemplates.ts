export type TaskCategory = 'NLP' | 'Extraction' | 'Vision';

export interface TaskTemplate {
  id: string;
  name: string;
  description: string;
  goal: string;
  sampleInputs: Record<string, any>;
  defaultBudget: number;
  defaultSLA: number;
  category: TaskCategory;
}

export const taskTemplates: TaskTemplate[] = [
  {
    id: 'extract_event',
    name: 'Extract Event Information',
    description: 'Extract event details (title, date, time, location) from text or images',
    goal: 'extract_event',
    sampleInputs: {
      text: 'Global Scoop AI Hackathon\n\nNov 22–23, 2025 8:30 AM – 5:30 PM\n\nSanta Clara'
    },
    defaultBudget: 0.1,
    defaultSLA: 5000,
    category: 'Extraction'
  },
  {
    id: 'analyze_sentiment',
    name: 'Analyze Sentiment',
    description: 'Determine the emotional tone (positive, negative, neutral) of text',
    goal: 'analyze_sentiment',
    sampleInputs: {
      text: 'I absolutely loved the product! The quality is outstanding and the customer service was exceptional. Highly recommended!'
    },
    defaultBudget: 0.05,
    defaultSLA: 3000,
    category: 'NLP'
  },
  {
    id: 'summarize_text',
    name: 'Summarize Text',
    description: 'Create a concise summary of long-form content',
    goal: 'summarize_text',
    sampleInputs: {
      text: 'Artificial Intelligence has revolutionized many industries. Machine learning algorithms can now process vast amounts of data and make predictions with remarkable accuracy. Deep learning, a subset of machine learning, uses neural networks with multiple layers to learn complex patterns. These technologies are being applied in healthcare, finance, transportation, and many other sectors to improve efficiency and decision-making.'
    },
    defaultBudget: 0.08,
    defaultSLA: 4000,
    category: 'NLP'
  },
  {
    id: 'extract_contact_info',
    name: 'Extract Contact Information',
    description: 'Extract names, emails, phone numbers, and addresses from text',
    goal: 'extract_contact_info',
    sampleInputs: {
      text: 'John Doe\nEmail: john.doe@example.com\nPhone: (555) 123-4567\nAddress: 123 Main St, San Francisco, CA 94102'
    },
    defaultBudget: 0.06,
    defaultSLA: 3000,
    category: 'Extraction'
  },
  {
    id: 'parse_invoice',
    name: 'Parse Invoice',
    description: 'Extract structured data from invoice documents',
    goal: 'parse_invoice',
    sampleInputs: {
      text: 'INVOICE #12345\nDate: January 15, 2025\nBill To: Acme Corp\n123 Business St\nItems:\n- Service A: $500.00\n- Service B: $300.00\nTotal: $800.00'
    },
    defaultBudget: 0.1,
    defaultSLA: 5000,
    category: 'Vision'
  },
  {
    id: 'extract_keywords',
    name: 'Extract Keywords',
    description: 'Identify key terms and phrases from text content',
    goal: 'extract_keywords',
    sampleInputs: {
      text: 'Machine learning and artificial intelligence are transforming the technology landscape. Deep neural networks enable computers to recognize patterns and make intelligent decisions.'
    },
    defaultBudget: 0.04,
    defaultSLA: 2000,
    category: 'Extraction'
  },
  {
    id: 'classify_text',
    name: 'Classify Text',
    description: 'Categorize text into predefined categories or topics',
    goal: 'classify_text',
    sampleInputs: {
      text: 'The stock market experienced significant volatility today as tech companies reported mixed earnings results. Analysts suggest a cautious approach for investors.'
    },
    defaultBudget: 0.05,
    defaultSLA: 3000,
    category: 'NLP'
  },
  {
    id: 'translate_text',
    name: 'Translate Text',
    description: 'Translate text from one language to another',
    goal: 'translate_text',
    sampleInputs: {
      text: 'Hello, how are you today?',
      targetLanguage: 'Spanish'
    },
    defaultBudget: 0.03,
    defaultSLA: 2500,
    category: 'NLP'
  }
];

export function getTemplateById(id: string): TaskTemplate | undefined {
  return taskTemplates.find(t => t.id === id);
}



