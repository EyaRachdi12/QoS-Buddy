"""
Agent 1: RAG-Powered Chatbot Advisor
Uses ChromaDB + Google Gemini for telecom network diagnostics

Refinements v2:
- Conversation memory (sliding window of last N turns)
- Intent classification before RAG
- Adaptive chunk retrieval (query complexity)
- Cell-specific context injection
- Response confidence score from ChromaDB distances
"""

import os
import re
from collections import deque
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import json
import warnings
import requests
import pandas as pd
from datetime import datetime, timedelta

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

load_dotenv()

from core.filled_transform import apply_filled_column_mapping, finalize_pipeline_dataframe


# ── Intent Classification ──

class QueryIntent:
    DATA_QUERY = "data_query"         # user asks about their dataset / statistics
    CELL_DIAGNOSTIC = "cell_diagnostic"  # user asks about a specific cell
    ISSUE_DIAGNOSTIC = "issue_diagnostic"  # user asks about a network problem type
    COMPARISON = "comparison"         # user compares KPIs, cells, time periods
    GENERAL_KNOWLEDGE = "general_knowledge"  # general telecom question
    HOWTO = "howto"                    # how to fix / optimize something


_INTENT_PATTERNS = [
    (QueryIntent.CELL_DIAGNOSTIC, [
        r'\bcell[_ ]?\w{2,}', r'\bsite[_ ]\w+', r'\bcell_id\b', r'\bspecific cell\b',
        r'\bthis cell\b', r'\bthat cell\b', r'\bcell \w+\b',
    ]),
    (QueryIntent.DATA_QUERY, [
        r'\bmy data\b', r'\bdataset\b', r'\bhow many\b', r'\bstatistics\b',
        r'\bshow me\b', r'\bsample\b', r'\brows?\b', r'\bdistribution\b',
        r'\bcurrent network\b', r'\bcells?\b.*\bmonitored\b',
    ]),
    (QueryIntent.COMPARISON, [
        r'\bcompare\b', r'\bvs\.?\b', r'\bbetter\b.*\bworse\b',
        r'\bdifference\b', r'\btrend\b', r'\bover time\b',
    ]),
    (QueryIntent.HOWTO, [
        r'\bhow to\b', r'\bhow do i\b', r'\bfix\b', r'\boptimize\b',
        r'\bimprove\b', r'\breduce\b', r'\bincrease\b', r'\bwhat should\b',
    ]),
    (QueryIntent.ISSUE_DIAGNOSTIC, [
        r'\bcall drop\b', r'\bhandover\b', r'\blatency\b', r'\bthroughput\b',
        r'\bmos\b', r'\bcongestion\b', r'\bprb\b', r'\bbler\b', r'\brsrp\b',
        r'\bsinr\b', r'\bsla\b', r'\banomaly\b', r'\bcapacity\b',
    ]),
]


def classify_intent(query: str) -> str:
    """Rule-based intent classification. Returns the most specific matching intent."""
    q = query.lower()
    for intent, patterns in _INTENT_PATTERNS:
        for pat in patterns:
            if re.search(pat, q):
                return intent
    return QueryIntent.GENERAL_KNOWLEDGE


def _extract_cell_id(query: str) -> Optional[str]:
    """Try to extract a cell_id from a user query."""
    m = re.search(r'\b(cell[_ ]?\w{3,})\b', query, re.IGNORECASE)
    if m:
        return m.group(1).replace(' ', '_')
    m = re.search(r'\b([A-Z]{2,4}[_-]\d{3,})\b', query)
    if m:
        return m.group(1)
    return None


