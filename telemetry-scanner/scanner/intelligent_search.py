"""
Intelligent Multi-Modal Search System with domain-specific knowledge and advanced ranking.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import subprocess
import re

class SearchStrategy(Enum):
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    PATTERN = "pattern"
    KEYWORD = "keyword"
    GRAPH_BASED = "graph_based"

class RelevanceScore(Enum):
    EXACT_MATCH = 100
    HIGH = 85
    MEDIUM = 70
    LOW = 50
    MINIMAL = 25

@dataclass
class SearchResult:
    file_path: Path
    strategy: SearchStrategy
    relevance_score: int
    reasoning: str
    matching_patterns: List[str]
    context_snippets: List[str]
    confidence: float

@dataclass
class DomainKnowledge:
    """Domain-specific knowledge for C# and OpenTelemetry."""
    telemetry_patterns: Dict[str, List[str]]
    csharp_patterns: Dict[str, List[str]]
    architectural_patterns: Dict[str, List[str]]
    semantic_relationships: Dict[str, List[str]]

class IntelligentSearchEngine:
    """Advanced search engine with domain knowledge and multi-modal search."""
    
    def __init__(self, repo_path: str, code_graph_path: str):
        self.repo_path = Path(repo_path)
        self.code_graph_path = code_graph_path
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.domain_knowledge = self._load_domain_knowledge()
        self.file_index = self._build_file_index()
        self.code_graph = self._load_code_graph()
        
    def _load_domain_knowledge(self) -> DomainKnowledge:
        """Load domain-specific knowledge patterns."""
        return DomainKnowledge(
            telemetry_patterns={
                "instrumentation": [
                    "AddOpenTelemetry", "AddHttpClientInstrumentation", "AddSqlClientInstrumentation",
                    "AddRabbitMQInstrumentation", "ActivitySource", "Meter", "ActivityListener",
                    "SetTag", "SetAttribute", "StartActivity", "CreateActivity"
                ],
                "configuration": [
                    "TracerProviderBuilder", "MeterProviderBuilder", "OpenTelemetryBuilder",
                    "WithTracing", "WithMetrics", "WithLogging", "AddConsoleExporter",
                    "AddJaegerExporter", "AddOtlpExporter"
                ],
                "attributes": [
                    "http.method", "http.url", "db.statement", "messaging.system",
                    "service.name", "service.version", "deployment.environment"
                ],
                "spans": [
                    "Activity", "IActivity", "ActivityContext", "ActivityKind",
                    "ActivityStatusCode", "ActivityTagsCollection"
                ]
            },
            csharp_patterns={
                "dependency_injection": [
                    "IServiceCollection", "ServiceCollectionExtensions", "AddScoped",
                    "AddSingleton", "AddTransient", "ConfigureServices"
                ],
                "middleware": [
                    "IMiddleware", "MiddlewareExtensions", "UseMiddleware", "app.Use",
                    "RequestDelegate", "HttpContext"
                ],
                "configuration": [
                    "IConfiguration", "IOptions", "IConfigurationBuilder", "appsettings",
                    "ConfigurationManager", "IHostBuilder"
                ],
                "startup": [
                    "Startup", "Program", "Main", "CreateHostBuilder", "ConfigureServices",
                    "Configure", "WebApplication"
                ]
            },
            architectural_patterns={
                "factory": ["Factory", "Create", "Builder", "IFactory"],
                "repository": ["Repository", "IRepository", "DataAccess", "Store"],
                "service": ["Service", "IService", "Handler", "Manager"],
                "controller": ["Controller", "ApiController", "ControllerBase"]
            },
            semantic_relationships={
                "telemetry": ["observability", "monitoring", "tracing", "metrics", "logging"],
                "instrumentation": ["measurement", "tracking", "recording", "collection"],
                "configuration": ["setup", "initialization", "bootstrap", "registration"],
                "middleware": ["pipeline", "filter", "interceptor", "handler"]
            }
        )
    
    def _build_file_index(self) -> Dict[str, Dict]:
        """Build an index of all C# files with metadata."""
        index = {}
        
        for cs_file in self.repo_path.rglob("*.cs"):
            if cs_file.stat().st_size == 0:
                continue
                
            try:
                content = cs_file.read_text(encoding="utf-8", errors="ignore")
                
                index[str(cs_file)] = {
                    "path": cs_file,
                    "content": content,
                    "size": cs_file.stat().st_size,
                    "keywords": self._extract_keywords(content),
                    "patterns": self._identify_patterns(content),
                    "imports": self._extract_imports(content),
                    "classes": self._extract_classes(content),
                    "methods": self._extract_methods(content)
                }
            except Exception as e:
                print(f"Warning: Could not index file {cs_file}: {e}")
        
        return index
    
    def _load_code_graph(self) -> Optional[Dict]:
        """Load code graph if available."""
        try:
            with open(self.code_graph_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract meaningful keywords from code content."""
        # Extract class names, method names, and important identifiers
        keywords = []
        
        # Extract class declarations
        class_matches = re.findall(r'class\s+(\w+)', content)
        keywords.extend(class_matches)
        
        # Extract interface declarations
        interface_matches = re.findall(r'interface\s+(\w+)', content)
        keywords.extend(interface_matches)
        
        # Extract method declarations
        method_matches = re.findall(r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?(?:\w+\s+)?(\w+)\s*\(', content)
        keywords.extend(method_matches)
        
        # Extract using statements
        using_matches = re.findall(r'using\s+([^;]+);', content)
        keywords.extend([u.strip() for u in using_matches])
        
        return list(set(keywords))
    
    def _identify_patterns(self, content: str) -> List[str]:
        """Identify domain-specific patterns in code."""
        patterns = []
        
        # Check telemetry patterns
        for category, pattern_list in self.domain_knowledge.telemetry_patterns.items():
            for pattern in pattern_list:
                if pattern in content:
                    patterns.append(f"telemetry.{category}.{pattern}")
        
        # Check C# patterns
        for category, pattern_list in self.domain_knowledge.csharp_patterns.items():
            for pattern in pattern_list:
                if pattern in content:
                    patterns.append(f"csharp.{category}.{pattern}")
        
        # Check architectural patterns
        for category, pattern_list in self.domain_knowledge.architectural_patterns.items():
            for pattern in pattern_list:
                if pattern in content:
                    patterns.append(f"architecture.{category}.{pattern}")
        
        return patterns
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract using/import statements."""
        imports = []
        using_matches = re.findall(r'using\s+([^;]+);', content)
        for match in using_matches:
            imports.append(match.strip())
        return imports
    
    def _extract_classes(self, content: str) -> List[str]:
        """Extract class and interface names."""
        classes = []
        
        # Extract class declarations
        class_matches = re.findall(r'(?:public|internal|private)?\s*(?:static|abstract|sealed)?\s*class\s+(\w+)', content)
        classes.extend(class_matches)
        
        # Extract interface declarations
        interface_matches = re.findall(r'(?:public|internal|private)?\s*interface\s+(\w+)', content)
        classes.extend(interface_matches)
        
        return classes
    
    def _extract_methods(self, content: str) -> List[str]:
        """Extract method names."""
        methods = []
        method_matches = re.findall(
            r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?(?:virtual\s+)?(?:override\s+)?(?:\w+\s+)?(\w+)\s*\(',
            content
        )
        methods.extend(method_matches)
        return methods
    
    def multi_modal_search(self, intent: Dict, top_k: int = 30) -> List[SearchResult]:
        """Perform multi-modal search using all available strategies."""
        
        all_results = []
        
        # Strategy 1: Semantic Search
        semantic_results = self._semantic_search(intent, top_k // 2)
        all_results.extend(semantic_results)
        
        # Strategy 2: Structural Search (based on static analysis query)
        if intent.get("static_analysis_query"):
            structural_results = self._structural_search(intent, top_k // 4)
            all_results.extend(structural_results)
        
        # Strategy 3: Pattern-Based Search
        pattern_results = self._pattern_search(intent, top_k // 4)
        all_results.extend(pattern_results)
        
        # Strategy 4: Keyword Search
        keyword_results = self._keyword_search(intent, top_k // 4)
        all_results.extend(keyword_results)
        
        # Strategy 5: Graph-Based Search (if code graph available)
        if self.code_graph:
            graph_results = self._graph_based_search(intent, top_k // 4)
            all_results.extend(graph_results)
        
        # Consolidate and rank results
        consolidated_results = self._consolidate_results(all_results)
        
        # Apply domain-specific ranking
        ranked_results = self._apply_domain_ranking(consolidated_results, intent)
        
        return ranked_results[:top_k]
    
    def _semantic_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Perform semantic search with domain knowledge enhancement."""
        query = intent.get("semantic_description", "")
        if not query:
            return []
        
        # Enhance query with domain-specific terms
        enhanced_query = self._enhance_query_with_domain_knowledge(query, intent)
        
        # Get file contents for embedding
        file_paths = list(self.file_index.keys())
        file_contents = [self.file_index[path]["content"] for path in file_paths]
        
        if not file_contents:
            return []
        
        # Generate embeddings
        query_embedding = self.semantic_model.encode([enhanced_query])
        file_embeddings = self.semantic_model.encode(file_contents)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, file_embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            file_path = Path(file_paths[idx])
            similarity_score = similarities[idx]
            
            # Convert similarity to relevance score
            relevance_score = int(similarity_score * 100)
            
            # Extract context snippets
            context_snippets = self._extract_context_snippets(
                self.file_index[file_paths[idx]]["content"], enhanced_query
            )
            
            result = SearchResult(
                file_path=file_path,
                strategy=SearchStrategy.SEMANTIC,
                relevance_score=relevance_score,
                reasoning=f"Semantic similarity: {similarity_score:.3f}",
                matching_patterns=[],
                context_snippets=context_snippets,
                confidence=similarity_score
            )
            results.append(result)
        
        return results
    
    def _enhance_query_with_domain_knowledge(self, query: str, intent: Dict) -> str:
        """Enhance search query with domain-specific knowledge."""
        enhanced_terms = [query]
        
        # Add semantic relationships
        for key, related_terms in self.domain_knowledge.semantic_relationships.items():
            if key.lower() in query.lower():
                enhanced_terms.extend(related_terms)
        
        # Add operation-specific terms
        telemetry_op = intent.get("telemetry_operation", {})
        op_type = telemetry_op.get("type", "")
        op_action = telemetry_op.get("action", "")
        
        if op_type in self.domain_knowledge.telemetry_patterns:
            enhanced_terms.extend(self.domain_knowledge.telemetry_patterns[op_type])
        
        if op_action == "CREATE":
            enhanced_terms.extend(["new", "initialize", "setup"])
        elif op_action == "ADD_ATTRIBUTES":
            enhanced_terms.extend(["SetTag", "SetAttribute", "enrich"])
        
        return " ".join(enhanced_terms)
    
    def _structural_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search based on code structure patterns."""
        static_query = intent.get("static_analysis_query", {})
        if not static_query:
            return []
        
        results = []
        search_method = static_query.get("find_method_call")
        
        if search_method:
            for file_path, file_data in self.file_index.items():
                content = file_data["content"]
                
                # Search for method calls
                if search_method in content:
                    # Count occurrences for relevance scoring
                    occurrences = content.count(search_method)
                    relevance_score = min(RelevanceScore.EXACT_MATCH.value, 80 + occurrences * 5)
                    
                    # Extract context around matches
                    context_snippets = self._extract_method_context(content, search_method)
                    
                    result = SearchResult(
                        file_path=Path(file_path),
                        strategy=SearchStrategy.STRUCTURAL,
                        relevance_score=relevance_score,
                        reasoning=f"Contains method call: {search_method} ({occurrences} times)",
                        matching_patterns=[search_method],
                        context_snippets=context_snippets,
                        confidence=0.9 if occurrences > 1 else 0.7
                    )
                    results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _pattern_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search based on domain-specific patterns."""
        results = []
        
        # Search for telemetry patterns based on intent
        telemetry_op = intent.get("telemetry_operation", {})
        search_patterns = []
        
        # Add patterns based on operation type
        op_type = telemetry_op.get("type", "")
        if op_type in self.domain_knowledge.telemetry_patterns:
            search_patterns.extend(self.domain_knowledge.telemetry_patterns[op_type])
        
        # Add patterns based on attributes
        attributes = telemetry_op.get("attributes_to_add", [])
        for attr in attributes:
            attr_name = attr.get("name", "")
            if "." in attr_name:
                pattern_prefix = attr_name.split(".")[0]
                search_patterns.append(pattern_prefix)
        
        # Search for patterns in files
        for file_path, file_data in self.file_index.items():
            patterns_found = file_data.get("patterns", [])
            matching_patterns = []
            
            for pattern in search_patterns:
                if any(pattern.lower() in p.lower() for p in patterns_found):
                    matching_patterns.append(pattern)
            
            if matching_patterns:
                relevance_score = min(RelevanceScore.HIGH.value, 60 + len(matching_patterns) * 10)
                
                result = SearchResult(
                    file_path=Path(file_path),
                    strategy=SearchStrategy.PATTERN,
                    relevance_score=relevance_score,
                    reasoning=f"Matches patterns: {', '.join(matching_patterns)}",
                    matching_patterns=matching_patterns,
                    context_snippets=[],
                    confidence=0.8
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _keyword_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search based on keywords."""
        keywords = intent.get("search_keywords", [])
        if not keywords:
            return []
        
        results = []
        
        for file_path, file_data in self.file_index.items():
            content = file_data["content"]
            file_keywords = file_data.get("keywords", [])
            
            matches = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in content.lower() or keyword in file_keywords:
                    matches += 1
                    matched_keywords.append(keyword)
            
            if matches > 0:
                relevance_score = min(RelevanceScore.MEDIUM.value, 40 + matches * 15)
                
                result = SearchResult(
                    file_path=Path(file_path),
                    strategy=SearchStrategy.KEYWORD,
                    relevance_score=relevance_score,
                    reasoning=f"Matches {matches} keywords: {', '.join(matched_keywords)}",
                    matching_patterns=matched_keywords,
                    context_snippets=[],
                    confidence=0.6
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _graph_based_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search using code graph relationships."""
        if not self.code_graph:
            return []
        
        # This would integrate with the advanced code graph analyzer
        # For now, return empty list as placeholder
        return []
    
    def _consolidate_results(self, all_results: List[SearchResult]) -> List[SearchResult]:
        """Consolidate results from different strategies, handling duplicates."""
        file_to_results = {}
        
        for result in all_results:
            file_path = str(result.file_path)
            
            if file_path not in file_to_results:
                file_to_results[file_path] = result
            else:
                # Merge results for the same file
                existing = file_to_results[file_path]
                
                # Take the higher relevance score
                if result.relevance_score > existing.relevance_score:
                    file_to_results[file_path] = result
                
                # Merge matching patterns
                existing.matching_patterns.extend(result.matching_patterns)
                existing.matching_patterns = list(set(existing.matching_patterns))
                
                # Combine reasoning
                existing.reasoning += f"; {result.reasoning}"
                
                # Take higher confidence
                existing.confidence = max(existing.confidence, result.confidence)
        
        return list(file_to_results.values())
    
    def _apply_domain_ranking(self, results: List[SearchResult], intent: Dict) -> List[SearchResult]:
        """Apply domain-specific ranking adjustments."""
        
        for result in results:
            file_path = str(result.file_path)
            file_data = self.file_index.get(file_path, {})
            
            # Boost configuration files for configuration intents
            if intent.get("issue_category") == "CONFIGURATION":
                if any(pattern in file_path.lower() for pattern in 
                       ["startup", "program", "extensions", "configuration"]):
                    result.relevance_score += 15
            
            # Boost files with telemetry imports
            imports = file_data.get("imports", [])
            if any("opentelemetry" in imp.lower() for imp in imports):
                result.relevance_score += 10
            
            # Boost files that already have instrumentation
            patterns = file_data.get("patterns", [])
            if any("telemetry" in pattern for pattern in patterns):
                result.relevance_score += 10
            
            # Penalize test files unless specifically looking for test patterns
            if "test" in file_path.lower() and "test" not in intent.get("semantic_description", "").lower():
                result.relevance_score -= 20
            
            # Ensure relevance score stays within bounds
            result.relevance_score = max(0, min(100, result.relevance_score))
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)
    
    def _extract_context_snippets(self, content: str, query: str) -> List[str]:
        """Extract relevant context snippets from file content."""
        lines = content.split('\n')
        snippets = []
        query_terms = query.lower().split()
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(term in line_lower for term in query_terms):
                # Extract context around the matching line
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                snippets.append(context.strip())
        
        return snippets[:3]  # Return top 3 snippets
    
    def _extract_method_context(self, content: str, method_name: str) -> List[str]:
        """Extract context around method calls."""
        lines = content.split('\n')
        contexts = []
        
        for i, line in enumerate(lines):
            if method_name in line:
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = '\n'.join(lines[start:end])
                contexts.append(context.strip())
        
        return contexts