class TelecomAdvisorAgent:
    """
    Agent 1: Chatbot Advisor
    Answers telecom diagnostic questions using RAG
    """

    # Maximum conversation turns to remember per conversation
    MEMORY_WINDOW = 6

    def __init__(self, knowledge_base_path: str = None, data_path: str = None):
        repo_root = Path(__file__).resolve().parent.parent
        default_kb = repo_root / "knowledge_base" / "telecom_causes_solutions.txt"
        default_filled = Path(__file__).resolve().parent / "unified_telecom_dataset_FILLED.csv"

        self.knowledge_base_path = str(knowledge_base_path) if knowledge_base_path else str(default_kb)
        self.data_path = str(data_path) if data_path else str(default_filled)
        self.collection_name = "telecom_knowledge"
        self.df = None

        self.chroma_client = chromadb.Client(Settings(
            persist_directory=str(repo_root / "data" / "chroma_db"),
            anonymized_telemetry=False
        ))

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Check for OpenRouter API key (preferred)
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        gemini_api_key = os.getenv('GEMINI_API_KEY')

        if openrouter_api_key:
            self.api_key = openrouter_api_key
            self.api_type = 'openrouter'
            self.model_name = 'openai/gpt-4o-mini'
            self.api_url = 'https://openrouter.ai/api/v1/chat/completions'
            print(f"  OpenRouter API configured ({self.model_name})")
        elif gemini_api_key:
            self.api_key = gemini_api_key
            self.api_type = 'gemini'
            self.model_name = 'gemini-1.5-flash'
            self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent'
            print("  Gemini API configured (gemini-1.5-flash)")
        else:
            self.api_key = None
            self.api_type = None
            self.model_name = None
            print("  No API key found. Set OPENROUTER_API_KEY or GEMINI_API_KEY in .env file")

        self.collection = None
        self.is_initialized = False
        self._insights_provider = None
        self._diagnostic_provider = None  # Agent 2 feeds live diagnostics

        # Conversation memory: conversation_id -> deque of (role, text) tuples
        self._conversations: Dict[str, deque] = {}

        self.load_network_data()

    def set_insights_provider(self, fn):
        """Callable returning a short string of live KPI / ML snapshot for RAG context."""
        self._insights_provider = fn

    def set_diagnostic_provider(self, fn):
        """Callable(cell_id=None) returning live diagnostic context from Agent 2."""
        self._diagnostic_provider = fn

    # ── Conversation Memory ──

    def _get_memory(self, conversation_id: Optional[str]) -> deque:
        cid = conversation_id or "__default__"
        if cid not in self._conversations:
            self._conversations[cid] = deque(maxlen=self.MEMORY_WINDOW * 2)
        return self._conversations[cid]

    def _add_to_memory(self, conversation_id: Optional[str], role: str, text: str):
        mem = self._get_memory(conversation_id)
        mem.append((role, text[:500]))  # truncate to save context space

    def _format_memory(self, conversation_id: Optional[str]) -> str:
        mem = self._get_memory(conversation_id)
        if not mem:
            return ""
        lines = []
        for role, text in mem:
            prefix = "User" if role == "user" else "Assistant"
            lines.append(f"{prefix}: {text}")
        return "\n".join(lines)

    # ── Data Loading ──

    def load_network_data(self):
        """Load the actual network KPI dataset"""
        try:
            df = pd.read_csv(self.data_path)
            filled_cols = set(df.columns)
            is_filled = (
                "risk_tier" in filled_cols
                or "RSRP_dBm" in filled_cols
                or "signal_strength_dbm" in filled_cols
            )
            if is_filled:
                df = self._transform_filled_dataset(df)
            else:
                df = df.copy()
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            self.df = df
            n_cells = self.df["cell_id"].nunique() if "cell_id" in self.df.columns else 0
            print(f"  Loaded network data: {len(self.df)} records from {n_cells} cells")
        except Exception as e:
            print(f"  Could not load network data: {e}")
            self.df = None

    def _transform_filled_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        df = apply_filled_column_mapping(df)
        out = finalize_pipeline_dataframe(df)
        return out.sort_values("timestamp").reset_index(drop=True)

    # ── Cell-Specific Context ──

    def _get_cell_context(self, cell_id: str) -> str:
        """Pull live KPIs for a specific cell from the dataset + Agent 2 diagnostics."""
        parts = []

        # From local dataset
        if self.df is not None and "cell_id" in self.df.columns:
            cell_data = self.df[self.df["cell_id"] == cell_id]
            if not cell_data.empty:
                latest = cell_data.iloc[-1]
                kpi_cols = ["RSRP", "SINR", "PRB_DL", "PRB_UL", "throughput_DL",
                            "latency_ms", "MOS", "handover_success_rate"]
                kpis = {c: float(latest[c]) for c in kpi_cols if c in latest and pd.notna(latest[c])}
                parts.append(f"CELL {cell_id} LIVE KPIs: {json.dumps(kpis, indent=2)}")

                # Recent history (last 10 records)
                recent = cell_data.tail(10)
                if "issue_type" in recent.columns:
                    issues = recent["issue_type"].value_counts().to_dict()
                    parts.append(f"Recent issues on this cell: {issues}")
                if "severity" in recent.columns:
                    sevs = recent["severity"].value_counts().to_dict()
                    parts.append(f"Severity distribution: {sevs}")

        # From Agent 2 live diagnostics
        if self._diagnostic_provider:
            try:
                diag = self._diagnostic_provider(cell_id=cell_id)
                if diag:
                    parts.append(f"AGENT 2 DIAGNOSTICS: {diag}")
            except Exception:
                pass

        return "\n".join(parts) if parts else ""

    # ── Dataset Analysis ──

    def get_dataset_sample(self, n: int = 10, issue_type: str = None) -> str:
        if self.df is None:
            return ""
        if issue_type:
            sample_df = self.df[self.df['issue_type'] == issue_type].head(n)
        else:
            sample_df = self.df.tail(n)
        display_cols = ['timestamp', 'cell_id', 'RSRP', 'SINR', 'PRB_DL', 'throughput_DL',
                        'latency_ms', 'MOS', 'call_drop_rate', 'issue_type', 'severity']
        display_cols = [c for c in display_cols if c in sample_df.columns]
        sample_df = sample_df[display_cols]
        result = f"\nSAMPLE DATA ({len(sample_df)} rows):\n"
        result += sample_df.to_string(index=False)
        return result

    def analyze_dataset(self) -> str:
        if self.df is None:
            return "No dataset available for analysis."
        total_records = len(self.df)
        num_cells = self.df['cell_id'].nunique()
        date_range = f"{self.df['timestamp'].min()} to {self.df['timestamp'].max()}"
        issue_dist = self.df['issue_type'].value_counts().to_dict() if 'issue_type' in self.df.columns else {}
        severity_dist = self.df['severity'].value_counts().to_dict() if 'severity' in self.df.columns else {}
        latest_time = self.df['timestamp'].max()
        cutoff_time = latest_time - timedelta(hours=24)
        recent_df = self.df[self.df['timestamp'] >= cutoff_time]
        recent_issues = recent_df[recent_df.get('issue_type', pd.Series()) != 'Normal'] if 'issue_type' in recent_df.columns else recent_df.head(0)
        problem_df = self.df[self.df['severity'].isin(['CRITICAL', 'HIGH'])] if 'severity' in self.df.columns else self.df.head(0)
        problem_cells = problem_df['cell_id'].unique() if not problem_df.empty else []

        analysis = f"""DATASET ANALYSIS:
Total Records: {total_records:,}
Cells Monitored: {num_cells}
Date Range: {date_range}

ISSUE DISTRIBUTION:
{json.dumps(issue_dist, indent=2)}

SEVERITY BREAKDOWN:
{json.dumps(severity_dist, indent=2)}

RECENT 24H ISSUES: {len(recent_issues)} problems detected
- Critical: {len(recent_df[recent_df['severity'] == 'CRITICAL']) if 'severity' in recent_df.columns else 0}
- High: {len(recent_df[recent_df['severity'] == 'HIGH']) if 'severity' in recent_df.columns else 0}
- Medium: {len(recent_df[recent_df['severity'] == 'MEDIUM']) if 'severity' in recent_df.columns else 0}

CELLS WITH CRITICAL/HIGH ISSUES: {len(problem_cells)} cells
"""
        if len(problem_cells) > 0:
            analysis += f"Top problem cells: {', '.join(list(problem_cells)[:5])}\n"
        if not problem_df.empty:
            analysis += f"""
AVERAGE KPIs (Problem Records):
- RSRP: {problem_df['RSRP'].mean():.1f} dBm
- SINR: {problem_df['SINR'].mean():.1f} dB
- PRB_DL: {problem_df['PRB_DL'].mean():.1f}%
- Latency: {problem_df['latency_ms'].mean():.1f} ms
- MOS: {problem_df['MOS'].mean():.2f}
"""
        return analysis

    # ── Vector DB ──

    def load_knowledge_base(self) -> str:
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"  Loaded knowledge base: {len(content)} characters")
            return content
        except FileNotFoundError:
            print(f"  Knowledge base not found: {self.knowledge_base_path}")
            return ""

    def chunk_documents(self, text: str) -> List[Dict[str, str]]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        documents = []
        for idx, chunk in enumerate(chunks):
            documents.append({
                'id': f'chunk_{idx}',
                'text': chunk,
                'metadata': {'chunk_id': idx, 'source': 'knowledge_base'}
            })
        print(f"  Created {len(documents)} chunks")
        return documents

    def initialize_vector_db(self):
        print("\nInitializing vector database...")
        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
            print(f"  Using existing collection: {self.collection_name}")
            self.is_initialized = True
            return
        except (ValueError, chromadb.errors.NotFoundError):
            pass
        except Exception as e:
            print(f"  Collection lookup failed, recreating: {e}")

        knowledge_text = self.load_knowledge_base()
        if not knowledge_text:
            print("  Cannot initialize without knowledge base")
            return

        documents = self.chunk_documents(knowledge_text)
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "Telecom network diagnostics knowledge base"}
        )
        texts = [doc['text'] for doc in documents]
        ids = [doc['id'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        embeddings_list = self.embeddings.embed_documents(texts)
        self.collection.add(
            embeddings=embeddings_list,
            documents=texts,
            ids=ids,
            metadatas=metadatas
        )
        print(f"  ChromaDB initialized with {len(documents)} chunks")
        self.is_initialized = True

    # ── Adaptive Retrieval ──

    def get_relevant_context(self, query: str, intent: str) -> Tuple[List[str], float]:
        """
        Retrieve relevant context with adaptive top_k based on intent/complexity.
        Returns (context_chunks, confidence_score).
        """
        if not self.is_initialized:
            return [], 0.0

        # Adaptive top_k: broad questions get more chunks
        if intent in (QueryIntent.GENERAL_KNOWLEDGE, QueryIntent.COMPARISON):
            top_k = 5
        elif intent == QueryIntent.DATA_QUERY:
            top_k = 2  # data queries rely on dataset, not KB
        else:
            top_k = 3

        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances"],
        )

        if not results or not results['documents']:
            return [], 0.0

        docs = results['documents'][0]
        distances = results['distances'][0] if results.get('distances') else []

        # Confidence: ChromaDB returns L2 distances. Lower = more similar.
        # Map to 0-1 confidence score. Typical good match < 1.0, poor > 1.5
        if distances:
            avg_dist = sum(distances) / len(distances)
            confidence = max(0.0, min(1.0, 1.0 - (avg_dist - 0.3) / 1.2))
        else:
            confidence = 0.5

        return docs, round(confidence, 3)

    # ── Response Generation ──

    def generate_response(
        self,
        query: str,
        context: List[str],
        intent: str,
        cell_context: str = "",
        live_insights: str = "",
        conversation_history: str = "",
    ) -> str:
        if not self.api_key:
            return "Error: No API key configured. Please add OPENROUTER_API_KEY or GEMINI_API_KEY to .env file."

        context_text = "\n\n".join(context)

        # Intent-driven dataset injection
        dataset_context = ""
        if intent == QueryIntent.DATA_QUERY and self.df is not None:
            dataset_context = f"\n\nACTUAL NETWORK DATA ANALYSIS:\n{self.analyze_dataset()}\n"
            if any(w in query.lower() for w in ['top', 'rows', 'sample', 'show', 'display']):
                dataset_context += f"\n{self.get_dataset_sample(n=10)}\n"

        cell_block = ""
        if cell_context:
            cell_block = f"\n\nCELL-SPECIFIC DATA:\n{cell_context}\n"

        insights_block = ""
        if live_insights:
            insights_block = f"\n\nLIVE SYSTEM INSIGHTS:\n{live_insights}\n"

        history_block = ""
        if conversation_history:
            history_block = f"\n\nCONVERSATION HISTORY (for follow-up context):\n{conversation_history}\n"

        system_prompt = """You are an expert telecom network engineer assistant specializing in 4G/5G network diagnostics and optimization. You have access to telecom knowledge, actual network data, and live diagnostic results from monitoring agents.

When cell-specific data is provided, use it to give precise answers about that cell.
When conversation history is provided, use it to understand follow-up questions and maintain context."""

        user_prompt = f"""CONTEXT FROM KNOWLEDGE BASE:
{context_text}
{dataset_context}{cell_block}{insights_block}{history_block}
USER QUESTION:
{query}

INSTRUCTIONS:
1. Use the provided context to answer the question accurately
2. If cell-specific data is provided, reference the actual KPI values
3. If asked about data/dataset, use the ACTUAL NETWORK DATA ANALYSIS section
4. If the question is about network issues, identify:
   - The root causes
   - The relevant KPI thresholds
   - Specific actionable solutions
5. Be concise but thorough
6. If multiple solutions exist, prioritize them (quick wins first, then infrastructure changes)
7. Use technical terminology but explain when necessary
8. If this is a follow-up question, use conversation history for context
9. If the context doesn't contain the answer, say so clearly

ANSWER:"""

        try:
            if self.api_type == 'openrouter':
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'http://localhost:5173',
                    'X-Title': 'QoS Buddy'
                }
                data = {
                    'model': self.model_name,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
                response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']

            else:
                headers = {'Content-Type': 'application/json'}
                data = {
                    'contents': [{
                        'parts': [{'text': f"{system_prompt}\n\n{user_prompt}"}]
                    }]
                }
                url = f'{self.api_url}?key={self.api_key}'
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                return response.json()['candidates'][0]['content']['parts'][0]['text']

        except requests.exceptions.HTTPError as e:
            return f"HTTP Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error generating response: {str(e)}"

    # ── Main Query Pipeline ──

    def query(
        self,
        user_question: str,
        include_live_insights: bool = True,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Main query method — enhanced RAG pipeline with:
        - Intent classification
        - Conversation memory
        - Cell-specific context
        - Adaptive retrieval
        - Confidence scoring
        """
        if not self.is_initialized:
            self.initialize_vector_db()

        # 1. Classify intent
        intent = classify_intent(user_question)

        # 2. Adaptive retrieval + confidence
        relevant_context, confidence = self.get_relevant_context(user_question, intent)

        if not relevant_context and intent not in (QueryIntent.DATA_QUERY, QueryIntent.CELL_DIAGNOSTIC):
            return {
                'question': user_question,
                'answer': "I don't have enough information to answer this question. Please check the knowledge base.",
                'context': [],
                'success': False,
                'intent': intent,
                'confidence': 0.0,
            }

        # 3. Cell-specific context injection
        cell_context = ""
        cell_id = _extract_cell_id(user_question)
        if cell_id or intent == QueryIntent.CELL_DIAGNOSTIC:
            if cell_id:
                cell_context = self._get_cell_context(cell_id)

        # 4. Live insights from orchestrator
        live = ""
        if include_live_insights and self._insights_provider:
            try:
                live = self._insights_provider()
            except Exception:
                live = ""

        # 5. Conversation history
        history = self._format_memory(conversation_id)

        # 6. Generate response
        answer = self.generate_response(
            user_question,
            relevant_context,
            intent=intent,
            cell_context=cell_context,
            live_insights=live,
            conversation_history=history,
        )

        # 7. Update conversation memory
        self._add_to_memory(conversation_id, "user", user_question)
        self._add_to_memory(conversation_id, "assistant", answer)

        return {
            'question': user_question,
            'answer': answer,
            'context': relevant_context,
            'success': True,
            'intent': intent,
            'confidence': confidence,
        }

    def chat(self, user_input: str) -> str:
        result = self.query(user_input)
        return result['answer']


def test_agent():
    print("=" * 70)
    print("TESTING AGENT 1: TELECOM ADVISOR CHATBOT")
    print("=" * 70)

    agent = TelecomAdvisorAgent()
    agent.initialize_vector_db()

    test_queries = [
        "Why is my MOS low on a cell?",
        "How to fix high call drop rate?",
        "What causes handover failures?",
        "My PRB is over 85%, what should I do?",
        "How to improve throughput?"
    ]

    for query in test_queries:
        print(f"\n{'=' * 70}")
        print(f"Q: {query}")
        print(f"{'=' * 70}")
        result = agent.query(query)
        print(f"\nA: {result['answer']}")
        print(f"\n[Intent: {result['intent']} | Confidence: {result['confidence']} | Context: {len(result['context'])} chunks]")


if __name__ == "__main__":
    test_agent()
